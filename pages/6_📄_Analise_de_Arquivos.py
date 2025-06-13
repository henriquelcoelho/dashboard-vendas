import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
from dotenv import load_dotenv
from openai import OpenAI
import matplotlib.pyplot as plt
import io

# Configuração da página
st.set_page_config(
    page_title="Análise de Arquivos",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Carregar variáveis de ambiente
load_dotenv()

# Configurar a API OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Título e descrição
st.title("📄 Análise de Arquivos")
st.markdown("""
    Esta página permite fazer upload de múltiplos arquivos para análise pelo assistente virtual.
    Formatos suportados: CSV, Excel, JSON, TXT
""")

# Inicializar o dicionário de DataFrames na sessão
if 'dataframes' not in st.session_state:
    st.session_state['dataframes'] = {}

# Função para processar diferentes tipos de arquivo
def process_file(file):
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file)
        elif file.name.endswith('.json'):
            df = pd.read_json(file)
        elif file.name.endswith('.txt'):
            df = pd.read_csv(file, sep='\t')
        else:
            st.error("Formato de arquivo não suportado!")
            return None
        return df
    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {str(e)}")
        return None

# Container para upload de arquivo
with st.container():
    st.subheader("Upload de Arquivos")
    uploaded_file = st.file_uploader(
        "Escolha um arquivo para análise",
        type=['csv', 'xlsx', 'xls', 'json', 'txt']
    )

    if uploaded_file is not None:
        # Processar o arquivo
        df = process_file(uploaded_file)
        
        if df is not None:
            # Salvar o DataFrame na sessão
            st.session_state['dataframes'][uploaded_file.name] = df
            st.success(f"Arquivo '{uploaded_file.name}' carregado com sucesso!")

# Exibir lista de arquivos carregados
if st.session_state['dataframes']:
    st.markdown("---")
    st.subheader("Arquivos Carregados")
    
    for filename, df in st.session_state['dataframes'].items():
        with st.expander(f"📄 {filename}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Número de Linhas", f"{len(df):,}")
            with col2:
                st.metric("Número de Colunas", f"{len(df.columns):,}")
            with col3:
                st.metric("Tamanho do Arquivo", f"{df.memory_usage(deep=True).sum() / 1024:.2f} KB")
            
            st.dataframe(df.head(), use_container_width=True)
            
            if st.button(f"Remover {filename}", key=f"remove_{filename}"):
                del st.session_state['dataframes'][filename]
                st.experimental_rerun()

