# exportar_parquet.py
import pandas as pd
from sqlalchemy import create_engine
import pg8000

# 🔧 Configurações de conexão
usuario = "powerbi"
senha = "3bJY9iAq"
host = "34.134.35.236"
banco = "Darwin"

# 🌐 String de conexão
engine = create_engine(f"postgresql+pg8000://{usuario}:{senha}@{host}:5432/{banco}")

# 📥 Consulta à view
query = """
SELECT nome_parceiro, data_competencia, status_titulo, banco, valor
FROM vw_efetividade
"""

# 📦 Carrega e salva
df = pd.read_sql(query, engine)
df.to_parquet("vw_efetividade.parquet", index=False)

print("✅ Arquivo Parquet exportado com sucesso!")