"""Inspeciona a estrutura dos arquivos XLS baixados."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import xlrd
from app.config import ROOT


def inspecionar(xls_path: Path):
    print("=" * 80)
    print(f"ARQUIVO: {xls_path.name}")
    print("=" * 80)
    try:
        book = xlrd.open_workbook(str(xls_path))
    except Exception as e:
        print(f"ERRO ao abrir: {e}")
        return

    print(f"Sheets: {book.sheet_names()}")
    for sname in book.sheet_names():
        sheet = book.sheet_by_name(sname)
        print(f"\n--- Sheet: {sname!r} ({sheet.nrows} linhas x {sheet.ncols} colunas) ---")
        # Mostra primeiras 40 linhas com indices de coluna
        max_rows = min(sheet.nrows, 40)
        for r in range(max_rows):
            cells = []
            for c in range(sheet.ncols):
                val = sheet.cell_value(r, c)
                ctype = sheet.cell_type(r, c)
                if val == "" and ctype == 0:
                    cells.append("")
                elif isinstance(val, float):
                    cells.append(f"{val:.4f}" if val != int(val) else f"{int(val)}")
                else:
                    s = str(val)
                    cells.append(s[:30] + "..." if len(s) > 30 else s)
            # so mostra linhas com pelo menos 1 celula nao vazia
            if any(c.strip() for c in cells):
                print(f"  R{r:02d}: {cells}")
        if sheet.nrows > max_rows:
            print(f"  ... (+ {sheet.nrows - max_rows} linhas)")


def main():
    amostras = ROOT / "anexos" / "_amostras_inspecao"
    for xls in sorted(amostras.glob("*.XLS")):
        inspecionar(xls)
        print()


if __name__ == "__main__":
    main()
