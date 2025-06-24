import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import psycopg2
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

# Validação das variáveis obrigatórias
required_vars = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASS", "DB_PORT"]
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    st.error(f"❌ Variáveis de ambiente ausentes: {', '.join(missing_vars)}")
    st.stop()

st.set_page_config(page_title="Dashboard Efetividade", layout="wide")

# Placeholders para UI responsiva
placeholder_filtros = st.sidebar.empty()
placeholder_metrics = st.empty()
placeholder_pizza = st.empty()
placeholder_grafico = st.empty()
placeholder_tabela = st.empty()

# Funções de carregamento com cache eficiente
@st.cache_data(ttl=300, show_spinner=False)
def carregar_dados():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            port=os.getenv("DB_PORT")
        )
        # Traz apenas colunas necessárias
        query = """
        SELECT data_competencia, nome_parceiro, status_titulo, banco, valor 
        FROM vw_efetividade
        """
        df = pd.read_sql(query, conn)
        conn.close()
        
        # Conversão otimizada de datas
        if not df.empty:
            df["data_competencia"] = pd.to_datetime(df["data_competencia"], errors="coerce", format='%Y-%m-%d')
            # Adiciona coluna de período mensal para filtros rápidos
            df["periodo_mensal"] = df["data_competencia"].dt.to_period('M')
        return df
    except Exception as e:
        st.error(f"Erro ao conectar no banco de dados: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def carregar_dados_mensais():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            port=os.getenv("DB_PORT")
        )
        query = """
        SELECT 
            DATE_TRUNC('month', data_competencia) AS mes,
            status_titulo,
            SUM(valor) AS valor
        FROM vw_efetividade
        GROUP BY mes, status_titulo
        ORDER BY mes;
        """
        df_mes = pd.read_sql(query, conn)
        conn.close()
        return df_mes
    except:
        return pd.DataFrame()

# Carregar dados
df = carregar_dados()
df_mes = carregar_dados_mensais()

# Placeholder para filtros
with placeholder_filtros.container():
    st.sidebar.header("Filtros")
    
    # Tratamento para quando não há dados
    if df.empty:
        st.sidebar.warning("Nenhum dado disponível")
        data_selecionada = None
    else:
        # Extração otimizada de datas
        datas_disponiveis = df["periodo_mensal"].dropna().unique()
        if len(datas_disponiveis) > 0:
            datas_ordenadas = np.sort(datas_disponiveis)
            datas_formatadas = [pd.Timestamp(str(date)) for date in datas_ordenadas]
            
            # Seleciona o último mês por padrão
            default_idx = len(datas_formatadas) - 1
            data_selecionada = st.sidebar.selectbox(
                "Data de Competência (Mês/Ano)",
                datas_formatadas,
                format_func=lambda d: d.strftime('%B/%Y').capitalize(),
                index=default_idx
            )
        else:
            data_selecionada = None
            st.sidebar.warning("Nenhuma data disponível")
    
    # Carregamento lazy das opções
    parceiros = ["Todos"] + sorted(df["nome_parceiro"].dropna().unique().tolist()) if not df.empty else ["Todos"]
    status_options = sorted(df["status_titulo"].dropna().unique().tolist()) if not df.empty else []
    bancos = ["Todos"] + sorted(df["banco"].dropna().unique().tolist()) if not df.empty else ["Todos"]
    
    parceiro = st.sidebar.selectbox("Parceiro", parceiros)
    status_selecionado = st.sidebar.multiselect("Status do Título", status_options, default=status_options)
    banco = st.sidebar.selectbox("Banco", bancos)

# Aplicação eficiente de filtros
if data_selecionada is not None and not df.empty:
    periodo_selecionado = data_selecionada.to_period('M')
    mask = (
        (df["periodo_mensal"] == periodo_selecionado) &
        (df["nome_parceiro"] == parceiro if parceiro != "Todos" else True) &
        (df["banco"] == banco if banco != "Todos" else True) &
        (df["status_titulo"].isin(status_selecionado) if status_selecionado else True)
    )
    df_filtrado = df.loc[mask].copy()
else:
    df_filtrado = pd.DataFrame()

