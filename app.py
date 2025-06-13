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
from openai import OpenAI
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
    layout="wide",
    initial_sidebar_state="expanded"
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

# Configurar a API OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Gerar dados de exemplo
@st.cache_data
def generate_data():
    dates = pd.date_range(end=datetime.now(), periods=365, freq='D')
    data = {
        'data': dates,
        'vendas': np.random.normal(1000, 200, 365).clip(min=0),  # Garantir valores positivos
        'clientes': np.random.normal(50, 10, 365).clip(min=0),   # Garantir valores positivos
        'receita': np.random.normal(50000, 10000, 365).clip(min=0),  # Garantir valores positivos
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

# Sidebar para filtros
with st.sidebar:
    st.header("Filtros")
    
    # Filtro de período
    st.subheader("Período")
    data_inicio = st.date_input(
        "Data Inicial",
        value=df['data'].min(),
        min_value=df['data'].min(),
        max_value=df['data'].max()
    )
    data_fim = st.date_input(
        "Data Final",
        value=df['data'].max(),
        min_value=df['data'].min(),
        max_value=df['data'].max()
    )
    
    # Filtro de região
    st.subheader("Região")
    regioes = ["Todas"] + sorted(df['regiao'].unique().tolist())
    regiao_selecionada = st.selectbox("Selecione a região", regioes)
    
    # Filtro de categoria
    st.subheader("Categoria")
    categorias = ["Todas"] + sorted(df['categoria'].unique().tolist())
    categoria_selecionada = st.selectbox("Selecione a categoria", categorias)

# Aplicar filtros
df_filtered = df.copy()
df_filtered = df_filtered[
    (df_filtered['data'].dt.date >= data_inicio) &
    (df_filtered['data'].dt.date <= data_fim)
]

if regiao_selecionada != "Todas":
    df_filtered = df_filtered[df_filtered['regiao'] == regiao_selecionada]

if categoria_selecionada != "Todas":
    df_filtered = df_filtered[df_filtered['categoria'] == categoria_selecionada]

# Título principal
st.title("📊 Dashboard de Vendas Interativo")
st.markdown("""
    Este dashboard permite visualizar e analisar dados de vendas de forma interativa.
    Utilize os filtros na barra lateral para personalizar sua análise.
""")

# Container para métricas principais
with st.container():
    st.subheader("Métricas Principais")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_vendas = df_filtered['vendas'].sum()
        total_vendas_anterior = df['vendas'].sum()
        variacao_vendas = ((total_vendas / total_vendas_anterior - 1) * 100) if total_vendas_anterior > 0 else 0
        st.metric(
            "Total de Vendas",
            f"{total_vendas:,.0f}",
            f"{variacao_vendas:,.1f}%"
        )
    
    with col2:
        total_clientes = df_filtered['clientes'].sum()
        total_clientes_anterior = df['clientes'].sum()
        variacao_clientes = ((total_clientes / total_clientes_anterior - 1) * 100) if total_clientes_anterior > 0 else 0
        st.metric(
            "Total de Clientes",
            f"{total_clientes:,.0f}",
            f"{variacao_clientes:,.1f}%"
        )
    
    with col3:
        total_receita = df_filtered['receita'].sum()
        total_receita_anterior = df['receita'].sum()
        variacao_receita = ((total_receita / total_receita_anterior - 1) * 100) if total_receita_anterior > 0 else 0
        st.metric(
            "Receita Total",
            f"R$ {total_receita:,.2f}",
            f"{variacao_receita:,.1f}%"
        )
    
    with col4:
        ticket_medio = total_receita / total_vendas if total_vendas > 0 else 0
        ticket_medio_anterior = total_receita_anterior / total_vendas_anterior if total_vendas_anterior > 0 else 0
        variacao_ticket = ((ticket_medio / ticket_medio_anterior - 1) * 100) if ticket_medio_anterior > 0 else 0
        st.metric(
            "Ticket Médio",
            f"R$ {ticket_medio:,.2f}",
            f"{variacao_ticket:,.1f}%"
        )

# Container para gráficos principais
with st.container():
    st.subheader("Análise de Vendas")
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de barras por região
        vendas_por_regiao = df_filtered.groupby('regiao')['vendas'].sum().reset_index()
        fig_vendas = px.bar(
            vendas_por_regiao,
            x='regiao',
            y='vendas',
            title='Vendas por Região',
            labels={'vendas': 'Total de Vendas', 'regiao': 'Região'},
            template='plotly_white',
            color='regiao'
        )
        fig_vendas.update_layout(
            showlegend=False,
            xaxis_title='Região',
            yaxis_title='Total de Vendas',
            title_x=0.5
        )
        st.plotly_chart(fig_vendas, use_container_width=True)
    
    with col2:
        # Gráfico de pizza por categoria
        vendas_por_categoria = df_filtered.groupby('categoria')['vendas'].sum().reset_index()
        fig_categorias = px.pie(
            vendas_por_categoria,
            values='vendas',
            names='categoria',
            title='Distribuição de Vendas por Categoria',
            template='plotly_white',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_categorias.update_layout(
            title_x=0.5,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            )
        )
        st.plotly_chart(fig_categorias, use_container_width=True)

# Container para evolução temporal
with st.container():
    st.subheader("Evolução Temporal")
    
    # Preparar dados para o gráfico de evolução
    evolucao_data = df_filtered.groupby('data').agg({
        'vendas': 'sum',
        'clientes': 'sum',
        'receita': 'sum'
    }).reset_index()
    
    # Criar gráfico de linha
    fig_evolucao = px.line(
        evolucao_data,
        x='data',
        y=['vendas', 'clientes', 'receita'],
        title='Evolução das Métricas ao Longo do Tempo',
        labels={'value': 'Valor', 'variable': 'Métrica'},
        template='plotly_white',
        color_discrete_sequence=px.colors.qualitative.Set1
    )
    
    # Atualizar layout
    fig_evolucao.update_layout(
        xaxis_title='Data',
        yaxis_title='Valor',
        legend_title='Métricas',
        hovermode='x unified',
        title_x=0.5,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )
    
    # Adicionar botões de zoom
    fig_evolucao.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=7, label="1w", step="day", stepmode="backward"),
                dict(count=30, label="1m", step="day", stepmode="backward"),
                dict(count=90, label="3m", step="day", stepmode="backward"),
                dict(count=180, label="6m", step="day", stepmode="backward"),
                dict(count=365, label="1y", step="day", stepmode="backward"),
                dict(step="all", label="All")
            ])
        )
    )
    
    st.plotly_chart(fig_evolucao, use_container_width=True)

