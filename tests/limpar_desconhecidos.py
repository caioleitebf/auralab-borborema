"""Limpa do banco amostras classificadas como DESCONHECIDO + logs relacionados
para que o coletor reprocesse com os tokens atualizados.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import get_conn

with get_conn() as conn:
    # Captura codigos DESCONHECIDO
    codigos = [r["codigo_amostra"] for r in conn.execute(
        "SELECT codigo_amostra FROM amostras WHERE processo='DESCONHECIDO'"
    ).fetchall()]
    print(f"Codigos DESCONHECIDO a remover: {len(codigos)}")

    # Captura entry_ids dos logs desses codigos (e dos sem codigo que falharam)
    entry_ids = [r["entry_id_outlook"] for r in conn.execute(
        "SELECT DISTINCT entry_id_outlook FROM processamento_log "
        "WHERE codigo_amostra IN ({})".format(",".join("?" * len(codigos))),
        codigos
    ).fetchall() if codigos] if codigos else []
    print(f"Entry IDs no log: {len(entry_ids)}")

    if codigos:
        placeholders = ",".join("?" * len(codigos))
        n_res = conn.execute(
            f"DELETE FROM resultados WHERE codigo_amostra IN ({placeholders})",
            codigos
        ).rowcount
        n_amo = conn.execute(
            f"DELETE FROM amostras WHERE codigo_amostra IN ({placeholders})",
            codigos
        ).rowcount
        n_log = conn.execute(
            f"DELETE FROM processamento_log WHERE codigo_amostra IN ({placeholders})",
            codigos
        ).rowcount
        print(f"Removidos: {n_res} resultados, {n_amo} amostras, {n_log} logs")
    else:
        print("Nada para remover.")
