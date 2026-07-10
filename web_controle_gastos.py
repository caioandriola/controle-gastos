import streamlit as st
import calendar
import gspread
from google.oauth2.service_account import Credentials
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

# --- CONEXÃO DIRETA E ESTÁVEL COM GSPREAD ---
@st.cache_resource
def obter_cliente_google():
    escopos = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    # Carrega as chaves do dicionário raiz do st.secrets de forma explícita
    info_chaves = {
        "type": st.secrets["type"],
        "project_id": st.secrets["project_id"],
        "private_key_id": st.secrets["private_key_id"],
        "private_key": st.secrets["private_key"],
        "client_email": st.secrets["client_email"],
        "client_id": st.secrets["client_id"],
        "auth_uri": st.secrets["auth_uri"],
        "token_uri": st.secrets["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["client_x509_cert_url"]
    }
    credenciais = Credentials.from_service_account_info(info_chaves, scopes=escopos)
    return gspread.authorize(credenciais)

try:
    gc = obter_cliente_google()
    # Abre a planilha individual do usuário logado usando a URL
    planilha = gc.open_by_url(st.session_state.spreadsheet_url)
    aba = planilha.get_worksheet(0) # Abre a primeira aba
    
    # Converte os dados da folha em DataFrame do Pandas
    dados_brutos = aba.get_all_records()
    if dados_brutos:
        dados_existentes = pd.DataFrame(dados_brutos)
    else:
        dados_existentes = pd.DataFrame(columns=["Mes", "Renda", "Contas_Fixas", "Alimentação", "Transporte", "Lazer_Compras", "Guardar"])
    
    dados_existentes = dados_existentes.dropna(how="all")
    if not dados_existentes.empty:
        dados_existentes['Mes'] = dados_existentes['Mes'].astype(str)
    gastos_salvos = dados_existentes.to_dict(orient="records")
except Exception as e:
    st.error(f"Erro ao conectar com a sua planilha do Google: {e}")
    st.stop()

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
    nova_linha = {
        "Mes": mes_selecionado,
        "Renda": renda,
        "Contas_Fixas": contas_fixas,
        "Alimentação": alimentacao,
        "Transporte": transporte,
        "Lazer_Compras": lazer_compras,
        "Guardar": guardar
    }
    
    # Atualiza a estrutura do DataFrame
    if not dados_mes_antigo.empty:
        df_atualizado = dados_existentes[dados_existentes['Mes'] != mes_selecionado]
        df_atualizado = pd.concat([df_atualizado, pd.DataFrame([nova_linha])], ignore_index=True)
    else:
        df_atualizado = pd.concat([dados_existentes, pd.DataFrame([nova_linha])], ignore_index=True)
        
    df_atualizado = df_atualizado.dropna(how="all")
    
    # Sobrescreve a planilha de forma limpa usando a API estável do gspread
    aba.clear()
    # Adiciona novamente o cabeçalho e as linhas atualizadas
    aba.update([df_atualizado.columns.values.tolist()] + df_atualizado.values.tolist())
    st.success(f"Dados salvos com sucesso na sua planilha!")
    st.rerun()

# --- EXIBIR HISTÓRICO INDIVIDUAL ---
if gastos_salvos:
    st.write("---")
    st.write("### 📋 Seu Histórico de Orçamentos Salvos")
    st.dataframe(dados_existentes, width="stretch")
