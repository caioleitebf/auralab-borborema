"""Inspeciona o estado atual do banco."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import get_conn, estatisticas


def main():
    stats = estatisticas()
    print(f"Total de amostras: {stats['total_amostras']}")
    print(f"  - Preliminar: {stats['preliminares']}")
    print(f"  - Final:      {stats['finais']}")
    print()
    print("Distribuicao por processo:")
    for p, n in sorted(stats['por_processo'].items()):
        print(f"  {p:18s} : {n}")
    print()

    with get_conn() as conn:
        # Por processo + status
        print("Detalhe (processo x subcategoria x status):")
        rows = conn.execute("""
            SELECT processo, subcategoria, status, COUNT(*) as n
            FROM amostras GROUP BY processo, subcategoria, status
            ORDER BY processo, subcategoria, status
        """).fetchall()
        for r in rows:
            print(f"  {r['processo']:14s} / {(r['subcategoria'] or '-'):14s} / {r['status']:12s} : {r['n']}")
        print()

        # Bateladas com Preliminar vs Final
        print("Bateladas com PM duplicado:")
        rows = conn.execute("""
            SELECT batelada, processo, COUNT(DISTINCT codigo_amostra) as n_pms
            FROM amostras
            WHERE batelada IS NOT NULL
            GROUP BY batelada, processo
            HAVING n_pms > 1
            ORDER BY batelada DESC LIMIT 10
        """).fetchall()
        for r in rows:
            print(f"  {r['batelada']:10s} ({r['processo']}) -> {r['n_pms']} PMs distintos")
        print()

        # Recentes
        print("5 amostras mais recentes:")
        rows = conn.execute("""
            SELECT codigo_amostra, processo, subcategoria, status, batelada,
                   data_amostra, data_recebimento_email,
                   (SELECT COUNT(*) FROM resultados r WHERE r.codigo_amostra = a.codigo_amostra) as n_resultados
            FROM amostras a
            ORDER BY data_recebimento_email DESC LIMIT 5
        """).fetchall()
        for r in rows:
            print(f"  {r['codigo_amostra']} | {r['processo']:12s} | {r['subcategoria'] or '-':12s} | "
                  f"{r['status']:12s} | bat={r['batelada'] or '-':8s} | "
                  f"data={r['data_amostra']} | resultados={r['n_resultados']}")
        print()

        # Status do processamento_log
        print("Distribuicao do processamento_log:")
        rows = conn.execute(
            "SELECT status, COUNT(*) FROM processamento_log GROUP BY status"
        ).fetchall()
        for r in rows:
            print(f"  {r[0]:30s} : {r[1]}")


if __name__ == "__main__":
    main()
