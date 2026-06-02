"""Diagnostico cru do Outlook COM. So usa win32com puro, sem nossas helpers."""
from __future__ import annotations

import sys
import traceback
from datetime import datetime, timedelta

import win32com.client


def main():
    print("Conectando...")
    outlook = win32com.client.Dispatch("Outlook.Application")
    ns = outlook.GetNamespace("MAPI")
    inbox = ns.GetDefaultFolder(6)
    print(f"Inbox: {inbox.Name}")

    # Localiza a subpasta
    pasta = None
    for sub in inbox.Folders:
        if "Laborat" in sub.Name:
            pasta = sub
            break
    if pasta is None:
        print("Pasta nao encontrada"); return
    print(f"Pasta: {pasta.Name} ({pasta.Items.Count} itens totais)")

    # Filtra ultimos 7 dias (janela pequena pra diagnostico)
    since = datetime.now() - timedelta(days=7)
    filtro = f"[ReceivedTime] >= '{since.strftime('%m/%d/%Y %I:%M %p')}'"
    print(f"\nFiltro: {filtro}")

    items = pasta.Items
    items.Sort("[ReceivedTime]", True)
    restricted = items.Restrict(filtro)
    print(f"Apos Restrict: {restricted.Count} itens")

    # Tenta ler propriedades 1 a 1 com GetFirst/GetNext
    print("\nIterando com GetFirst/GetNext:")
    item = restricted.GetFirst()
    idx = 0
    while item is not None and idx < 10:
        idx += 1
        try:
            subj = item.Subject
            received = item.ReceivedTime
            sender = item.SenderEmailAddress
            print(f"  [{idx}] {received} | {sender[:40] if sender else '(sem sender)'} | {subj[:80]}")
        except Exception as e:
            print(f"  [{idx}] ERRO ao ler propriedades: {type(e).__name__}: {e}")
            traceback.print_exc()
            break
        item = restricted.GetNext()

    print(f"\nTotal iterado com sucesso: {idx}")


if __name__ == "__main__":
    main()
