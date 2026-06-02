"""Mostra a ultima data de amostra por processo."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import get_conn

with get_conn() as conn:
    print(f"{'PROCESSO':<18} {'ULTIMA AMOSTRA':<14} {'ULTIMO RECEBIDO':<22} {'TOTAL'}")
    print("-" * 70)
    rows = conn.execute("""
        SELECT processo,
               MAX(date(data_amostra)) AS ultima,
               MAX(data_recebimento_email) AS recebido,
               COUNT(*) AS total
        FROM amostras
        WHERE processo != 'DESCONHECIDO'
        GROUP BY processo
        ORDER BY ultima DESC
    """).fetchall()
    for r in rows:
        print(f"  {r['processo']:<16} {r['ultima']:<14} {r['recebido'] or '':<22} {r['total']}")
