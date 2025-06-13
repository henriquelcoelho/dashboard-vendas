import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Marketing",
    page_icon="📱",
    layout="wide"
)

# Título
st.title("📱 Dashboard de Marketing")

# Dados de exemplo
np.random.seed(42)
dates = pd.date_range(start='2024-01-01', periods=30)
canais = ['Facebook', 'Instagram', 'Google Ads', 'Email', 'LinkedIn']
data = pd.DataFrame({
    'Data': dates,
    'Canal': np.random.choice(canais, 30),
    'Impressoes': np.random.randint(1000, 100000, 30),
    'Cliques': np.random.randint(100, 10000, 30),
    'Conversoes': np.random.randint(10, 1000, 30),
    'Custo': np.random.uniform(100, 5000, 30),
    'Valor_Conversao': np.random.uniform(50, 500, 30)
})

# Calculando métricas derivadas
data['CTR'] = (data['Cliques'] / data['Impressoes']) * 100
data['CPA'] = data['Custo'] / data['Conversoes']
data['ROI'] = ((data['Valor_Conversao'] * data['Conversoes']) - data['Custo']) / data['Custo'] * 100

# Sidebar com filtros
st.sidebar.header("Filtros")
canal = st.sidebar.multiselect(
    "Canal:",
    options=data['Canal'].unique(),
    default=data['Canal'].unique()
)

data_inicio = st.sidebar.date_input(
    "Data Inicial:",
    value=data['Data'].min()
)

data_fim = st.sidebar.date_input(
    "Data Final:",
    value=data['Data'].max()
)

# Filtrando dados
data_filtrada = data[
    (data['Canal'].isin(canal)) &
    (data['Data'].dt.date >= data_inicio) &
    (data['Data'].dt.date <= data_fim)
]

# Métricas principais
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Investido", f"R$ {data_filtrada['Custo'].sum():,.2f}", "+15%")
with col2:
    st.metric("Conversões", f"{data_filtrada['Conversoes'].sum():,.0f}", "+8%")
with col3:
    st.metric("CPA Médio", f"R$ {data_filtrada['CPA'].mean():,.2f}", "-5%")
with col4:
    st.metric("ROI Médio", f"{data_filtrada['ROI'].mean():,.1f}%", "+12%")

# Gráficos
col1, col2 = st.columns(2)

with col1:
    st.subheader("Desempenho por Canal")
    fig_canal = px.bar(
        data_filtrada.groupby('Canal').agg({
            'Impressoes': 'sum',
            'Cliques': 'sum',
            'Conversoes': 'sum'
        }).reset_index(),
        x='Canal',
        y=['Impressoes', 'Cliques', 'Conversoes'],
        barmode='group'
    )
    st.plotly_chart(fig_canal, use_container_width=True)

with col2:
    st.subheader("ROI por Canal")
    fig_roi = px.bar(
        data_filtrada.groupby('Canal')['ROI'].mean().reset_index(),
        x='Canal',
        y='ROI',
        color='ROI',
        color_continuous_scale='RdYlGn'
    )
    st.plotly_chart(fig_roi, use_container_width=True)

# Gráfico de linha temporal
st.subheader("Evolução das Métricas")
fig_evol = go.Figure()
fig_evol.add_trace(go.Scatter(x=data_filtrada['Data'], y=data_filtrada['CTR'], name='CTR'))
fig_evol.add_trace(go.Scatter(x=data_filtrada['Data'], y=data_filtrada['CPA'], name='CPA'))
fig_evol.add_trace(go.Scatter(x=data_filtrada['Data'], y=data_filtrada['ROI'], name='ROI'))
st.plotly_chart(fig_evol, use_container_width=True)

# Tabela de dados
st.subheader("Dados Detalhados das Campanhas")
st.dataframe(data_filtrada)

# Incluir o chatbot
with open('static/chatbot.html', 'r', encoding='utf-8') as f:
    chatbot_html = f.read()
    components.html(chatbot_html, height=600) 