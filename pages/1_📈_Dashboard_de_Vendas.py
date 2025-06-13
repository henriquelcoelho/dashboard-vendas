import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Vendas",
    page_icon="📈",
    layout="wide"
)

# Título
st.title("📈 Dashboard de Vendas")

# Dados de exemplo
np.random.seed(42)
dates = pd.date_range(start='2024-01-01', periods=100)
data = pd.DataFrame({
    'Data': dates,
    'Vendas': np.random.randint(1000, 10000, 100),
    'Categoria': np.random.choice(['Eletrônicos', 'Vestuário', 'Alimentos', 'Móveis'], 100),
    'Região': np.random.choice(['Norte', 'Sul', 'Leste', 'Oeste'], 100),
    'Canal': np.random.choice(['Online', 'Loja Física', 'Marketplace'], 100)
})

# Sidebar com filtros
st.sidebar.header("Filtros")
categoria = st.sidebar.multiselect(
    "Categoria:",
    options=data['Categoria'].unique(),
    default=data['Categoria'].unique()
)

regiao = st.sidebar.multiselect(
    "Região:",
    options=data['Região'].unique(),
    default=data['Região'].unique()
)

canal = st.sidebar.multiselect(
    "Canal de Vendas:",
    options=data['Canal'].unique(),
    default=data['Canal'].unique()
)

# Filtrando dados
data_filtrada = data[
    (data['Categoria'].isin(categoria)) &
    (data['Região'].isin(regiao)) &
    (data['Canal'].isin(canal))
]

# Métricas principais
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Vendas Totais", f"R$ {data_filtrada['Vendas'].sum():,.2f}", "+12%")
with col2:
    st.metric("Ticket Médio", f"R$ {data_filtrada['Vendas'].mean():,.2f}", "+5%")
with col3:
    st.metric("Pedidos", len(data_filtrada), "+8%")
with col4:
    st.metric("Crescimento", "+15%", "+3%")

# Gráficos
col1, col2 = st.columns(2)

with col1:
    st.subheader("Vendas por Categoria")
    fig_cat = px.bar(
        data_filtrada.groupby('Categoria')['Vendas'].sum().reset_index(),
        x='Categoria',
        y='Vendas',
        color='Categoria'
    )
    st.plotly_chart(fig_cat, use_container_width=True)

with col2:
    st.subheader("Vendas por Região")
    fig_reg = px.pie(
        data_filtrada.groupby('Região')['Vendas'].sum().reset_index(),
        values='Vendas',
        names='Região',
        hole=0.4
    )
    st.plotly_chart(fig_reg, use_container_width=True)

# Gráfico de linha temporal
st.subheader("Evolução das Vendas")
fig_linha = px.line(
    data_filtrada.groupby('Data')['Vendas'].sum().reset_index(),
    x='Data',
    y='Vendas',
    title='Vendas ao Longo do Tempo'
)
st.plotly_chart(fig_linha, use_container_width=True)

# Tabela de dados
st.subheader("Dados Detalhados")
st.dataframe(data_filtrada)

# Incluir o chatbot
with open('static/chatbot.html', 'r', encoding='utf-8') as f:
    chatbot_html = f.read()
    components.html(chatbot_html, height=600) 