# Container para chat com o assistente
if st.session_state['dataframes']:
    with st.container():
        st.markdown("---")
        st.subheader("Chat com o Assistente")
        
        # Botão Incluir acima do chat
        if st.button("➕ Incluir", use_container_width=True, key="file_include_button"):
            st.session_state['show_file_code_input'] = True
        
        # Inicializar histórico de chat se não existir
        if 'file_chat_history' not in st.session_state:
            st.session_state['file_chat_history'] = []
        
        # Exibir histórico de chat
        for message in st.session_state['file_chat_history']:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # Container para input de chat
        if prompt := st.chat_input("Faça uma pergunta sobre os dados dos arquivos..."):
            # Adicionar mensagem do usuário ao histórico
            st.session_state['file_chat_history'].append({"role": "user", "content": prompt})
            
            # Exibir mensagem do usuário
            with st.chat_message("user"):
                st.write(prompt)
            
            try:
                # Preparar o contexto com os dados de todos os arquivos
                context = "Informações dos arquivos carregados:\n\n"
                for filename, df in st.session_state['dataframes'].items():
                    context += f"""
                    Arquivo: {filename}
                    - Número de linhas: {len(df)}
                    - Número de colunas: {len(df.columns)}
                    - Colunas: {', '.join(df.columns)}
                    
                    Primeiras linhas:
                    {df.head().to_string()}
                    
                    Estatísticas básicas:
                    {df.describe().to_string()}
                    
                    ---
                    """
                
                # Criar o prompt para o GPT
                messages = [
                    {"role": "system", "content": """Você é um assistente especializado em análise de dados. 
                    Use o contexto fornecido para responder às perguntas sobre os dados dos arquivos.
                    
                    IMPORTANTE: 
                    1. Ao gerar código Python, use a variável 'dataframes' que contém todos os DataFrames carregados
                    2. Para acessar um DataFrame específico, use: df = dataframes['nome_do_arquivo']
                    3. NÃO tente ler os arquivos novamente, pois eles já estão carregados em memória
                    4. Você pode combinar dados de diferentes arquivos se necessário
                    5. SEMPRE verifique os tipos de dados antes de fazer operações:
                       - Use df.dtypes para ver os tipos de cada coluna
                       - Use df.head() para visualizar os dados
                       - Converta colunas para o tipo correto se necessário (ex: pd.to_numeric())
                    
                    EXEMPLOS DE ANÁLISES QUE VOCÊ PODE FAZER:
                    1. Análises Univariadas:
                       - Distribuição de vendas por região
                       - Níveis de competências por função
                       - Histogramas de estoque
                       - Box plots de vendas
                    
                    2. Análises Bivariadas:
                       - Relação entre vendas e estoque
                       - Competências vs. Níveis esperados
                       - Vendas por mês e região
                    
                    3. Análises Multivariadas:
                       - Vendas, estoque e região
                       - Competências, níveis e funções
                    
                    4. Análises Temporais:
                       - Evolução das vendas ao longo do tempo
                       - Sazonalidade nas vendas
                    
                    5. Análises Comparativas:
                       - Comparação entre regiões
                       - Comparação entre funções
                    
                    SEMPRE que possível:
                    1. Crie visualizações usando Plotly ou Matplotlib
                    2. Forneça insights sobre os dados
                    3. Sugira análises adicionais
                    4. Explique os resultados encontrados
                    
                    Quando o usuário pedir exemplos ou não especificar uma análise:
                    1. Mostre 3-5 exemplos de análises diferentes
                    2. Inclua visualizações para cada exemplo
                    3. Explique o que cada análise revela
                    4. Sugira análises complementares
                    
                    EXEMPLO DE CÓDIGO:
                    ```python
                    # Acessar um DataFrame específico
                    df_vendas = dataframes['vendas_estoque_por_mes_regiao.xlsx']
                    
                    # Verificar tipos de dados
                    print("Tipos de dados:")
                    print(df_vendas.dtypes)
                    
                    # Verificar primeiras linhas
                    print("\nPrimeiras linhas:")
                    print(df_vendas.head())
                    
                    # Converter colunas para o tipo correto se necessário
                    df_vendas['vendas'] = pd.to_numeric(df_vendas['vendas'], errors='coerce')
                    df_vendas['estoque'] = pd.to_numeric(df_vendas['estoque'], errors='coerce')
                    
                    # Criar um gráfico de barras
                    fig = px.bar(df_vendas, x='regiao', y='vendas', title='Vendas por Região')
                    ```"""},
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
                st.session_state['file_chat_history'].append({"role": "assistant", "content": assistant_response})
                
                # Exibir resposta
                with st.chat_message("assistant"):
                    st.write(assistant_response)
                
            except Exception as e:
                error_message = f"Erro ao processar a pergunta: {str(e)}"
                st.error(error_message)
                st.session_state['file_chat_history'].append({"role": "assistant", "content": error_message})

        # Interface de entrada de código
        if st.session_state.get('show_file_code_input', False):
            st.markdown("---")
            st.subheader("Interface de Entrada de Código")
            st.info("""
            **Dica:** Para exibir gráficos no Streamlit:
            1. Para Plotly: crie o objeto da figura (ex: `fig = px.scatter(...)`) e **não** use `fig.show()`
            2. Para Matplotlib: crie a figura (ex: `fig = plt.figure()`) e **não** use `plt.show()`
            Basta criar o objeto da figura e clicar em "Executar Código" para vê-lo na tela.
            
            **Acesso aos DataFrames:**
            - Use `st.session_state['dataframes']` para acessar todos os DataFrames carregados
            - Exemplo: `df = st.session_state['dataframes']['nome_do_arquivo']`
            """)
            
            # Campo de entrada de código
            code_input = st.text_area(
                "Digite seu código Python:",
                height=200,
                key="file_code_input_area"
            )
            
            col1, col2 = st.columns([1, 5])
            with col1:
                if st.button("Executar e Salvar", key="file_execute_code_button"):
                    if code_input:
                        try:
                            # Criar um namespace local para execução
                            local_vars = {
                                'st': st,
                                'pd': pd,
                                'np': np,
                                'px': px,
                                'plt': plt,
                                'go': go,
                                'dataframes': st.session_state['dataframes']
                            }
                            
                            try:
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
                                if 'file_added_codes' not in st.session_state:
                                    st.session_state['file_added_codes'] = []
                                st.session_state['file_added_codes'].append({
                                    'name': code_name,
                                    'code': code_input,
                                    'timestamp': current_time.strftime("%Y-%m-%d %H:%M:%S")
                                })
                                
                                st.success("Código executado e salvo com sucesso!")
                            except Exception as e:
                                st.error(f"Erro ao executar o código: {str(e)}")
                                st.info("""
                                Dicas para resolver o erro:
                                1. Verifique se as colunas que você está usando existem no DataFrame
                                2. Certifique-se de que está usando colunas numéricas para operações matemáticas
                                3. Use df.dtypes para verificar os tipos de dados das colunas
                                4. Use df.head() para visualizar os dados antes de fazer operações
                                """)
                        except Exception as e:
                            st.error(f"Erro ao executar o código: {str(e)}")
                    else:
                        st.error("Por favor, insira o código.")
            
            with col2:
                if st.button("Cancelar", key="file_cancel_code_button"):
                    st.session_state['show_file_code_input'] = False
                    st.experimental_rerun()

        # Container para códigos adicionados
        if st.session_state.get('file_added_codes', []):
            st.markdown("---")
            st.subheader("Códigos Salvos")
            
            for idx, code_item in enumerate(st.session_state['file_added_codes']):
                with st.expander(f"{code_item['name']} - {code_item['timestamp']}"):
                    st.code(code_item['code'], language='python')
                    
                    col1, col2 = st.columns([1, 5])
                    with col1:
                        if st.button("Executar", key=f"file_run_saved_{idx}"):
                            try:
                                # Criar um namespace local para execução
                                local_vars = {
                                    'st': st,
                                    'pd': pd,
                                    'np': np,
                                    'px': px,
                                    'plt': plt,
                                    'go': go,
                                    'dataframes': st.session_state['dataframes']
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
                                st.info("""
                                Dicas para resolver o erro:
                                1. Verifique se as colunas que você está usando existem no DataFrame
                                2. Certifique-se de que está usando colunas numéricas para operações matemáticas
                                3. Use df.dtypes para verificar os tipos de dados das colunas
                                4. Use df.head() para visualizar os dados antes de fazer operações
                                """)
                    
                    with col2:
                        if st.button("Remover", key=f"file_remove_{idx}"):
                            st.session_state['file_added_codes'].pop(idx)
                            st.experimental_rerun()

            # Container para visualizações
            with st.container():
                st.markdown("---")
                st.subheader("Visualizações")
                
                # Selecionar tipo de visualização
                viz_type = st.selectbox(
                    "Tipo de Visualização",
                    ["Gráfico de Barras", "Gráfico de Linha", "Gráfico de Dispersão", "Histograma", "Box Plot"]
                )
                
                # Selecionar colunas para visualização
                if df.select_dtypes(include=[np.number]).columns.any():
                    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                    x_col = st.selectbox("Coluna X", numeric_cols)
                    
                    if viz_type in ["Gráfico de Dispersão", "Box Plot"]:
                        y_col = st.selectbox("Coluna Y", numeric_cols)
                    
                    # Criar visualização
                    if viz_type == "Gráfico de Barras":
                        fig = px.bar(df, x=x_col, title=f"Gráfico de Barras - {x_col}")
                    elif viz_type == "Gráfico de Linha":
                        fig = px.line(df, x=x_col, title=f"Gráfico de Linha - {x_col}")
                    elif viz_type == "Gráfico de Dispersão":
                        fig = px.scatter(df, x=x_col, y=y_col, title=f"Gráfico de Dispersão - {x_col} vs {y_col}")
                    elif viz_type == "Histograma":
                        fig = px.histogram(df, x=x_col, title=f"Histograma - {x_col}")
                    elif viz_type == "Box Plot":
                        fig = px.box(df, x=x_col, y=y_col, title=f"Box Plot - {x_col} vs {y_col}")
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Não há colunas numéricas para visualização.") 