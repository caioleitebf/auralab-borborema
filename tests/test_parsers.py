"""Testa os parsers contra os XLS baixados em anexos/_amostras_inspecao."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import parsers
from app.subject_parser import parse_subject
from app.config import ROOT


CASOS = [
    # (arquivo, assunto que veio com ele)
    (
        "ACACIA_PM2602477.XLS",
        "[External]Envio de Resultado Analitico PM2602477 SOL.RICA.ACACIA",
    ),
    (
        "ELETROLISE_PM2602474.XLS",
        "[External]Envio de Resultado Analitico PM2602474 LICOR-CE001 BAT-385",
    ),
    (
        "LIXIVIACAO_PM2602468.XLS",
        "[External]Envio de Resultado Analitico PM2602468 Rej./Alim.",
    ),
]


def main():
    amostras = ROOT / "anexos" / "_amostras_inspecao"
    for nome, assunto in CASOS:
        path = amostras / nome
        info = parse_subject(assunto)
        if not info:
            print(f"!! parse_subject falhou: {assunto}")
            continue

        print("=" * 78)
        print(f"ARQUIVO: {nome}")
        print(f"ASSUNTO: {assunto}")
        print(f"INFO:    {info.codigo} | {info.processo}/{info.subcategoria or '-'} | tipo={info.tipo} | bat={info.batelada} turno={info.turno}")
        print("=" * 78)

        anexo = parsers.parse(path, info)
        print(f"Processo: {anexo.processo} / {anexo.subcategoria or '-'}")
        print(f"Batelada: {anexo.batelada} | Turno: {anexo.turno}")
        print(f"Data amostra: {anexo.data_amostra}")
        print(f"Date received: {anexo.data_recebimento_lab}")
        print(f"Date finalized: {anexo.data_finalizacao_lab}")
        print(f"PO Number: {anexo.po_number}")
        print(f"Metodos: {anexo.metodos}")
        print(f"Total de resultados extraidos: {len(anexo.resultados)}")

        # Mostra primeiros 12 nao-NA
        validos = [r for r in anexo.resultados if r.valor is not None]
        print(f"  -> {len(validos)} com valor numerico, {len(anexo.resultados) - len(validos)} NA/vazio")
        print()
        print("Primeiros resultados com valor:")
        for r in validos[:12]:
            unit = f" {r.unidade}" if r.unidade else ""
            print(f"  - {r.raw_label:50s} = {r.valor}{unit} ({r.elemento}/{r.metodo})")
        if len(validos) > 12:
            print(f"  ... (+ {len(validos) - 12} resultados)")
        print()


if __name__ == "__main__":
    main()
