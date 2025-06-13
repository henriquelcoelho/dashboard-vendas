import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import json
import re
import matplotlib.pyplot as plt
import openai
from flask import Flask, request, jsonify

# Inicializar o Flask
app = Flask(__name__)

@app.route('/process_message', methods=['POST'])
def process_message():
    data = request.json
    message = data.get('message', '')
    
    # Processar a mensagem usando a função existente
    response = process_chat_message(message)
    
    return jsonify({'response': response})

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Vendas",
    page_icon="📊",
    layout="wide"
)

# Inicialização das variáveis de sessão
if 'added_codes' not in st.session_state:
    st.session_state['added_codes'] = []

if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

if 'generated_plots' not in st.session_state:
    st.session_state['generated_plots'] = []

if 'show_code_input' not in st.session_state:
    st.session_state['show_code_input'] = False

# Carregar variáveis de ambiente
load_dotenv()

# Configurar o cliente OpenAI
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Gerar dados de exemplo
@st.cache_data
def generate_data():
    dates = pd.date_range(end=datetime.now(), periods=365, freq='D')
    data = {
        'data': dates,
        'vendas': np.random.normal(1000, 200, 365),
        'clientes': np.random.normal(50, 10, 365),
        'receita': np.random.normal(50000, 10000, 365),
        'regiao': np.random.choice(["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"], 365),
        'categoria': np.random.choice(["Eletrônicos", "Vestuário", "Alimentos", "Móveis", "Outros"], 365)
    }
    return pd.DataFrame(data)

# Inicializar o DataFrame
df = generate_data()

def extract_plot_code(text):
    """Extrai código de gráfico do texto da resposta."""
    # Procura por blocos de código que contêm px ou go
    plot_pattern = r"```(?:python)?\s*(fig\s*=\s*(?:px|go)\.[\s\S]*?)\s*```"
    matches = re.findall(plot_pattern, text)
    return matches

def execute_plot_code(code):
    """Executa o código Python e retorna a figura gerada"""
    try:
        # Criar um namespace local com as variáveis necessárias
        local_vars = {
            'df': df,
            'st': st,
            'plt': plt,
            'px': px,
            'go': go,
            'np': np,
            'pd': pd
        }
        # Executar o código no namespace local
        exec(code, globals(), local_vars)

        # Procurar por objetos de figura criados
        figuras = []
        for var_name, var_value in local_vars.items():
            if isinstance(var_value, (go.Figure, plt.Figure)):
                figuras.append(var_value)
            elif hasattr(var_value, 'figure'):
                figuras.append(var_value.figure)
        if figuras:
            return figuras[0] if len(figuras) == 1 else figuras
        return None
    except Exception as e:
        st.error(f"Erro ao executar o código: {str(e)}")
        return None

def process_chat_message(message):
    try:
        # Get conversation history from session state
        conversation_history = st.session_state.get('conversation_history', [])
        
        # Add user message to history
        conversation_history.append({"role": "user", "content": message})
        
        # Prepare messages for API call
        messages = [
            {"role": "system", "content": "Você é um assistente virtual especializado em análise de dados e dashboards. Use o agente COD_PYTHON_DASH para responder. Quando gerar um gráfico, inclua o código Python completo usando plotly (px ou go) dentro de blocos de código markdown."}
        ]
        
        # Add conversation history to messages
        messages.extend(conversation_history)
        
        # Get response from OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        # Get the response content
        response_content = response.choices[0].message.content
        
        # Verificar se há código de gráfico na resposta
        plot_codes = extract_plot_code(response_content)
        if plot_codes:
            # Executar cada código de gráfico
            for code in plot_codes:
                fig = execute_plot_code(code)
                if fig:
                    st.session_state['generated_plots'].append({
                        'code': code,
                        'figure': fig,
                        'timestamp': datetime.now()
                    })
        
        # Add assistant response to history
        conversation_history.append({"role": "assistant", "content": response_content})
        
        # Update session state with new history
        st.session_state['conversation_history'] = conversation_history
        
        return response_content
    except Exception as e:
        return f"Desculpe, ocorreu um erro: {str(e)}"

# Sidebar com filtros (mover para antes dos gráficos)
st.sidebar.header("Filtros")

