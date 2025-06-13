import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Produtos",
    page_icon="📦",
    layout="wide"
)

# Título
st.title("📦 Dashboard de Produtos")

# Dados de exemplo
np.random.seed(42)
n_produtos = 100
categorias = ['Eletrônicos', 'Vestuário', 'Alimentos', 'Móveis', 'Livros']
data = pd.DataFrame({
    'ID_Produto': range(1, n_produtos + 1),
    'Nome': [f'Produto {i}' for i in range(1, n_produtos + 1)],
    'Categoria': np.random.choice(categorias, n_produtos),
    'Preco': np.random.uniform(10, 1000, n_produtos),
    'Estoque': np.random.randint(0, 100, n_produtos),
    'Vendas_Mes': np.random.randint(0, 50, n_produtos),
    'Avaliacao': np.random.uniform(1, 5, n_produtos),
    'Fornecedor': np.random.choice(['Fornecedor A', 'Fornecedor B', 'Fornecedor C'], n_produtos)
})

# Calculando métricas derivadas
data['Valor_Estoque'] = data['Preco'] * data['Estoque']
data['Rotatividade'] = data['Vendas_Mes'] / data['Estoque'].replace(0, 1)
data['Status_Estoque'] = np.where(data['Estoque'] < 10, 'Baixo', 
                                 np.where(data['Estoque'] < 30, 'Médio', 'Alto'))

# Sidebar com filtros
st.sidebar.header("Filtros")
categoria = st.sidebar.multiselect(
    "Categoria:",
    options=data['Categoria'].unique(),
    default=data['Categoria'].unique()
)

fornecedor = st.sidebar.multiselect(
    "Fornecedor:",
    options=data['Fornecedor'].unique(),
    default=data['Fornecedor'].unique()
)

status_estoque = st.sidebar.multiselect(
    "Status do Estoque:",
    options=data['Status_Estoque'].unique(),
    default=data['Status_Estoque'].unique()
)

# Filtrando dados
data_filtrada = data[
    (data['Categoria'].isin(categoria)) &
    (data['Fornecedor'].isin(fornecedor)) &
    (data['Status_Estoque'].isin(status_estoque))
]

# Métricas principais
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total de Produtos", len(data_filtrada), "+5%")
with col2:
    st.metric("Valor em Estoque", f"R$ {data_filtrada['Valor_Estoque'].sum():,.2f}", "+8%")
with col3:
    st.metric("Produtos com Estoque Baixo", len(data_filtrada[data_filtrada['Status_Estoque'] == 'Baixo']), "-2%")
with col4:
    st.metric("Avaliação Média", f"{data_filtrada['Avaliacao'].mean():.1f}", "+0.2")

# Gráficos
col1, col2 = st.columns(2)

with col1:
    st.subheader("Produtos por Categoria")
    fig_cat = px.bar(
        data_filtrada.groupby('Categoria').size().reset_index(name='count'),
        x='Categoria',
        y='count',
        color='Categoria'
    )
    st.plotly_chart(fig_cat, use_container_width=True)

with col2:
    st.subheader("Distribuição de Preços")
    fig_preco = px.histogram(
        data_filtrada,
        x='Preco',
        color='Categoria',
        nbins=20
    )
    st.plotly_chart(fig_preco, use_container_width=True)

# Gráfico de dispersão
st.subheader("Relação entre Preço e Avaliação")
fig_disp = px.scatter(
    data_filtrada,
    x='Preco',
    y='Avaliacao',
    color='Categoria',
    size='Vendas_Mes',
    hover_data=['Nome', 'Fornecedor']
)
st.plotly_chart(fig_disp, use_container_width=True)

# Tabela de produtos com estoque baixo
st.subheader("Produtos com Estoque Baixo")
produtos_baixo_estoque = data_filtrada[data_filtrada['Status_Estoque'] == 'Baixo']
st.dataframe(produtos_baixo_estoque[['Nome', 'Categoria', 'Estoque', 'Preco', 'Fornecedor']])

# Tabela de dados completa
st.subheader("Dados Completos dos Produtos")
st.dataframe(data_filtrada)

# Incluir o chatbot
with open('static/chatbot.html', 'r', encoding='utf-8') as f:
    chatbot_html = f.read()
    components.html(chatbot_html, height=600) 