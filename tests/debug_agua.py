import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import date
import pandas as pd
from app.database import get_conn

with get_conn() as conn:
    df = pd.read_sql_query("""
        SELECT a.codigo_amostra, a.data_amostra, r.raw_label, r.valor, r.unidade
        FROM amostras a
        JOIN resultados r ON r.codigo_amostra = a.codigo_amostra
        WHERE a.processo = 'AGUA_PROCESSO'
          AND date(a.data_amostra) BETWEEN ? AND ?
          AND r.valor IS NOT NULL
    """, conn, params=("2026-05-18", "2026-05-25"))
print(f"shape: {df.shape}")
print(df.head(15).to_string() if not df.empty else "EMPTY")

print()
print("SQL sem filtro de data:")
with get_conn() as conn:
    df2 = pd.read_sql_query("""
        SELECT a.codigo_amostra, a.data_amostra, r.raw_label, r.valor
        FROM amostras a
        JOIN resultados r ON r.codigo_amostra = a.codigo_amostra
        WHERE a.processo = 'AGUA_PROCESSO' AND r.valor IS NOT NULL
        LIMIT 5
    """, conn)
print(df2.to_string())
print(f"dtype data_amostra: {df2['data_amostra'].dtype if not df2.empty else 'N/A'}")
