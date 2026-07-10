import streamlit as st
import calendar
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Orçamento Familiar", page_icon="💰", layout="centered")

# --- CONTROLE DE LOGIN (SESSION STATE) ---
if "logado" not in st.session_state:
    st.session_state.logado = False
if "usuario_atual" not in st.session_state:
    st.session_state.usuario_atual = None
if "spreadsheet_url" not in st.session_state:
    st.session_state.spreadsheet_url = None

# --- TELA DE LOGIN ---
if not st.session_state.logado:
    st.title("🔐 Acesso ao Controle Financeiro")
    st.write("Insira as suas credenciais para gerenciar o seu orçamento individual.")
    
    usuario_input = st.text_input("Usuário:").strip().lower()
    senha_input = st.text_input("Senha:", type="password")
    
    if st.button("Entrar"):
        try:
            lista_usuarios = st.secrets["usuarios"]
            if usuario_input in lista_usuarios and str(lista_usuarios[usuario_input]["senha"]) == senha_input:
                st.session_state.logado = True
                st.session_state.usuario_atual = usuario_input
                st.session_state.spreadsheet_url = lista_usuarios[usuario_input]["spreadsheet"]
                st.success(f"Bem-vindo(a), {usuario_input.capitalize()}!")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
        except Exception:
            st.error("Erro ao carregar a base de dados de usuários nos Secrets.")
    st.stop()

# --- SESSÃO LOGADA COM SUCESSO ---
st.sidebar.write(f"👤 Usuário: **{st.session_state.usuario_atual.capitalize()}**")
if st.sidebar.button("🚪 Sair / Trocar Conta"):
    st.session_state.logado = False
    st.session_state.usuario_atual = None
    st.session_state.spreadsheet_url = None
    st.rerun()

st.title(f"💰 Planejamento de {st.session_state.usuario_atual.capitalize()}")

# CONEXÃO LIMPA (O Streamlit busca automaticamente o bloco [connections.gsheets])
conn = st.connection("meugoogle", type=GSheetsConnection)
# --- CARREGAR HISTÓRICO ---
try:
    # Passamos explicitamente a URL correta do usuário ativo no parâmetro 'spreadsheet'
    dados_existentes = conn.read(spreadsheet=st.session_state.spreadsheet_url, ttl=0) 
    dados_existentes = dados_existentes.dropna(how="all")
    if not dados_existentes.empty:
        dados_existentes['Mes'] = dados_existentes['Mes'].astype(str)
    gastos_salvos = dados_existentes.to_dict(orient="records")
except Exception:
    dados_existentes = pd.DataFrame(columns=["Mes", "Renda", "Contas_Fixas", "Alimentação", "Transporte", "Lazer_Compras", "Guardar"])
    gastos_salvos = []

# Lista dos meses foco (Julho a Dezembro)
meses_foco = [calendar.month_name[m] for m in range(7, 13)]

st.write("---")
mes_selecionado = st.selectbox("Selecione o mês que deseja preencher ou editar:", meses_foco)

# Verificar dados existentes do mês selecionado
dados_mes_antigo = dados_existentes[dados_existentes['Mes'] == mes_selecionado]

if not dados_mes_antigo.empty:
    st.info(f"O mês de {mes_selecionado} já possui dados salvos. Alterar os valores abaixo irá atualizar o seu histórico!")
    valores_padrao = dados_mes_antigo.iloc[0].to_dict()
else:
    valores_padrao = {"Renda": 2000.0, "Contas_Fixas": 0.0, "Alimentação": 0.0, "Transporte": 0.0, "Lazer_Compras": 0.0, "Guardar": 0.0}

# --- INTERFACE DE ENTRADA ---
st.subheader(f"📅 Dados para: {mes_selecionado}")
renda = st.number_input(f"Qual a sua Renda em {mes_selecionado} (R$):", min_value=0.0, value=float(valores_padrao["Renda"]), step=100.0)

st.write("### 💸 Distribuição dos Gastos")
col1, col2 = st.columns(2)
with col1:
    contas_fixas = st.number_input("Contas Fixas (R$):", min_value=0.0, value=float(valores_padrao["Contas_Fixas"]), step=50.0)
    alimentacao = st.number_input("Alimentação / Comida (R$):", min_value=0.0, value=float(valores_padrao["Alimentação"]), step=50.0)
with col2:
    transporte = st.number_input("Transporte (R$):", min_value=0.0, value=float(valores_padrao["Transporte"]), step=20.0)
    lazer_compras = st.number_input("Lazer & Roupas (R$):", min_value=0.0, value=float(valores_padrao["Lazer_Compras"]), step=50.0)
    
st.write("### 🏦 Destinação de Futuro")
guardar = st.number_input("Valor para Guardar / Investir (R$):", min_value=0.0, value=float(valores_padrao["Guardar"]), step=50.0)

# --- CÁLCULOS EM TEMPO REAL ---
total_distribuido = contas_fixas + alimentacao + transporte + lazer_compras + guardar
saldo_restante = renda - total_distribuido

st.write("---")
if saldo_restante >= 0:
    st.metric(label="Saldo Livre Restante", value=f"R$ {saldo_restante:.2f}")
else:
    st.metric(label="⚠️ Saldo Estourado", value=f"R$ {saldo_restante:.2f}", delta=f"{saldo_restante:.2f}")

if st.button("🚀 Salvar / Atualizar no Google Sheets"):
    nova_linha = pd.DataFrame([{
        "Mes": mes_selecionado,
        "Renda": renda,
        "Contas_Fixas": contas_fixas,
        "Alimentação": alimentacao,
        "Transporte": transporte,
        "Lazer_Compras": lazer_compras,
        "Guardar": guardar
    }])
    
    if not dados_mes_antigo.empty:
        df_atualizado = dados_existentes[dados_existentes['Mes'] != mes_selecionado]
        df_atualizado = pd.concat([df_atualizado, nova_linha], ignore_index=True)
    else:
        df_atualizado = pd.concat([dados_existentes, nova_linha], ignore_index=True)
        
    df_atualizado = df_atualizado.dropna(how="all")
    
    # Atualiza na planilha correta passando o link dinâmico
    conn.update(spreadsheet=st.session_state.spreadsheet_url, data=df_atualizado)
    st.success(f"Dados salvos com sucesso na sua planilha!")
    st.rerun()

# --- EXIBIR HISTÓRICO INDIVIDUAL ---
if gastos_salvos:
    st.write("---")
    st.write("### 📋 Seu Histórico de Orçamentos Salvos")
    st.dataframe(dados_existentes, use_container_width=True)
