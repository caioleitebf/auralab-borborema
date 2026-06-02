"""Baixa 1 anexo .XLS de cada processo prioritario (analitico, recente).

Salva em anexos/_amostras_inspecao/ para inspecao da estrutura do Excel.
"""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.email_reader import OutlookDesktopSource
from app.subject_parser import parse_subject
from app.config import PASTA_LABORATORIO, ROOT


PROCESSOS_ALVO = ("LIXIVIACAO", "ACACIA", "ELETROLISE")


def main():
    out_dir = ROOT / "anexos" / "_amostras_inspecao"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Salvando amostras em: {out_dir}\n")

    src = OutlookDesktopSource(pastas=[PASTA_LABORATORIO])
    since = datetime.now() - timedelta(days=7)
    print(f"Janela: ultimos 7 dias\n")

    coletados: dict[str, dict] = {}

    for msg in src.fetch_unprocessed(since=since):
        info = parse_subject(msg.subject)
        if not info:
            continue
        if info.tipo != "Analitico":
            continue
        if info.processo not in PROCESSOS_ALVO:
            continue
        # Pega o primeiro de cada processo (mais recente, ja que esta ordenado desc)
        if info.processo in coletados:
            continue

        # Procura anexo XLS
        anexo_xls = None
        for att in msg.attachments:
            if att.filename.lower().endswith(('.xls', '.xlsx')):
                anexo_xls = att
                break
        if anexo_xls is None:
            print(f"  Sem XLS: {info.codigo}")
            continue

        # Nome amigavel: PROCESSO_CODIGO.xls
        ext = Path(anexo_xls.filename).suffix
        destino = out_dir / f"{info.processo}_{info.codigo}{ext}"
        anexo_xls.save_to(destino)

        coletados[info.processo] = {
            "codigo": info.codigo,
            "assunto": msg.subject,
            "subcategoria": info.subcategoria,
            "batelada": info.batelada,
            "turno": info.turno,
            "data_amostra": info.data_amostra_assunto,
            "arquivo": destino,
            "tamanho": destino.stat().st_size,
        }
        print(f"  OK: [{info.processo}] {info.codigo} ({info.subcategoria or '-'}) -> {destino.name} ({destino.stat().st_size} bytes)")

        if len(coletados) == len(PROCESSOS_ALVO):
            print("\nAmostras de todos os processos prioritarios coletadas.")
            break

    print(f"\nTotal coletado: {len(coletados)}/{len(PROCESSOS_ALVO)} processos")
    for proc in PROCESSOS_ALVO:
        if proc not in coletados:
            print(f"  AVISO: nao coletei amostra de {proc}")


if __name__ == "__main__":
    main()
