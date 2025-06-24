
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

# Carrega variáveis do .env
load_dotenv()

# Validação das variáveis obrigatórias
required_vars = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASS", "DB_PORT"]
for var in required_vars:
    if not os.getenv(var):
        st.error(f"❌ Variável de ambiente {var} não encontrada. Verifique o arquivo .env.")
        st.stop()

st.set_page_config(page_title="Dashboard Efetividade", layout="wide")

@st.cache_data
def carregar_dados():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            port=os.getenv("DB_PORT")
        )
        query = "SELECT * FROM vw_efetividade"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Erro ao conectar no banco de dados: {e}")
        st.stop()

df = carregar_dados()

df["data_competencia"] = pd.to_datetime(df["data_competencia"], errors="coerce")

st.sidebar.header("Filtros")

datas = df["data_competencia"].dropna().dt.to_period("M").drop_duplicates().sort_values()
datas_formatadas = [data.to_timestamp() for data in datas]
data_selecionada = st.sidebar.selectbox(
    "Data de Competência (Mês/Ano)",
    datas_formatadas,
    format_func=lambda d: d.strftime('%B/%Y').capitalize()
)

parceiros = df["nome_parceiro"].dropna().unique()
parceiro = st.sidebar.selectbox("Parceiro", ["Todos"] + sorted(parceiros.tolist()))

status = df["status_titulo"].dropna().unique()
status_selecionado = st.sidebar.multiselect("Status do Título", sorted(status.tolist()), default=status.tolist())

bancos = df["banco"].dropna().unique()
banco = st.sidebar.selectbox("Banco", ["Todos"] + sorted(bancos.tolist()))

df_filtrado = df[df["data_competencia"].dt.to_period("M") == data_selecionada.to_period("M")]
if parceiro != "Todos":
    df_filtrado = df_filtrado[df_filtrado["nome_parceiro"] == parceiro]
if banco != "Todos":
    df_filtrado = df_filtrado[df_filtrado["banco"] == banco]
if status_selecionado:
    df_filtrado = df_filtrado[df_filtrado["status_titulo"].isin(status_selecionado)]

st.title("📊 Dashboard de Contratos")

total_valor = df_filtrado["valor"].sum()
total_titulos = df_filtrado.shape[0]

col1, col2 = st.columns(2)
with col1:
    st.metric("Valor Total", f"R$ {total_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
with col2:
    st.metric("Qtd. de Títulos", f"{total_titulos}")

# Gráfico de Pizza
with st.container():
    st.markdown("""
    <div style="background-color: #f9f9f9; padding: 25px; border-radius: 12px;
                box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.05); margin-bottom: 20px;">
    """, unsafe_allow_html=True)

    st.markdown("## 🥧 Distribuição por Status do Título")
    df_pizza = df_filtrado.groupby("status_titulo")["valor"].sum().reset_index()

    fig_pizza = px.pie(
        df_pizza,
        names="status_titulo",
        values="valor",
        hole=0.4,
        template="plotly_white"
    )
    fig_pizza.update_traces(textinfo='percent+label', hovertemplate='%{label}: R$ %{value:,.2f}<extra></extra>')
    st.plotly_chart(fig_pizza, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)


# Gráfico de Barras por Mês
with st.container():
    st.markdown("""
    <div style="background-color: #f9f9f9; padding: 25px; border-radius: 12px;
                box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.05); margin-top: 20px;">
    """, unsafe_allow_html=True)

    st.markdown("## 📈 Evolução Mensal por Status")

    df_mes = df.copy()
    df_mes["mes"] = df_mes["data_competencia"].dt.to_period("M").dt.to_timestamp()
    df_mes = df_mes.groupby(["mes", "status_titulo"])["valor"].sum().reset_index()

    fig_bar = px.bar(
        df_mes,
        x="mes",
        y="valor",
        color="status_titulo",
        title="",
        labels={"mes": "Mês", "valor": "Valor"},
        template="plotly_white"
    )
    fig_bar.update_layout(
        barmode='stack',
        xaxis_tickformat="%b/%Y",
        margin=dict(t=10, b=10),
        plot_bgcolor="#fff",
        paper_bgcolor="#f9f9f9"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

# Tabela detalhada

with st.container():
    st.markdown("""
    <div style="background-color: #f9f9f9; padding: 25px; border-radius: 12px;
                box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.05); margin-top: 20px;">
    """, unsafe_allow_html=True)

    st.markdown("## 📋 Tabela Detalhada por Parceiro e Status")

    if not df_filtrado.empty:
        tabela = df_filtrado.groupby(["nome_parceiro", "status_titulo"])["valor"].sum().reset_index()
        valor_total_geral = tabela["valor"].sum()
        tabela["% do Total"] = (tabela["valor"] / valor_total_geral * 100).round(2)
        tabela["valor"] = tabela["valor"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        tabela["% do Total"] = tabela["% do Total"].apply(lambda x: f"{x}%")
        st.dataframe(tabela, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum dado disponível para os filtros selecionados.")

    st.markdown("</div>", unsafe_allow_html=True)
