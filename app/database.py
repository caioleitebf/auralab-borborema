"""SQLite -- schema, upsert e queries do AuraLab Borborema.

Tabelas:
- amostras (codigo_amostra PK): metadados da amostra
- resultados (cada metrica/elemento extraida do XLS)
- processamento_log (auditoria de cada email)
- estado_coletor (chaves auxiliares: ultima_execucao etc.)

Upsert Preliminar -> Analitico:
- INSERT se codigo nao existe
- UPDATE se ja existe e o novo email e Analitico (substitui preliminar)
- UPDATE se ja existe e tem entry_id diferente (reprocessamento)
- Resultados sao SEMPRE substituidos (delete + insert).
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

from loguru import logger

from .config import DATABASE_PATH, STATUS_FINAL, STATUS_PRELIMINAR
from .parsers.base import AnexoParseado


SCHEMA = """
CREATE TABLE IF NOT EXISTS amostras (
    codigo_amostra          TEXT PRIMARY KEY,
    tipo_codigo             TEXT,
    processo                TEXT NOT NULL,
    subcategoria            TEXT,
    status                  TEXT NOT NULL,            -- preliminar | final
    batelada                TEXT,
    turno                   TEXT,
    data_amostra            DATE,
    data_recebimento_lab    TIMESTAMP,
    data_finalizacao_lab    TIMESTAMP,
    data_recebimento_email  TIMESTAMP,
    remetente_email         TEXT,
    assunto_original        TEXT,
    po_number               TEXT,
    metodos                 TEXT,                     -- JSON list
    arquivo_xls_path        TEXT,
    entry_id_outlook        TEXT UNIQUE,
    versao                  INTEGER DEFAULT 1,
    criado_em               TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_amostras_processo ON amostras(processo);
CREATE INDEX IF NOT EXISTS idx_amostras_data ON amostras(data_amostra);
CREATE INDEX IF NOT EXISTS idx_amostras_status ON amostras(status);
CREATE INDEX IF NOT EXISTS idx_amostras_batelada ON amostras(batelada);

CREATE TABLE IF NOT EXISTS resultados (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_amostra  TEXT NOT NULL REFERENCES amostras(codigo_amostra) ON DELETE CASCADE,
    raw_label       TEXT NOT NULL,
    valor           REAL,
    flag_ld         TEXT DEFAULT 'igual',
    unidade         TEXT,
    elemento        TEXT,
    metodo          TEXT,
    raw_value       TEXT,
    coluna_xls      INTEGER
);

CREATE INDEX IF NOT EXISTS idx_resultados_codigo ON resultados(codigo_amostra);
CREATE INDEX IF NOT EXISTS idx_resultados_label ON resultados(raw_label);

CREATE TABLE IF NOT EXISTS processamento_log (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    email_subject       TEXT,
    email_received_at   TIMESTAMP,
    remetente_email     TEXT,
    status              TEXT NOT NULL,             -- ok | erro | ignorado_duplicata | ignorado_dominio | ignorado_sem_anexo
    erro_detalhe        TEXT,
    codigo_amostra      TEXT,
    entry_id_outlook    TEXT
);

CREATE INDEX IF NOT EXISTS idx_log_timestamp ON processamento_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_log_status ON processamento_log(status);

CREATE TABLE IF NOT EXISTS estado_coletor (
    chave           TEXT PRIMARY KEY,
    valor           TEXT,
    atualizado_em   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


@contextmanager
def get_conn(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """Context manager para conexao SQLite."""
    path = db_path or DATABASE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(
        str(path),
        detect_types=sqlite3.PARSE_DECLTYPES,
        timeout=30,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Path | None = None):
    """Cria/atualiza schema do banco."""
    with get_conn(db_path) as conn:
        conn.executescript(SCHEMA)
    logger.info(f"Schema inicializado em {db_path or DATABASE_PATH}")


# -----------------------------------------------------------------------------
# Idempotencia / dedup
# -----------------------------------------------------------------------------
def entry_id_ja_processado(entry_id: str, db_path: Path | None = None) -> bool:
    """Checa se este entry_id ja foi processado com sucesso."""
    with get_conn(db_path) as conn:
        r = conn.execute(
            "SELECT 1 FROM processamento_log "
            "WHERE entry_id_outlook = ? AND status = 'ok' LIMIT 1",
            (entry_id,),
        ).fetchone()
        return r is not None


def entry_ids_processados(db_path: Path | None = None) -> set[str]:
    """Retorna set de entry_ids ja processados com sucesso (para fetch)."""
    with get_conn(db_path) as conn:
        rows = conn.execute(
            "SELECT DISTINCT entry_id_outlook FROM processamento_log "
            "WHERE status = 'ok' AND entry_id_outlook IS NOT NULL"
        ).fetchall()
        return {r[0] for r in rows if r[0]}


# -----------------------------------------------------------------------------
# Upsert
# -----------------------------------------------------------------------------
def upsert_amostra(
    anexo: AnexoParseado,
    tipo: str,                     # "Preliminar" | "Analitico"
    tipo_codigo: str,              # "PM" | "EC" | "AB" | "PR"
    entry_id_outlook: str,
    email_received_at: datetime,
    remetente: str,
    assunto: str,
    xls_path: Path,
    db_path: Path | None = None,
) -> str:
    """Faz upsert na tabela amostras + substitui resultados.

    Returns: "inserido" | "atualizado_para_final" | "atualizado_mesmo_status"
    """
    status_novo = STATUS_FINAL if tipo == "Analitico" else STATUS_PRELIMINAR

    with get_conn(db_path) as conn:
        # Verifica se ja existe
        existente = conn.execute(
            "SELECT status, versao FROM amostras WHERE codigo_amostra = ?",
            (anexo.codigo,),
        ).fetchone()

        if existente is None:
            acao = "inserido"
            conn.execute("""
                INSERT INTO amostras (
                    codigo_amostra, tipo_codigo, processo, subcategoria, status,
                    batelada, turno, data_amostra,
                    data_recebimento_lab, data_finalizacao_lab,
                    data_recebimento_email, remetente_email, assunto_original,
                    po_number, metodos, arquivo_xls_path, entry_id_outlook, versao
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)
            """, (
                anexo.codigo, tipo_codigo, anexo.processo, anexo.subcategoria,
                status_novo, anexo.batelada, anexo.turno, anexo.data_amostra,
                anexo.data_recebimento_lab, anexo.data_finalizacao_lab,
                email_received_at, remetente, assunto,
                anexo.po_number, json.dumps(anexo.metodos), str(xls_path),
                entry_id_outlook,
            ))
        else:
            status_anterior = existente["status"]

            # REGRA CRITICA: nunca rebaixar de "final" para "preliminar".
            # Pode acontecer quando varremos do mais recente para o mais
            # antigo e o Preliminar antigo chega depois do Final.
            if status_anterior == STATUS_FINAL and status_novo == STATUS_PRELIMINAR:
                logger.debug(f"[{anexo.codigo}] Ignorando preliminar antigo "
                             "(ja temos analitico final).")
                return "ignorado_preliminar_apos_final"

            versao_nova = existente["versao"] + 1
            if status_anterior == STATUS_PRELIMINAR and status_novo == STATUS_FINAL:
                acao = "atualizado_para_final"
            else:
                acao = "atualizado_mesmo_status"

            conn.execute("""
                UPDATE amostras SET
                    tipo_codigo = ?, processo = ?, subcategoria = ?, status = ?,
                    batelada = ?, turno = ?, data_amostra = ?,
                    data_recebimento_lab = ?, data_finalizacao_lab = ?,
                    data_recebimento_email = ?, remetente_email = ?, assunto_original = ?,
                    po_number = ?, metodos = ?, arquivo_xls_path = ?, entry_id_outlook = ?,
                    versao = ?, atualizado_em = CURRENT_TIMESTAMP
                WHERE codigo_amostra = ?
            """, (
                tipo_codigo, anexo.processo, anexo.subcategoria, status_novo,
                anexo.batelada, anexo.turno, anexo.data_amostra,
                anexo.data_recebimento_lab, anexo.data_finalizacao_lab,
                email_received_at, remetente, assunto,
                anexo.po_number, json.dumps(anexo.metodos), str(xls_path),
                entry_id_outlook, versao_nova,
                anexo.codigo,
            ))

        # Substitui resultados (so para acoes que efetivamente gravaram)
        conn.execute("DELETE FROM resultados WHERE codigo_amostra = ?", (anexo.codigo,))
        if anexo.resultados:
            conn.executemany("""
                INSERT INTO resultados (
                    codigo_amostra, raw_label, valor, flag_ld, unidade,
                    elemento, metodo, raw_value, coluna_xls
                ) VALUES (?,?,?,?,?,?,?,?,?)
            """, [(
                anexo.codigo, r.raw_label, r.valor, r.flag_ld, r.unidade,
                r.elemento, r.metodo, r.raw_value, r.coluna_xls,
            ) for r in anexo.resultados])

    return acao


def registrar_log(
    email_subject: str,
    email_received_at: datetime | None,
    remetente: str,
    status: str,
    entry_id: str | None,
    codigo_amostra: str | None = None,
    erro: str | None = None,
    db_path: Path | None = None,
):
    """Grava entrada no processamento_log para auditoria."""
    with get_conn(db_path) as conn:
        conn.execute("""
            INSERT INTO processamento_log
                (email_subject, email_received_at, remetente_email, status,
                 erro_detalhe, codigo_amostra, entry_id_outlook)
            VALUES (?,?,?,?,?,?,?)
        """, (email_subject, email_received_at, remetente, status,
              erro, codigo_amostra, entry_id))


# -----------------------------------------------------------------------------
# Estado do coletor
# -----------------------------------------------------------------------------
def get_estado(chave: str, default: str | None = None, db_path: Path | None = None) -> str | None:
    with get_conn(db_path) as conn:
        r = conn.execute("SELECT valor FROM estado_coletor WHERE chave = ?", (chave,)).fetchone()
        return r["valor"] if r else default


def set_estado(chave: str, valor: str, db_path: Path | None = None):
    with get_conn(db_path) as conn:
        conn.execute("""
            INSERT INTO estado_coletor (chave, valor) VALUES (?, ?)
            ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor,
                                              atualizado_em = CURRENT_TIMESTAMP
        """, (chave, valor))


# -----------------------------------------------------------------------------
# Queries para o dashboard
# -----------------------------------------------------------------------------
def listar_amostras_por_processo(
    processo: str,
    data_ini: datetime | None = None,
    data_fim: datetime | None = None,
    db_path: Path | None = None,
) -> list[sqlite3.Row]:
    sql = "SELECT * FROM amostras WHERE processo = ?"
    params: list = [processo]
    if data_ini:
        sql += " AND data_amostra >= ?"
        params.append(data_ini.date())
    if data_fim:
        sql += " AND data_amostra <= ?"
        params.append(data_fim.date())
    sql += " ORDER BY data_amostra DESC, data_recebimento_email DESC"
    with get_conn(db_path) as conn:
        return conn.execute(sql, params).fetchall()


def listar_resultados(codigo_amostra: str, db_path: Path | None = None) -> list[sqlite3.Row]:
    with get_conn(db_path) as conn:
        return conn.execute(
            "SELECT * FROM resultados WHERE codigo_amostra = ? ORDER BY id",
            (codigo_amostra,),
        ).fetchall()


def estatisticas(db_path: Path | None = None) -> dict:
    """Resumo geral para a home do dashboard."""
    with get_conn(db_path) as conn:
        total_amostras = conn.execute("SELECT COUNT(*) FROM amostras").fetchone()[0]
        preliminares = conn.execute(
            "SELECT COUNT(*) FROM amostras WHERE status = ?", (STATUS_PRELIMINAR,)
        ).fetchone()[0]
        finais = conn.execute(
            "SELECT COUNT(*) FROM amostras WHERE status = ?", (STATUS_FINAL,)
        ).fetchone()[0]
        por_processo = dict(conn.execute("""
            SELECT processo, COUNT(*) FROM amostras GROUP BY processo
        """).fetchall())
        ultimos_logs = conn.execute("""
            SELECT * FROM processamento_log ORDER BY timestamp DESC LIMIT 20
        """).fetchall()
        return {
            "total_amostras": total_amostras,
            "preliminares": preliminares,
            "finais": finais,
            "por_processo": por_processo,
            "ultimos_logs": ultimos_logs,
        }
