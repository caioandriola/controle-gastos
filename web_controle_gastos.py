import streamlit as st
import calendar
import pandas as pd
import gspread

# Configuração da página
st.set_page_config(page_title="Controle de Gastos", page_icon="📊", layout="centered")
st.title("📊 Controle de Gastos Familiares")

# Pegando a URL da planilha que você salvou nos Secrets do Streamlit
try:
    URL_PLANILHA = st.secrets["connections"]["gsheets"]["spreadsheet"]
except Exception:
    st.error("Por favor, configure os Secrets do Streamlit com o link da sua planilha!")
    st.stop()

# Conectando à planilha usando gspread de forma pública/aberta
@st.cache_data(ttl=0)  # ttl=0 garante dados limpos a cada atualização
def carregar_dados():
    try:
        # Abre a planilha pelo link de forma anônima/pública
        gc = gspread.public()
        planilha = gc.open_by_url(URL_PLANILHA)
        aba = planilha.get_worksheet(0) # Pega a primeira aba (Página1)
        dados = aba.get_all_records()
        return pd.DataFrame(dados), aba
    except Exception:
        # Se a planilha estiver totalmente zerada ou sem registros ainda
        return pd.DataFrame(columns=["Mes", "Gasto", "Lucro"]), None

df_existente, aba_planilha = carregar_dados()
gastos_salvos = df_existente.to_dict(orient="records")

# Lógica dos meses (Julho a Dezembro)
meses = [calendar.month_name[m] for m in range(1, 13)]
quantidade_preenchida = len(gastos_salvos)
indice_atual = 6 + quantidade_preenchida

# --- INTERFACE PRINCIPAL ---
if indice_atual < 12:
    mes_atual = meses[indice_atual]
    st.subheader(f"Preenchendo dados para: {mes_atual}")
    
    custo = st.number_input(f"Qual foi seu gasto em {mes_atual} (R$):", min_value=0.0, step=50.0)
    lucros = st.number_input(f"Qual a meta de lucro para {mes_atual} (R$):", min_value=0.0, step=50.0)
    
    if st.button("🚀 Enviar para o Google Sheets"):
        # Se for o primeiro registro e a aba não foi capturada corretamente, usamos uma requisição com permissão
        try:
            # Para conseguir ESCREVER sem chaves de serviço, precisamos usar a API de conexão que você configurou nos Secrets
            # O gspread público serve para ler. Para escrever, usamos a própria URL do pandas que sobrescreve dados públicos de edição:
            nova_linha = pd.DataFrame([{"Mes": mes_atual, "Gasto": custo, "Lucro": lucros}])
            df_atualizado = pd.concat([df_existente, nova_linha], ignore_index=True)
            
            # Convertendo a URL de visualização para a URL de exportação/gravação do Google
            sheet_id = URL_PLANILHA.split("/d/")[1].split("/")[0]
            url_gravar = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"
            
            # Nota técnica: O Google Sheets aceita atualizações via API de formulários ou via conector do gspread com conta de serviço. 
            # Como a sua planilha está como "Qualquer pessoa com o link pode EDITAR", o gspread comum com autenticação anônima bloqueia a escrita por segurança.
            
            # Para garantir 100% que grave sem te dar dor de cabeça com chaves do Google Cloud:
            st.warning("Para gravar direto na planilha sem erros de segurança, precisamos usar uma conta de serviço ou o formulário vinculado.")
            
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")
            
else:
    st.info("Todos os meses de Julho a Dezembro já foram preenchidos!")

if gastos_salvos:
    st.write("---")
    st.write("### 📋 Dados Salvos na Nuvem")
    st.dataframe(gastos_salvos, use_container_width=True)
