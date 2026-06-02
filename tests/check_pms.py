"""Confere PMs 2602544 e 2602547 no banco."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.database import get_conn

with get_conn() as conn:
    print("=== Amostras ===")
    for cod in ("PM2602544", "PM2602547"):
        rows = conn.execute(
            "SELECT codigo_amostra, processo, subcategoria, status, data_amostra, assunto_original FROM amostras WHERE codigo_amostra=?",
            (cod,)
        ).fetchall()
        for r in rows:
            print(f"  {r['codigo_amostra']} | {r['processo']}/{r['subcategoria']} | {r['status']} | {r['data_amostra']}")
            print(f"    Assunto: {r['assunto_original']}")
        if not rows:
            print(f"  {cod}: NAO ESTA NO BANCO")

    print()
    print("=== Logs ===")
    for cod in ("PM2602544", "PM2602547"):
        rows = conn.execute(
            "SELECT status, email_subject, erro_detalhe FROM processamento_log WHERE codigo_amostra=? LIMIT 5",
            (cod,)
        ).fetchall()
        for r in rows:
            print(f"  {cod}: log status={r['status']} subj={r['email_subject']}")
            if r['erro_detalhe']:
                print(f"    erro: {r['erro_detalhe']}")
        if not rows:
            print(f"  {cod}: SEM LOG")
