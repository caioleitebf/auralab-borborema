"""Testes do subject_parser com casos reais coletados do Outlook do Caio."""
from __future__ import annotations

import sys
from pathlib import Path

# Garante que conseguimos importar 'app' rodando direto via python.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.subject_parser import parse_subject


CASOS = [
    # (assunto, codigo esperado, processo esperado, tipo, subcategoria, batelada, turno)
    (
        "[External]Envio de Resultado Analitico - PM2602458 - Sol. Rica Acacia - BAT-386",
        "PM2602458", "ACACIA", "Analitico", "Sol. Rica", "BAT-386", None,
    ),
    (
        "[External]Envio de Resultado Analitico - PM2602455 - Over Acacia BAT-386",
        "PM2602455", "ACACIA", "Analitico", "Over", "BAT-386", None,
    ),
    (
        "[External]Envio de Resultado Preliminar - PM2602455 - Over Acacia BAT-386",
        "PM2602455", "ACACIA", "Preliminar", "Over", "BAT-386", None,
    ),
    (
        "[External]Envio de Resultado Analitico PM2602438 LICOR-CE001 BAT-384",
        "PM2602438", "ELETROLISE", "Analitico", "CE0001", "BAT-384", None,
    ),
    (
        "[External]Envio de Resultado Analitico- PM2602453- Licor CE002 BAT 472",
        "PM2602453", "ELETROLISE", "Analitico", "CE0002", "BAT-472", None,
    ),
    (
        "[External]Envio de Resultado Analitico - PM2602445 - Rej./Alim 21/05 - TURNO: T2",
        "PM2602445", "LIXIVIACAO", "Analitico", None, None, "T2",
    ),
    (
        "[External]Envio de Resultado Analitico - PM2602437 - Agua de Processo 21/05",
        "PM2602437", "AGUA_PROCESSO", "Analitico", None, None, None,
    ),
    (
        "[External]Envio de Resultado Analitico PM2602443 TQS.DIARIO 08:00",
        "PM2602443", "TANQUES", "Analitico", None, None, None,
    ),
    (
        "[External]Envio de Resultado Analitico - EC2600031 - BULLION 15/05/2026",
        "EC2600031", "BULLION", "Analitico", None, None, None,
    ),
    (
        "[External]Envio de Resultado Analitico PM2602442 CARVAO ELUICAO",
        "PM2602442", "ELUICAO", "Analitico", None, None, None,
    ),
    (
        "[External]Envio de Resultado Analitico - AB2600019 - DETOX - Cianeto WAD",
        "AB2600019", "DETOX", "Analitico", "Cianeto WAD", None, None,
    ),
    (
        "[External]Re: Envio de Resultado Analitico - AB2600017 - DETOX - CIANETO WAD",
        "AB2600017", "DETOX", "Analitico", "Cianeto WAD", None, None,
    ),
    (
        "[External]Envio de Resultado Analitico - AB2600016 CIANETO WAD",
        "AB2600016", "DETOX", "Analitico", "Cianeto WAD", None, None,
    ),
]


def run():
    ok, fail = 0, 0
    for caso in CASOS:
        subj, exp_codigo, exp_proc, exp_tipo, exp_sub, exp_bat, exp_turno = caso
        info = parse_subject(subj)
        if info is None:
            print(f"FALHA (parse None): {subj}")
            fail += 1
            continue

        problemas = []
        if info.codigo != exp_codigo:
            problemas.append(f"codigo {info.codigo} != {exp_codigo}")
        if info.processo != exp_proc:
            problemas.append(f"processo {info.processo} != {exp_proc}")
        if info.tipo != exp_tipo:
            problemas.append(f"tipo {info.tipo} != {exp_tipo}")
        if info.subcategoria != exp_sub:
            problemas.append(f"subcategoria {info.subcategoria!r} != {exp_sub!r}")
        if info.batelada != exp_bat:
            problemas.append(f"batelada {info.batelada} != {exp_bat}")
        if info.turno != exp_turno:
            problemas.append(f"turno {info.turno} != {exp_turno}")

        if problemas:
            print(f"FALHA: {subj}")
            for p in problemas:
                print(f"   - {p}")
            fail += 1
        else:
            ok += 1
            print(f"OK: {info.codigo} -> {info.processo}/{info.subcategoria or '-'} ({info.tipo}, bat={info.batelada}, turno={info.turno})")

    print(f"\n{'='*60}\nResultado: {ok} OK, {fail} FALHAS de {len(CASOS)}\n{'='*60}")
    return fail == 0


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
