"""Verifica por que so aparece 1o turno do 26/05/2026 na tabela."""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import get_conn

regex_hora = re.compile(r"(?<!\d)(\d{1,2}):(\d{2})(?!\d)")

with get_conn() as conn:
    # Todos os PMs de Lixiviacao com data_amostra 26/05/2026
    print("=== Amostras de Lixiviacao com data_amostra em 25-27/05 ===")
    rows = conn.execute("""
        SELECT codigo_amostra, data_amostra, status, data_recebimento_lab,
               assunto_original
        FROM amostras
        WHERE processo='LIXIVIACAO'
          AND date(data_amostra) BETWEEN '2026-05-25' AND '2026-05-27'
        ORDER BY data_amostra DESC, data_recebimento_lab DESC
    """).fetchall()
    for r in rows:
        print(f"  {r['data_amostra']} {r['codigo_amostra']:12s} status={r['status']:11s} recv={r['data_recebimento_lab']!s:25s}")
        print(f"      Assunto: {r['assunto_original']}")

    print()
    print("=== Resultados desses PMs (com hora extraida) ===")
    for r in rows:
        cod = r["codigo_amostra"]
        res = conn.execute("""
            SELECT raw_label, valor, unidade FROM resultados
            WHERE codigo_amostra = ? AND valor IS NOT NULL LIMIT 8
        """, (cod,)).fetchall()
        print(f"  PM {cod}:")
        for x in res:
            m = regex_hora.search(x["raw_label"])
            hora = m.group(1) if m else "?"
            print(f"    {x['raw_label']:50s} val={x['valor']:8.3f} hora={hora}")
