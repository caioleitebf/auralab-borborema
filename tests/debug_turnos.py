"""Verifica se ha amostras de Lixiviacao com hora 00-07 (1o turno) no banco."""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import get_conn

regex_hora = re.compile(r"(?<!\d)(\d{1,2}):(\d{2})(?!\d)")

with get_conn() as conn:
    rows = conn.execute("""
        SELECT a.codigo_amostra, a.data_amostra, r.raw_label, r.valor
        FROM amostras a JOIN resultados r ON r.codigo_amostra=a.codigo_amostra
        WHERE a.processo='LIXIVIACAO' AND r.valor IS NOT NULL
        ORDER BY a.data_amostra DESC
    """).fetchall()
    print(f"Total resultados Lixiviacao: {len(rows)}")
    print()
    horas = {}
    primeiro_turno_labels = []
    for r in rows:
        m = regex_hora.search(r["raw_label"])
        if m:
            hh = int(m.group(1))
            horas[hh] = horas.get(hh, 0) + 1
            if 0 <= hh < 8:
                primeiro_turno_labels.append((r["data_amostra"], r["codigo_amostra"], r["raw_label"], r["valor"]))
    print("Distribuicao por hora:")
    for h in sorted(horas):
        turno = "1o" if h < 8 else "2o" if h < 16 else "3o"
        print(f"  {h:02d}h ({turno}): {horas[h]}")
    print()
    print(f"Labels com hora 00-07h (1o turno): {len(primeiro_turno_labels)}")
    for d, c, l, v in primeiro_turno_labels[:10]:
        print(f"  {d} {c} {l} = {v}")
