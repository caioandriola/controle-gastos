import streamlit as st
import calendar
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Configuração visual da página web
st.set_page_config(page_title="Controle de Gastos", page_icon="📊", layout="centered")
st.title("📊 Controle de Gastos Familiares")

# Cria a conexão com o Google Sheets pegando a URL e as credenciais direto dos Secrets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- CARREGAR DADOS EXISTENTES EM TEMPO REAL ---
try:
    # ttl=0 força o Streamlit a buscar dados atualizados diretamente do Google sempre
    dados_existentes = conn.read(ttl=0) 
    dados_existentes = dados_existentes.dropna(how="all")
    gastos_salvos = dados_existentes.to_dict(orient="records")
except Exception:
    gastos_salvos = []

# Lógica dos meses (Focado de Julho até Dezembro)
meses = [calendar.month_name[m] for m in range(1, 13)]
quantidade_preenchida = len(gastos_salvos)
indice_atual = 6 + quantidade_preenchida  # Começa em Julho (índice 6) + quantidade já salva

# --- INTERFACE PRINCIPAL DE CADASTRO ---
if indice_atual < 12:
    mes_atual = meses[indice_atual]
    st.subheader(f"Preenchendo dados para: {mes_atual}")
    
    custo = st.number_input(f"Qual foi seu gasto em {mes_atual} (R$):", min_value=0.0, step=50.0)
    lucros = st.number_input(f"Qual a meta de lucro para {mes_atual} (R$):", min_value=0.0, step=50.0)
    
    if st.button("🚀 Enviar para o Google Sheets"):
        # Cria a nova linha estruturada
        nova_linha = pd.DataFrame([{"Mes": mes_atual, "Gasto": custo, "Lucro": lucros}])
        
        # Junta o histórico existente com o novo mês lançado
        if gastos_salvos:
            df_atualizado = pd.concat([dados_existentes, nova_linha], ignore_index=True)
        else:
            df_atualizado = nova_linha
            
        # Grava os dados atualizados de volta na planilha através das credenciais seguras
        conn.update(data=df_atualizado)
        
        st.success(f"Dados de {mes_atual} salvos na planilha com sucesso!")
        st.rerun()  # Atualiza a tela para avançar o mês visualmente
else:
    st.info("Todos os meses de Julho a Dezembro já foram preenchidos na planilha!")

# --- EXIBIR HISTÓRICO (TABELA) ---
if gastos_salvos:
    st.write("---")
    st.write("### 📋 Dados Salvos na Nuvem")
    st.dataframe(gastos_salvos, use_container_width=True)
