"""Inspeciona os raw_label dos novos processos para entender padroes."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import get_conn


PROCESSOS = ["TANQUES", "ELUICAO", "AGUA_PROCESSO", "DETOX", "BULLION"]


def main():
    with get_conn() as conn:
        for proc in PROCESSOS:
            print(f"\n{'='*80}")
            print(f"  {proc}")
            print('='*80)
            # Pega 1 PM com mais resultados e mostra labels
            row = conn.execute("""
                SELECT codigo_amostra, subcategoria, batelada FROM amostras
                WHERE processo = ?
                ORDER BY (SELECT COUNT(*) FROM resultados r WHERE r.codigo_amostra = amostras.codigo_amostra) DESC
                LIMIT 1
            """, (proc,)).fetchone()
            if not row:
                print("  (sem amostras)")
                continue
            print(f"  Amostra exemplo: {row['codigo_amostra']} (sub={row['subcategoria']}, bat={row['batelada']})")
            labels = conn.execute("""
                SELECT raw_label, valor, unidade, elemento, metodo
                FROM resultados WHERE codigo_amostra = ?
                ORDER BY id LIMIT 30
            """, (row["codigo_amostra"],)).fetchall()
            for l in labels:
                v = f"{l['valor']:.3f}" if l['valor'] is not None else "NA"
                print(f"    {l['raw_label']:60s} = {v:>8} {l['unidade'] or '':6s} ({l['elemento']}/{l['metodo']})")

            # Lista subcategorias do processo
            subs = conn.execute("""
                SELECT subcategoria, COUNT(*) FROM amostras WHERE processo = ?
                GROUP BY subcategoria
            """, (proc,)).fetchall()
            print(f"  Subcategorias: {dict(subs)}")


if __name__ == "__main__":
    main()
