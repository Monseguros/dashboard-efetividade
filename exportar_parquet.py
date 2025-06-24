# exportar_parquet.py
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

print(
  host= os.getenv("DB_HOST"),
  database=os.getenv("DB_NAME"),
  user=os.getenv("DB_USER"),
  password=os.getenv("DB_PASS"),
  port=os.getenv("DB_PORT")
)
# 🔧 Configurações de conexão
host= os.getenv("DB_HOST"),
database=os.getenv("DB_NAME"),
user=os.getenv("DB_USER"),
password=os.getenv("DB_PASS"),
port=os.getenv("DB_PORT")

# 🌐 String de conexão
engine = create_engine(f"postgresql://{user}:{password}@{host}:5432/{database}")

# 📥 Consulta à view
query = """
SELECT nome_parceiro, data_competencia, status_titulo, banco, valor
FROM vw_efetividade
"""

# 📦 Carrega e salva
df = pd.read_sql(query, engine)
df.to_parquet("vw_efetividade.parquet", index=False)

print("✅ Arquivo Parquet exportado com sucesso!")