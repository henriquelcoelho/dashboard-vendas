import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components

# Configuração da página
st.set_page_config(
    page_title="Dashboard Financeiro",
    page_icon="📊",
    layout="wide"
)

# Título
st.title("📊 Dashboard Financeiro")

# Dados de exemplo
np.random.seed(42)
dates = pd.date_range(start='2024-01-01', periods=12)
data = pd.DataFrame({
    'Data': dates,
    'Receita': np.random.uniform(100000, 500000, 12),
    'Custos': np.random.uniform(50000, 200000, 12),
    'Despesas_Operacionais': np.random.uniform(20000, 100000, 12),
    'Investimentos': np.random.uniform(10000, 50000, 12),
    'Impostos': np.random.uniform(10000, 80000, 12)
})

# Calculando métricas derivadas
data['Lucro_Bruto'] = data['Receita'] - data['Custos']
data['Lucro_Liquido'] = data['Lucro_Bruto'] - data['Despesas_Operacionais'] - data['Impostos']
data['Margem_Bruta'] = (data['Lucro_Bruto'] / data['Receita']) * 100
data['Margem_Liquida'] = (data['Lucro_Liquido'] / data['Receita']) * 100

# Sidebar com filtros
st.sidebar.header("Filtros")
periodo = st.sidebar.select_slider(
    "Período:",
    options=data['Data'].dt.strftime('%Y-%m').tolist(),
    value=(data['Data'].dt.strftime('%Y-%m').iloc[0], data['Data'].dt.strftime('%Y-%m').iloc[-1])
)

# Filtrando dados
data_filtrada = data[
    (data['Data'].dt.strftime('%Y-%m') >= periodo[0]) &
    (data['Data'].dt.strftime('%Y-%m') <= periodo[1])
]

# Métricas principais
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Receita Total", f"R$ {data_filtrada['Receita'].sum():,.2f}", "+15%")
with col2:
    st.metric("Lucro Líquido", f"R$ {data_filtrada['Lucro_Liquido'].sum():,.2f}", "+8%")
with col3:
    st.metric("Margem Líquida", f"{data_filtrada['Margem_Liquida'].mean():.1f}%", "+2.5%")
with col4:
    st.metric("ROI", "18.5%", "+3.2%")

# Gráficos
col1, col2 = st.columns(2)

with col1:
    st.subheader("Evolução da Receita e Custos")
    fig_evol = go.Figure()
    fig_evol.add_trace(go.Scatter(x=data_filtrada['Data'], y=data_filtrada['Receita'], name='Receita'))
    fig_evol.add_trace(go.Scatter(x=data_filtrada['Data'], y=data_filtrada['Custos'], name='Custos'))
    st.plotly_chart(fig_evol, use_container_width=True)

with col2:
    st.subheader("Composição das Despesas")
    fig_desp = px.pie(
        data_filtrada,
        values=[data_filtrada['Custos'].sum(), 
                data_filtrada['Despesas_Operacionais'].sum(),
                data_filtrada['Impostos'].sum(),
                data_filtrada['Investimentos'].sum()],
        names=['Custos', 'Despesas Operacionais', 'Impostos', 'Investimentos'],
        hole=0.4
    )
    st.plotly_chart(fig_desp, use_container_width=True)

# Gráfico de barras empilhadas
st.subheader("Análise de Margens")
fig_margens = go.Figure()
fig_margens.add_trace(go.Bar(
    x=data_filtrada['Data'],
    y=data_filtrada['Margem_Bruta'],
    name='Margem Bruta'
))
fig_margens.add_trace(go.Bar(
    x=data_filtrada['Data'],
    y=data_filtrada['Margem_Liquida'],
    name='Margem Líquida'
))
st.plotly_chart(fig_margens, use_container_width=True)

# Tabela de dados
st.subheader("Dados Financeiros Detalhados")
st.dataframe(data_filtrada)

# Incluir o chatbot
with open('static/chatbot.html', 'r', encoding='utf-8') as f:
    chatbot_html = f.read()
    components.html(chatbot_html, height=600) 