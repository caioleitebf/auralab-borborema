"""Debug: ve por que Bullion sem Au/Ag e Agua de Processo vazia."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import get_conn

with get_conn() as conn:
    print("=== Bullion EC2600032 resultados ===")
    for r in conn.execute("""
        SELECT raw_label, valor, elemento, unidade, metodo
        FROM resultados WHERE codigo_amostra='EC2600032' LIMIT 12
    """).fetchall():
        print(f"  {r['raw_label']:15s} val={r['valor']!s:10s} elem={r['elemento']!s:8s} unid={r['unidade']!s:8s} met={r['metodo']!s}")

    print()
    print("=== Agua de Processo amostras ===")
    for r in conn.execute("""
        SELECT codigo_amostra, data_amostra, processo, status, batelada
        FROM amostras WHERE processo='AGUA_PROCESSO' LIMIT 10
    """).fetchall():
        print(f"  {r['codigo_amostra']} data={r['data_amostra']} status={r['status']}")

    print()
    print("=== Agua resultados (1 PM exemplo) ===")
    for r in conn.execute("""
        SELECT a.codigo_amostra, a.data_amostra, r.raw_label, r.valor
        FROM amostras a JOIN resultados r ON r.codigo_amostra=a.codigo_amostra
        WHERE a.processo='AGUA_PROCESSO' AND r.valor IS NOT NULL LIMIT 8
    """).fetchall():
        print(f"  {r['codigo_amostra']} data={r['data_amostra']} lbl={r['raw_label']} val={r['valor']}")
