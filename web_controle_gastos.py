import streamlit as st
import calendar
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Controle de Gastos", page_icon="📊")
st.title("📊 Controle de Gastos com Google Sheets")

URL_PLANILHA = "https://docs.google.com/spreadsheets/d/https://docs.google.com/spreadsheets/d/1Frac6UuZ7uIrOWW5IWFwhWbjAu1VMGMCu9TKilskN1Y/edit?usp=sharing/edit?usp=sharing"

# Cria a conexão com o Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- CARREGAR DADOS EXISTENTES ---
# Lemos a planilha atualizada direto do Google
try:
    dados_existentes = conn.read(spreadsheet=URL_PLANILHA, ttl=0) # ttl=0 garante dados em tempo real
    # Se a planilha não estiver vazia, transformamos em lista de dicionários
    gastos_salvos = dados_existentes.to_dict(orient="records")
except Exception:
    gastos_salvos = []

# Determinar em qual mês parar/continuar
meses = [calendar.month_name[m] for m in range(1, 13)]
quantidade_preenchida = len(gastos_salvos)
indice_atual = 6 + quantidade_preenchida  # Começa em Julho (6) + o que já foi preenchido

# --- INTERFACE ---
if indice_atual < 12:
    mes_atual = meses[indice_atual]
    st.subheader(f"Preenchendo dados para: {mes_atual}")
    
    custo = st.number_input(f"Qual foi seu gasto em {mes_atual} (R$):", min_value=0.0, step=50.0)
    lucros = st.number_input(f"Qual a meta de lucro para {mes_atual} (R$):", min_value=0.0, step=50.0)
    
    if st.button("🚀 Enviar para o Google Sheets"):
        # 1. Cria a nova linha
        nova_linha = pd.DataFrame([{"Mes": mes_atual, "Gasto": custo, "Lucro": lucros}])
        
        # 2. Junta os dados antigos com a nova linha
        if gastos_salvos:
            df_atualizado = pd.concat([dados_existentes, nova_linha], ignore_index=True)
        else:
            df_atualizado = nova_linha
            
        # 3. Envia de volta para a nuvem do Google
        conn.update(spreadsheet=URL_PLANILHA, data=df_atualizado)
        
        st.success(f"Dados de {mes_atual} salvos na planilha!")
        st.rerun()
else:
    st.info("Todos os meses de Julho a Dezembro já foram preenchidos!")

# --- EXIBIR HISTÓRICO ---
if gastos_salvos:
    st.write("---")
    st.write("### 📋 Dados Salvos na Nuvem")
    st.dataframe(gastos_salvos, use_container_width=True)
