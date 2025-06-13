import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Clientes",
    page_icon="👥",
    layout="wide"
)

# Título
st.title("👥 Dashboard de Clientes")

# Dados de exemplo
np.random.seed(42)
n_clientes = 1000
data = pd.DataFrame({
    'ID_Cliente': range(1, n_clientes + 1),
    'Idade': np.random.randint(18, 80, n_clientes),
    'Valor_Total_Compras': np.random.uniform(100, 10000, n_clientes),
    'Frequencia_Compras': np.random.randint(1, 50, n_clientes),
    'Ultima_Compra': pd.date_range(start='2023-01-01', periods=n_clientes),
    'Segmento': np.random.choice(['Bronze', 'Prata', 'Ouro', 'Platina'], n_clientes, p=[0.4, 0.3, 0.2, 0.1]),
    'Cidade': np.random.choice(['São Paulo', 'Rio de Janeiro', 'Belo Horizonte', 'Salvador', 'Brasília'], n_clientes),
    'Satisfacao': np.random.randint(1, 6, n_clientes)
})

# Sidebar com filtros
st.sidebar.header("Filtros")
segmento = st.sidebar.multiselect(
    "Segmento:",
    options=data['Segmento'].unique(),
    default=data['Segmento'].unique()
)

cidade = st.sidebar.multiselect(
    "Cidade:",
    options=data['Cidade'].unique(),
    default=data['Cidade'].unique()
)

satisfacao = st.sidebar.slider(
    "Nível de Satisfação:",
    min_value=1,
    max_value=5,
    value=(1, 5)
)

# Filtrando dados
data_filtrada = data[
    (data['Segmento'].isin(segmento)) &
    (data['Cidade'].isin(cidade)) &
    (data['Satisfacao'].between(satisfacao[0], satisfacao[1]))
]

# Métricas principais
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total de Clientes", len(data_filtrada), "+5%")
with col2:
    st.metric("Ticket Médio", f"R$ {data_filtrada['Valor_Total_Compras'].mean():,.2f}", "+8%")
with col3:
    st.metric("Satisfação Média", f"{data_filtrada['Satisfacao'].mean():.1f}", "+0.2")
with col4:
    st.metric("Frequência Média", f"{data_filtrada['Frequencia_Compras'].mean():.1f}", "+1.5")

# Gráficos
col1, col2 = st.columns(2)

with col1:
    st.subheader("Distribuição por Segmento")
    fig_seg = px.pie(
        data_filtrada.groupby('Segmento').size().reset_index(name='count'),
        values='count',
        names='Segmento',
        hole=0.4
    )
    st.plotly_chart(fig_seg, use_container_width=True)

with col2:
    st.subheader("Distribuição por Idade")
    fig_idade = px.histogram(
        data_filtrada,
        x='Idade',
        nbins=20,
        color='Segmento'
    )
    st.plotly_chart(fig_idade, use_container_width=True)

# Gráfico de dispersão
st.subheader("Relação entre Valor e Frequência de Compras")
fig_disp = px.scatter(
    data_filtrada,
    x='Frequencia_Compras',
    y='Valor_Total_Compras',
    color='Segmento',
    size='Satisfacao',
    hover_data=['Cidade']
)
st.plotly_chart(fig_disp, use_container_width=True)

# Tabela de dados
st.subheader("Dados dos Clientes")
st.dataframe(data_filtrada)

# Incluir o chatbot
with open('static/chatbot.html', 'r', encoding='utf-8') as f:
    chatbot_html = f.read()
    components.html(chatbot_html, height=600) 