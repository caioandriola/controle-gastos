import streamlit as st
import calendar
import json
import os

# Configuração visual da página web
st.set_page_config(page_title="Controle de Gastos", page_icon="📊", layout="centered")
st.title("📊 Controle de Gastos Mensais")

# Gerar lista de meses (Janeiro a Dezembro)
meses = [calendar.month_name[m] for m in range(1, 13)]

# --- INICIALIZAÇÃO DO ESTADO DA SESSÃO ---
# Substitui a lógica de declaração inicial do terminal
if "gastos" not in st.session_state:
    st.session_state.gastos = []
if "i" not in st.session_state:
    st.session_state.i = 6  # Começa em Julho por padrão
if "historico_verificado" not in st.session_state:
    st.session_state.historico_verificado = False

# --- VERIFICADOR DE HISTÓRICO (POP-UP NA TELA) ---
if os.path.exists("historico_gastos.json") and not st.session_state.historico_verificado:
    st.warning("Encontramos um histórico antigo salvo!")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Continuar de onde parei (Manter dados)"):
            with open("historico_gastos.json", "r", encoding="utf-8") as arquivo:
                st.session_state.gastos = json.load(arquivo)
            st.session_state.i = 6 + len(st.session_state.gastos)
            st.session_state.historico_verificado = True
            st.rerun()
            
    with col2:
        if st.button("Começar do zero (Apagar antigos)"):
            st.session_state.gastos = []
            st.session_state.i = 6
            st.session_state.historico_verificado = True
            st.rerun()

# --- INTERFACE PRINCIPAL ---
# Só mostra os campos se o verificador de histórico já foi resolvido
if not os.path.exists("historico_gastos.json") or st.session_state.historico_verificado:
    
    i = st.session_state.i

    if i < 12:
        st.subheader(f"Preenchendo dados para: {meses[i]}")
        
        # Inputs nativos do Streamlit com caixas de digitação
        custo = st.number_input(f"Qual foi seu gasto em {meses[i]} (R$):", min_value=0.0, step=50.0)
        lucros = st.number_input(f"Qual a meta de lucro para {meses[i]} (R$):", min_value=0.0, step=50.0)
        
        # Botão para adicionar o mês atual
        if st.button("Registrar Mês"):
            dados_mes = {"Mes": meses[i], "Gasto": custo, "Lucro": lucros}
            st.session_state.gastos.append(dados_mes)
            st.session_state.i += 1  # Avança o índice
            st.success(f"{meses[i]} registrado!")
            st.rerun()
    else:
        st.info("Todos os meses até Dezembro já foram preenchidos.")

    # --- SITUAÇÃO ATUAL (TABELA) ---
    if st.session_state.gastos:
        st.write("---")
        st.write("### 📋 Situação Atual")
        # Gera uma tabela interativa rica e limpa na tela na hora
        st.dataframe(st.session_state.gastos, use_container_width=True)
        
        # Botão de salvar (Substitui a saída do terminal)
        if st.button("💾 Finalizar e Salvar Arquivo"):
            with open("historico_gastos.json", "w", encoding="utf-8") as arquivo:
                json.dump(st.session_state.gastos, arquivo, indent=4, ensure_ascii=False)
            st.success("Dados salvos com sucesso em 'historico_gastos.json'!")