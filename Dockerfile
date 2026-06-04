# Imagem base oficial do Python
FROM python:3.11-slim

# Copia o binário do uv de sua imagem oficial para velocidade de build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos de especificação de dependências
COPY pyproject.toml uv.lock ./

# Instala as dependências do projeto de forma congelada e limpa
RUN uv sync --frozen --no-install-project --no-dev

# Copia o código-fonte e os diretórios de PDFs oficiais e ChromaDB indexado
COPY src/ ./src/
COPY data/corpus/ ./data/corpus/
COPY data/chroma/ ./data/chroma/

# Expõe a porta do Streamlit
EXPOSE 8501

# Configurações do Streamlit e Python para rodar dentro do container
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV PYTHONUNBUFFERED=1

# Executa o Streamlit dentro do ambiente virtual do uv
CMD ["uv", "run", "streamlit", "run", "src/ui/streamlit_app.py"]