# Container para dados detalhados
with st.container():
    st.subheader("Dados Detalhados")
    st.dataframe(df_filtered, use_container_width=True)

# Container para chat
with st.container():
    st.markdown("---")
    
    # Botão Incluir acima do chat
    if st.button("➕ Incluir", use_container_width=True):
        st.session_state['show_code_input'] = True
    
    st.subheader("Chat com o Assistente")
    
    # Inicializar histórico de chat se não existir
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []
    
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
        
        try:
            # Preparar o contexto com os dados
            context = f"""
            Dados de vendas:
            - Total de vendas: {total_vendas:,.0f}
            - Total de clientes: {total_clientes:,.0f}
            - Receita total: R$ {total_receita:,.2f}
            - Ticket médio: R$ {ticket_medio:,.2f}
            
            Vendas por região:
            {vendas_por_regiao.to_string()}
            
            Vendas por categoria:
            {vendas_por_categoria.to_string()}
            """
            
            # Criar o prompt para o GPT
            messages = [
                {"role": "system", "content": "Você é um assistente especializado em análise de dados de vendas."},
                {"role": "user", "content": f"Contexto: {context}\n\nPergunta: {prompt}"}
            ]
            
            # Fazer a chamada à API
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            # Obter a resposta
            assistant_response = response.choices[0].message.content
            
            # Adicionar resposta ao histórico
            st.session_state['chat_history'].append({"role": "assistant", "content": assistant_response})
            
            # Exibir resposta
            with st.chat_message("assistant"):
                st.write(assistant_response)
            
        except Exception as e:
            error_message = f"Erro ao processar a pergunta: {str(e)}"
            st.error(error_message)
            st.session_state['chat_history'].append({"role": "assistant", "content": error_message})