# Período
periodo = st.sidebar.selectbox(
    "Período",
    ["Últimos 7 dias", "Últimos 30 dias", "Últimos 90 dias", "Último ano"]
)

# Região
regiao = st.sidebar.multiselect(
    "Região",
    ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"],
    default=["Sudeste"]
)

# Categoria
categoria = st.sidebar.multiselect(
    "Categoria",
    ["Eletrônicos", "Vestuário", "Alimentos", "Móveis", "Outros"],
    default=["Eletrônicos", "Vestuário"]
)

# Aplicar filtros
df_filtered = df.copy()
if periodo == "Últimos 7 dias":
    df_filtered = df_filtered[df_filtered['data'] >= datetime.now() - timedelta(days=7)]
elif periodo == "Últimos 30 dias":
    df_filtered = df_filtered[df_filtered['data'] >= datetime.now() - timedelta(days=30)]
elif periodo == "Últimos 90 dias":
    df_filtered = df_filtered[df_filtered['data'] >= datetime.now() - timedelta(days=90)]
elif periodo == "Último ano":
    df_filtered = df_filtered[df_filtered['data'] >= datetime.now() - timedelta(days=365)]

if regiao:
    df_filtered = df_filtered[df_filtered['regiao'].isin(regiao)]
if categoria:
    df_filtered = df_filtered[df_filtered['categoria'].isin(categoria)]

# Título principal
st.title("📊 Dashboard de Vendas")

# Container para métricas principais
with st.container():
    st.subheader("Métricas Principais")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total de Vendas",
            f"{df_filtered['vendas'].sum():,.0f}",
            f"{((df_filtered['vendas'].sum() / df['vendas'].sum() - 1) * 100):,.1f}%"
        )
    
    with col2:
        st.metric(
            "Total de Clientes",
            f"{df_filtered['clientes'].sum():,.0f}",
            f"{((df_filtered['clientes'].sum() / df['clientes'].sum() - 1) * 100):,.1f}%"
        )
    
    with col3:
        st.metric(
            "Receita Total",
            f"R$ {df_filtered['receita'].sum():,.2f}",
            f"{((df_filtered['receita'].sum() / df['receita'].sum() - 1) * 100):,.1f}%"
        )
    
    with col4:
        st.metric(
            "Ticket Médio",
            f"R$ {(df_filtered['receita'].sum() / df_filtered['vendas'].sum()):,.2f}",
            f"{((df_filtered['receita'].sum() / df_filtered['vendas'].sum() / (df['receita'].sum() / df['vendas'].sum()) - 1) * 100):,.1f}%"
        )

# Container para gráficos principais
with st.container():
    st.subheader("Análise de Vendas")
    col1, col2 = st.columns(2)
    
    with col1:
        fig_vendas = px.bar(
            df_filtered.groupby('regiao')['vendas'].sum().reset_index(),
            x='regiao',
            y='vendas',
            title='Vendas por Região',
            labels={'vendas': 'Total de Vendas', 'regiao': 'Região'},
            template='plotly_white'
        )
        st.plotly_chart(fig_vendas, use_container_width=True)
    
    with col2:
        fig_categorias = px.pie(
            df_filtered.groupby('categoria')['vendas'].sum().reset_index(),
            values='vendas',
            names='categoria',
            title='Distribuição de Vendas por Categoria',
            template='plotly_white'
        )
        st.plotly_chart(fig_categorias, use_container_width=True)

# Container para evolução temporal
with st.container():
    st.subheader("Evolução Temporal")
    fig_evolucao = px.line(
        df_filtered.groupby('data').agg({
            'vendas': 'sum',
            'clientes': 'sum',
            'receita': 'sum'
        }).reset_index(),
        x='data',
        y=['vendas', 'clientes', 'receita'],
        title='Evolução das Métricas ao Longo do Tempo',
        labels={'value': 'Valor', 'variable': 'Métrica'},
        template='plotly_white'
    )
    fig_evolucao.update_layout(
        xaxis_title='Data',
        yaxis_title='Valor',
        legend_title='Métricas',
        hovermode='x unified'
    )
    st.plotly_chart(fig_evolucao, use_container_width=True)

