FROM python:3.11-slim-bookworm

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV STREAMLIT_SERVER_PORT=8501

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/* && \
    python -m venv $VIRTUAL_ENV

WORKDIR /app
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE $STREAMLIT_SERVER_PORT

CMD ["streamlit", "run", "app.py"]