FROM python:3.11-slim-bookworm

# Configuração do virtualenv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV STREAMLIT_SERVER_PORT=8501

# Instalação de dependências do sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libffi-dev \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && python -m venv $VIRTUAL_ENV

# Define diretório de trabalho
WORKDIR /app

# Copia apenas requirements para cache de layer
COPY requirements.txt .

# Instalação de pacotes Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia o restante da aplicação
COPY . .

# Expõe porta do streamlit
EXPOSE $STREAMLIT_SERVER_PORT

# Comando para rodar o app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
