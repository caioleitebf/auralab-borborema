"""Teste read-only do OutlookDesktopSource.

Lista pastas disponiveis, conta emails na pasta-alvo e mostra amostra
dos 5 mais recentes. Nao grava nada -- so leitura.
"""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.email_reader import OutlookDesktopSource
from app.subject_parser import parse_subject
from app.config import PASTA_LABORATORIO, INBOX_PRINCIPAL, DOMINIOS_LAB


def listar_pastas_inbox():
    """Mostra pastas disponiveis para confirmar nome correto."""
    import win32com.client
    outlook = win32com.client.Dispatch("Outlook.Application")
    ns = outlook.GetNamespace("MAPI")
    inbox = ns.GetDefaultFolder(6)  # 6 = Inbox
    print(f"Inbox principal: {inbox.Name!r}")
    print("Subpastas da Inbox:")
    try:
        for sub in inbox.Folders:
            try:
                print(f"  - {sub.Name!r}  ({sub.Items.Count} itens)")
            except Exception as e:
                print(f"  - {sub.Name!r}  (erro ao contar: {e})")
    except Exception as e:
        print(f"  Erro ao iterar: {e}")
    print()


def contar_emails_pasta(nome_pasta: str):
    """Conta emails e mostra 5 mais recentes do dominio do lab."""
    src = OutlookDesktopSource(pastas=[nome_pasta])
    print(f"=== Testando leitura da pasta: {nome_pasta!r} ===")
    print(f"Dominios aceitos: {DOMINIOS_LAB}")
    print()

    # Janela curta para nao saturar memoria do Outlook
    since = datetime.now() - timedelta(days=7)
    print(f"Janela: ultimos 7 dias (since {since:%Y-%m-%d})")
    print()

    from collections import Counter
    encontrados = []
    falhas = []
    distribuicao = Counter()
    sub_distribuicao = Counter()
    operadores = Counter()
    for msg in src.fetch_unprocessed(since=since):
        encontrados.append(msg)
        info = parse_subject(msg.subject)
        operadores[msg.sender_email] += 1
        if info:
            distribuicao[(info.processo, info.tipo)] += 1
            sub_distribuicao[(info.processo, info.subcategoria or '-')] += 1
        else:
            falhas.append(msg)

    parseados_ok = len(encontrados) - len(falhas)
    print(f"TOTAL elegiveis: {len(encontrados)} | parse OK: {parseados_ok} | parse falha: {len(falhas)}")
    print()
    print("=== Distribuicao por processo + tipo ===")
    for (proc, tipo), n in sorted(distribuicao.items()):
        print(f"  {proc:18s} {tipo:12s} : {n}")
    print()
    print("=== Subcategorias (vazio = NAO classificou) ===")
    for (proc, sub), n in sorted(sub_distribuicao.items()):
        print(f"  {proc:18s} -> {sub:20s} : {n}")
    print()
    print("=== Remetentes ===")
    for sender, n in sorted(operadores.items(), key=lambda x: -x[1]):
        print(f"  {sender:50s} : {n}")
    print()
    if falhas:
        print(f"=== ASSUNTOS QUE FALHARAM PARSE ({len(falhas)}) ===")
        for m in falhas:
            print(f"  [{m.received_at:%Y-%m-%d %H:%M}] {m.subject!r}")
        print()

    # Mostra assuntos classificados como DESCONHECIDO
    desconhecidos = []
    for msg in encontrados:
        info = parse_subject(msg.subject)
        if info and info.processo == "DESCONHECIDO":
            desconhecidos.append((msg, info))
    if desconhecidos:
        print(f"=== ASSUNTOS CLASSIFICADOS COMO 'DESCONHECIDO' ({len(desconhecidos)}) ===")
        for m, info in desconhecidos:
            print(f"  [{m.received_at:%m-%d %H:%M}] [{info.codigo}] {m.subject!r}")
        print()


if __name__ == "__main__":
    print("="*70)
    print("DRY RUN -- Coletor de emails")
    print("="*70)
    print()
    try:
        listar_pastas_inbox()
    except Exception as e:
        print(f"ERRO conectando ao Outlook: {e}")
        print("Verifique se o Outlook esta aberto e logado.")
        sys.exit(1)

    contar_emails_pasta(PASTA_LABORATORIO)
