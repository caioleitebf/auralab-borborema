"""Inspeciona estrutura interna do XLS de Tanques e Bullion."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import xlrd
from app.database import get_conn


def inspecionar(xls_path: Path, titulo: str):
    print(f"\n{'='*80}\n{titulo} -- {xls_path.name}\n{'='*80}")
    if not xls_path.exists():
        print(f"NAO ENCONTRADO: {xls_path}")
        return
    book = xlrd.open_workbook(str(xls_path))
    for sname in book.sheet_names():
        sheet = book.sheet_by_name(sname)
        print(f"\nSheet: {sname!r} ({sheet.nrows} linhas x {sheet.ncols} colunas)")
        for r in range(sheet.nrows):
            cells = []
            for c in range(sheet.ncols):
                v = sheet.cell_value(r, c)
                if v == "":
                    cells.append("")
                elif isinstance(v, float):
                    if v == int(v):
                        cells.append(str(int(v)))
                    else:
                        cells.append(f"{v:.4f}")
                else:
                    cells.append(str(v)[:30])
            if any(c.strip() for c in cells):
                print(f"  R{r:02d}: {cells}")


def main():
    with get_conn() as conn:
        # 1 PM de Tanques recente
        r1 = conn.execute("""
            SELECT arquivo_xls_path FROM amostras WHERE processo='TANQUES'
            ORDER BY data_recebimento_email DESC LIMIT 1
        """).fetchone()
        # 1 EC de Bullion
        r2 = conn.execute("""
            SELECT arquivo_xls_path FROM amostras WHERE processo='BULLION'
            ORDER BY data_recebimento_email DESC LIMIT 1
        """).fetchone()

    if r1:
        inspecionar(Path(r1["arquivo_xls_path"]), "TANQUES")
    if r2:
        inspecionar(Path(r2["arquivo_xls_path"]), "BULLION")


if __name__ == "__main__":
    main()
