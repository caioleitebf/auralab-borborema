"""Coletor principal -- orquestra email -> parser -> banco -> backup.

Como rodar:
    python -m app.collector --since-days 7
    python -m app.collector --since 2026-01-01   # backlog

O coletor:
1. Conecta ao Outlook desktop
2. Le emails da pasta `Resultados_Laboratorio` + Inbox (para Bullion)
3. Para cada email do dominio do lab:
   a. Verifica se ja foi processado (entry_id)
   b. Parseia assunto -> SubjectInfo
   c. Salva anexo XLS em anexos/<ano>/<mes>/
   d. Parseia XLS -> AnexoParseado
   e. Faz upsert na tabela amostras + substitui resultados
4. Registra cada email no processamento_log (sucesso ou erro)
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

from loguru import logger

from . import parsers
from .config import (
    ANEXOS_DIR, BACKLOG_INICIO, DOMINIOS_LAB,
    INBOX_PRINCIPAL, LOGS_DIR, PASTA_LABORATORIO, PROCESSOS_FASE1,
)
from .database import (
    entry_ids_processados, init_db, registrar_log, upsert_amostra, set_estado,
)
from .email_reader import EmailMessage, OutlookDesktopSource
from .subject_parser import SubjectInfo, parse_subject


def _setup_logging():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / f"coletor_{datetime.now():%Y-%m-%d}.log"
    logger.remove()
    logger.add(sys.stderr, level="INFO",
               format="<green>{time:HH:mm:ss}</green> | <level>{level:<7}</level> | {message}")
    logger.add(str(log_file), level="DEBUG", rotation="10 MB", retention="12 months",
               encoding="utf-8")


def _anexo_xls(msg: EmailMessage):
    """Retorna o primeiro anexo .XLS/.XLSX, ou None."""
    for att in msg.attachments:
        if att.filename.lower().endswith(('.xls', '.xlsx')):
            return att
    return None


def _path_destino_anexo(codigo: str, data: datetime | None, filename_original: str) -> Path:
    """Define onde salvar o anexo no backup."""
    if data is None:
        data = datetime.now()
    ano = data.strftime("%Y")
    mes = data.strftime("%m")
    pasta = ANEXOS_DIR / ano / mes
    pasta.mkdir(parents=True, exist_ok=True)
    ext = Path(filename_original).suffix or ".xls"
    return pasta / f"{codigo}{ext}"


def _path_destino_pdf(codigo: str, data: datetime | None) -> Path:
    if data is None:
        data = datetime.now()
    pasta = ANEXOS_DIR / data.strftime("%Y") / data.strftime("%m")
    return pasta / f"{codigo}.pdf"


def processar_email(msg: EmailMessage, somente_processos: set[str] | None = None) -> str:
    """Processa 1 email.

    Returns: status final ('ok' | 'ignorado_*' | 'erro').
    """
    # 1) Validar dominio
    if not any(msg.sender_email.lower().endswith(d) for d in DOMINIOS_LAB):
        registrar_log(msg.subject, msg.received_at, msg.sender_email,
                      "ignorado_dominio", msg.entry_id)
        return "ignorado_dominio"

    # 2) Parse do assunto
    info: SubjectInfo | None = parse_subject(msg.subject)
    if info is None:
        registrar_log(msg.subject, msg.received_at, msg.sender_email,
                      "erro", msg.entry_id,
                      erro="parse_subject retornou None")
        return "erro"

    # 3) Filtro por processo (Fase 1: so 3 processos)
    if somente_processos and info.processo not in somente_processos:
        registrar_log(msg.subject, msg.received_at, msg.sender_email,
                      "ignorado_processo_fora_fase", msg.entry_id,
                      codigo_amostra=info.codigo)
        return "ignorado_processo_fora_fase"

    # 4) Ignora replies (Re:) se duplicata
    if info.is_reply:
        logger.info(f"[{info.codigo}] Email com Re: ignorado (provavel duplicata)")
        registrar_log(msg.subject, msg.received_at, msg.sender_email,
                      "ignorado_duplicata", msg.entry_id, codigo_amostra=info.codigo)
        return "ignorado_duplicata"

    # 5) Encontra anexo XLS
    anexo_xls = _anexo_xls(msg)
    if anexo_xls is None:
        registrar_log(msg.subject, msg.received_at, msg.sender_email,
                      "ignorado_sem_anexo", msg.entry_id, codigo_amostra=info.codigo)
        logger.warning(f"[{info.codigo}] sem anexo XLS")
        return "ignorado_sem_anexo"

    # 6) Salva o anexo XLS no backup organizado
    try:
        data_ref = msg.received_at
        xls_path = _path_destino_anexo(info.codigo, data_ref, anexo_xls.filename)
        anexo_xls.save_to(xls_path)
        # PDF (se houver)
        for att in msg.attachments:
            if att.filename.lower().endswith('.pdf'):
                att.save_to(_path_destino_pdf(info.codigo, data_ref))
                break
    except Exception as e:
        registrar_log(msg.subject, msg.received_at, msg.sender_email,
                      "erro", msg.entry_id, codigo_amostra=info.codigo,
                      erro=f"falha ao salvar anexo: {e}")
        logger.exception(f"[{info.codigo}] falha ao salvar anexo")
        return "erro"

    # 7) Parser XLS
    try:
        anexo = parsers.parse(xls_path, info)
    except Exception as e:
        registrar_log(msg.subject, msg.received_at, msg.sender_email,
                      "erro", msg.entry_id, codigo_amostra=info.codigo,
                      erro=f"parser XLS falhou: {e}")
        logger.exception(f"[{info.codigo}] parser falhou")
        return "erro"

    # 8) Upsert no banco
    try:
        acao = upsert_amostra(
            anexo=anexo,
            tipo=info.tipo,
            tipo_codigo=info.prefixo_codigo,
            entry_id_outlook=msg.entry_id,
            email_received_at=msg.received_at,
            remetente=msg.sender_email,
            assunto=msg.subject,
            xls_path=xls_path,
        )
    except Exception as e:
        registrar_log(msg.subject, msg.received_at, msg.sender_email,
                      "erro", msg.entry_id, codigo_amostra=info.codigo,
                      erro=f"upsert falhou: {e}")
        logger.exception(f"[{info.codigo}] upsert falhou")
        return "erro"

    registrar_log(msg.subject, msg.received_at, msg.sender_email,
                  "ok", msg.entry_id, codigo_amostra=info.codigo)
    logger.info(f"[{info.codigo}] {info.processo}/{info.subcategoria or '-'} | "
                f"{info.tipo} | {acao} | {len(anexo.resultados)} resultados")
    return "ok"


def run(
    since: datetime,
    somente_processos: set[str] | None = None,
    pastas: list[str] | None = None,
):
    """Executa o coletor uma vez."""
    init_db()
    pastas = pastas or [PASTA_LABORATORIO, INBOX_PRINCIPAL]
    src = OutlookDesktopSource(pastas=pastas)

    ja_processados = entry_ids_processados()
    logger.info(f"Iniciando coleta | since={since:%Y-%m-%d %H:%M} | "
                f"ja_processados={len(ja_processados)} | "
                f"processos_alvo={somente_processos or 'TODOS'}")

    stats = {"ok": 0, "erro": 0, "ignorado_duplicata": 0,
             "ignorado_sem_anexo": 0, "ignorado_dominio": 0,
             "ignorado_processo_fora_fase": 0}

    for msg in src.fetch_unprocessed(since=since, already_processed_ids=ja_processados):
        status = processar_email(msg, somente_processos=somente_processos)
        stats[status] = stats.get(status, 0) + 1

    set_estado("ultima_execucao", datetime.now().isoformat())
    logger.info(f"Coleta finalizada: {stats}")
    return stats


def main():
    ap = argparse.ArgumentParser(description="Coletor AuraLab Borborema")
    grp = ap.add_mutually_exclusive_group()
    grp.add_argument("--since-days", type=int, default=1,
                     help="Janela em dias (default: 1)")
    grp.add_argument("--since", type=str, help="Data inicial YYYY-MM-DD")
    grp.add_argument("--backlog", action="store_true",
                     help=f"Processa desde {BACKLOG_INICIO}")
    ap.add_argument("--todos-processos", action="store_true",
                    help="Processa TODOS os processos (default: Fase 1)")
    args = ap.parse_args()

    _setup_logging()

    if args.backlog:
        since = datetime.combine(BACKLOG_INICIO, datetime.min.time())
    elif args.since:
        since = datetime.strptime(args.since, "%Y-%m-%d")
    else:
        since = datetime.now() - timedelta(days=args.since_days)

    somente = None if args.todos_processos else PROCESSOS_FASE1
    run(since=since, somente_processos=somente)


if __name__ == "__main__":
    main()