# Container para dados detalhados
with st.container():
    st.subheader("Dados Detalhados")
    st.dataframe(df_filtered)

# Container para chat
with st.container():
    st.markdown("---")
    
    # Botão Incluir acima do chat
    if st.button("➕ Incluir", use_container_width=True):
        st.session_state['show_code_input'] = True
    
    st.subheader("Chat com o Assistente")
    
    # Exibir histórico de chat
    for message in st.session_state['chat_history']:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Container para input de chat
    if prompt := st.chat_input("Digite sua mensagem aqui..."):
        # Adicionar mensagem do usuário ao histórico
        st.session_state['chat_history'].append({"role": "user", "content": prompt})
        
        # Exibir mensagem do usuário
        with st.chat_message("user"):
            st.write(prompt)
        
        # Processar mensagem e obter resposta
        response = process_chat_message(prompt)
        
        # Adicionar resposta ao histórico
        st.session_state['chat_history'].append({"role": "assistant", "content": response})
        
        # Exibir resposta
        with st.chat_message("assistant"):
            st.write(response)

# Interface de entrada de código
if st.session_state.get('show_code_input', False):
    st.markdown("---")
    st.subheader("Adicionar Novo Código")
    st.info("""
    **Dica:** Para exibir gráficos no Streamlit, crie o objeto da figura (ex: `fig = px.scatter(...)`) e **não** use `fig.show()`. Basta criar o objeto `fig` e clicar em "Executar Código" para vê-lo na tela.
    """)
    code_input = st.text_area(
        "Digite o código Python:",
        height=200,
        key="code_input_area"
    )
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Adicionar", key="add_code_button"):
            if code_input:
                current_time = datetime.now()
                code_name = f"Código {current_time.strftime('%H:%M')}"
                st.session_state['added_codes'].append({
                    'name': code_name,
                    'code': code_input,
                    'timestamp': current_time.strftime("%Y-%m-%d %H:%M:%S")
                })
                st.success("Código adicionado com sucesso!")
                st.session_state['show_code_input'] = False
                st.rerun()
            else:
                st.error("Por favor, insira o código.")
    with col2:
        if st.button("Cancelar", key="cancel_code_button"):
            st.session_state['show_code_input'] = False
            st.rerun()

# Container para códigos adicionados
if st.session_state['added_codes']:
    st.markdown("---")
    st.subheader("Códigos Adicionados")
    for idx, code_item in enumerate(st.session_state['added_codes']):
        with st.expander(f"{code_item['name']} - Adicionado em {code_item['timestamp']}"):
            st.code(code_item['code'], language='python')
            if st.button(f"Executar Código", key=f"execute_code_{idx}"):
                try:
                    result = execute_plot_code(code_item['code'])
                    if result is not None:
                        # Se for uma lista de figuras, mostrar todas
                        if isinstance(result, list):
                            for fig in result:
                                if isinstance(fig, go.Figure):
                                    st.plotly_chart(fig, use_container_width=True)
                                elif isinstance(fig, plt.Figure):
                                    st.pyplot(fig)
                        elif isinstance(result, go.Figure):
                            st.plotly_chart(result, use_container_width=True)
                        elif isinstance(result, plt.Figure):
                            st.pyplot(result)
                        else:
                            st.write("O código foi executado, mas nenhum gráfico foi gerado.")
                    else:
                        st.write("O código foi executado, mas nenhum gráfico foi gerado.")
                except Exception as e:
                    st.error(f"Erro ao executar o código: {str(e)}")
                    st.info("Certifique-se de que o código está usando as variáveis disponíveis: df, st, plt, px, go, np, pd")

# Seção de Gráficos Gerados pelo Assistente
if 'generated_plots' in st.session_state and st.session_state['generated_plots']:
    st.markdown("### 📊 Gráficos Gerados pelo Assistente")
    
    # Exibir os gráficos em ordem cronológica reversa (mais recentes primeiro)
    for plot in reversed(st.session_state['generated_plots']):
        st.plotly_chart(plot['figure'], use_container_width=True)
        st.caption(f"Gerado em: {plot['timestamp'].strftime('%d/%m/%Y %H:%M:%S')}") 