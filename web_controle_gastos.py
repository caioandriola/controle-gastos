import streamlit as st
import calendar
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Configuração visual da página web
st.set_page_config(page_title="Orçamento Familiar", page_icon="💰", layout="centered")
st.title("💰 Planejamento &amp; Controle Financeiro")

# Conexão segura com os Secrets configurados
conn = st.connection("gsheets", type=GSheetsConnection)

# --- CARREGAR HISTÓRICO ---
try:
    dados_existentes = conn.read(ttl=0) 
    dados_existentes = dados_existentes.dropna(how="all")
    gastos_salvos = dados_existentes.to_dict(orient="records")
except Exception:
    gastos_salvos = []

# Lógica dos meses (Focado de Julho até Dezembro)
meses = [calendar.month_name[m] for m in range(1, 13)]
quantidade_preenchida = len(gastos_salvos)
indice_atual = 6 + quantidade_preenchida 

# --- INTERFACE ---
if indice_atual < 12:
    mes_atual = meses[indice_atual]
    st.subheader(f"📅 Planejamento para: {mes_atual}")
    
    # Entrada da Renda Principal
    renda = st.number_input(f"Qual a sua Renda em {mes_atual} (R$):", min_value=0.0, value=2000.0, step=100.0)
    
    st.write("### 💸 Distribuição dos Gastos")
    
    # Criando duas colunas visuais organizadas para os inputs
    col1, col2 = st.columns(2)
    with col1:
        contas_fixas = st.number_input("Contas Fixas (R$):", min_value=0.0, step=50.0)
        alimentacao = st.number_input("Alimentação / Comida (R$):", min_value=0.0, step=50.0)
    with col2:
        transporte = st.number_input("Transporte (R$):", min_value=0.0, step=20.0)
        lazer_compras = st.number_input("Lazer &amp; Roupas (R$):", min_value=0.0, step=50.0)
        
    st.write("### 🏦 Destinação de Futuro")
    guardar = st.number_input("Valor para Guardar / Investir (R$):", min_value=0.0, step=50.0)

    # --- CÁLCULOS EM TEMPO REAL (Devem ficar dentro do bloco 'if') ---
    total_distribuido = contas_fixas + alimentacao + transporte + lazer_compras + guardar
    saldo_restante = renda - total_distribuido

    st.write("---")
    if saldo_restante >= 0:
        st.metric(label="Saldo Livre Restante", value=f"R$ {saldo_restante:.2f}")
    else:
        st.metric(label="⚠️ Saldo Estourado", value=f"R$ {saldo_restante:.2f}", delta=f"{saldo_restante:.2f}")

    if st.button("🚀 Confirmar e Enviar para o Google Sheets"):
        # Estrutura a nova linha com as categorias novas
        nova_linha = pd.DataFrame([{
            "Mes": mes_atual,
            "Renda": renda,
            "Contas_Fixas": contas_fixas,
            "Alimentação": alimentacao,
            "Transporte": transporte,
            "Lazer_Compras": lazer_compras,
            "Guardar": guardar
        }])
        
        if gastos_salvos:
            df_atualizado = pd.concat([dados_existentes, nova_linha], ignore_index=True)
        else:
            df_atualizado = nova_linha
            
        conn.update(data=df_atualizado)
        st.success(f"Orçamento de {mes_atual} integrado à nuvem!")
        st.rerun()
else:
    st.info("Todos os meses de Julho a Dezembro já foram preenchidos na planilha!")

# --- EXIBIR HISTÓRICO ---
if gastos_salvos:
    st.write("---")
    st.write("### 📋 Histórico de Orçamentos Salvos")
    st.dataframe(gastos_salvos, use_container_width=True)