# Interface de entrada de código
if st.session_state.get('show_code_input', False):
    st.markdown("---")
    st.subheader("Interface de Entrada de Código")
    st.info("""
    **Dica:** Para exibir gráficos no Streamlit:
    1. Para Plotly: crie o objeto da figura (ex: `fig = px.scatter(...)`) e **não** use `fig.show()`
    2. Para Matplotlib: crie a figura (ex: `fig = plt.figure()`) e **não** use `plt.show()`
    Basta criar o objeto da figura e clicar em "Executar Código" para vê-lo na tela.
    """)
    
    # Campo de entrada de código
    code_input = st.text_area(
        "Digite seu código Python:",
        height=200,
        key="code_input_area"
    )
    
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Executar e Salvar", key="execute_code_button"):
            if code_input:
                try:
                    # Criar um namespace local para execução
                    local_vars = {
                        'df': df,
                        'df_filtered': df_filtered,
                        'px': px,
                        'st': st,
                        'pd': pd,
                        'np': np,
                        'plt': plt,
                        'go': go
                    }
                    
                    # Executar o código
                    exec(code_input, globals(), local_vars)
                    
                    # Verificar se algum gráfico foi criado
                    for var_name, var_value in local_vars.items():
                        if isinstance(var_value, go.Figure):
                            st.plotly_chart(var_value, use_container_width=True)
                        elif isinstance(var_value, plt.Figure):
                            st.pyplot(var_value)
                    
                    # Verificar se há uma figura atual do matplotlib
                    if plt.get_fignums():
                        st.pyplot(plt.gcf())
                        plt.close('all')  # Limpar as figuras após exibir
                    
                    # Salvar o código
                    current_time = datetime.now()
                    code_name = f"Código {current_time.strftime('%H:%M')}"
                    st.session_state['added_codes'].append({
                        'name': code_name,
                        'code': code_input,
                        'timestamp': current_time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
                    st.success("Código executado e salvo com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao executar o código: {str(e)}")
            else:
                st.error("Por favor, insira o código.")
    
    with col2:
        if st.button("Cancelar", key="cancel_code_button"):
            st.session_state['show_code_input'] = False
            st.experimental_rerun()

# Container para códigos adicionados
if st.session_state['added_codes']:
    st.markdown("---")
    st.subheader("Códigos Salvos")
    
    for idx, code_item in enumerate(st.session_state['added_codes']):
        with st.expander(f"{code_item['name']} - {code_item['timestamp']}"):
            st.code(code_item['code'], language='python')
            
            col1, col2 = st.columns([1, 5])
            with col1:
                if st.button("Executar", key=f"run_saved_{idx}"):
                    try:
                        # Criar um namespace local para execução
                        local_vars = {
                            'df': df,
                            'df_filtered': df_filtered,
                            'px': px,
                            'st': st,
                            'pd': pd,
                            'np': np,
                            'plt': plt,
                            'go': go
                        }
                        
                        # Executar o código
                        exec(code_item['code'], globals(), local_vars)
                        
                        # Verificar se algum gráfico foi criado
                        for var_name, var_value in local_vars.items():
                            if isinstance(var_value, go.Figure):
                                st.plotly_chart(var_value, use_container_width=True)
                            elif isinstance(var_value, plt.Figure):
                                st.pyplot(var_value)
                        
                        # Verificar se há uma figura atual do matplotlib
                        if plt.get_fignums():
                            st.pyplot(plt.gcf())
                            plt.close('all')  # Limpar as figuras após exibir
                        
                        st.success("Código executado com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao executar o código: {str(e)}")
            
            with col2:
                if st.button("Remover", key=f"remove_{idx}"):
                    st.session_state['added_codes'].pop(idx)
                    st.experimental_rerun()

# Seção de Gráficos Gerados pelo Assistente
if 'generated_plots' in st.session_state and st.session_state['generated_plots']:
    st.markdown("### 📊 Gráficos Gerados pelo Assistente")
    
    # Exibir os gráficos em ordem cronológica reversa (mais recentes primeiro)
    for plot in reversed(st.session_state['generated_plots']):
        st.plotly_chart(plot['figure'], use_container_width=True)
        st.caption(f"Gerado em: {plot['timestamp'].strftime('%d/%m/%Y %H:%M:%S')}") 