# Cálculos vetorizados
total_valor = df_filtrado["valor"].sum() if not df_filtrado.empty else 0
total_titulos = len(df_filtrado)

# Exibição de métricas
with placeholder_metrics.container():
    st.title("📊 Dashboard de Contratos")
    
    col1, col2 = st.columns(2)
    with col1:
        # Formatação numérica otimizada
        valor_formatado = f"R$ {total_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        st.metric("Valor Total", valor_formatado)
        
    with col2:
        st.metric("Qtd. de Títulos", f"{total_titulos}")

# Gráfico de Pizza
with placeholder_pizza.container():
    st.markdown("""
    <div style="background-color: #f9f9f9; padding: 25px; border-radius: 12px;
                box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.05); margin-bottom: 20px;">
    """, unsafe_allow_html=True)

    st.markdown("## 🥧 Distribuição por Status do Título")
    
    if not df_filtrado.empty:
        # Agregação otimizada
        df_pizza = df_filtrado.groupby("status_titulo", observed=True)["valor"].sum().reset_index()
        
        fig_pizza = px.pie(
            df_pizza,
            names="status_titulo",
            values="valor",
            hole=0.4,
            template="plotly_white"
        )
        fig_pizza.update_traces(
            textinfo='percent+label', 
            hovertemplate='%{label}: R$ %{value:,.2f}<extra></extra>',
            textposition='inside'
        )
        fig_pizza.update_layout(margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_pizza, use_container_width=True)
    else:
        st.warning("Sem dados para exibir o gráfico")

    st.markdown("</div>", unsafe_allow_html=True)

# Gráfico de Barras por Mês
with placeholder_grafico.container():
    st.markdown("""
    <div style="background-color: #f9f9f9; padding: 25px; border-radius: 12px;
                box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.05); margin-top: 20px;">
    """, unsafe_allow_html=True)

    st.markdown("## 📈 Evolução Mensal por Status")
    
    if not df_mes.empty:
        # Otimização: usar dados pré-agregados
        fig_bar = px.bar(
            df_mes,
            x="mes",
            y="valor",
            color="status_titulo",
            labels={"mes": "Mês", "valor": "Valor"},
            template="plotly_white"
        )
        fig_bar.update_layout(
            barmode='stack',
            xaxis_tickformat="%b/%Y",
            margin=dict(t=20, b=20),
            plot_bgcolor="#fff",
            paper_bgcolor="#f9f9f9",
            height=400
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning("Dados mensais não disponíveis")

    st.markdown("</div>", unsafe_allow_html=True)

# Tabela detalhada com paginação
with placeholder_tabela.container():
    st.markdown("""
    <div style="background-color: #f9f9f9; padding: 25px; border-radius: 12px;
                box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.05); margin-top: 20px;">
    """, unsafe_allow_html=True)

    st.markdown("## 📋 Tabela Detalhada por Parceiro e Status")
    
    if not df_filtrado.empty:
        # Agregação otimizada
        tabela = df_filtrado.groupby(["nome_parceiro", "status_titulo"], observed=False)["valor"].sum().reset_index()
        valor_total_geral = tabela["valor"].sum()
        
        # Cálculo vetorizado
        tabela["% do Total"] = (tabela["valor"] / valor_total_geral * 100).round(2)
        
        # Paginação
        items_por_pagina = 10
        total_paginas = max(1, (len(tabela) + items_por_pagina - 1) // items_por_pagina)
        pagina = st.number_input("Página", min_value=1, max_value=total_paginas, value=1, step=1)
        
        inicio = (pagina - 1) * items_por_pagina
        fim = min(inicio + items_por_pagina, len(tabela))
        tabela_paginada = tabela.iloc[inicio:fim].copy()
        
        # Formatação otimizada
        tabela_paginada["valor"] = tabela_paginada["valor"].map(
            lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )
        tabela_paginada["% do Total"] = tabela_paginada["% do Total"].map(lambda x: f"{x}%")
        
        st.dataframe(tabela_paginada, use_container_width=True, hide_index=True)
        st.caption(f"Página {pagina} de {total_paginas} | Total de registros: {len(tabela)}")
    else:
        st.info("Nenhum dado disponível para os filtros selecionados.")

    st.markdown("</div>", unsafe_allow_html=True)