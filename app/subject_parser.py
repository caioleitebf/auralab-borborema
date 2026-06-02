"""Parser do assunto dos emails do laboratorio.

Lida com variacoes de operadores (Deyvid, Anthony, Joicy, Maik, Augustto) que
usam separadores e capitalizacao diferentes. Veja PRD secoes 5.4-5.6.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

from .config import PROCESSOS, PREFIXOS_CODIGO


TipoResultado = Literal["Preliminar", "Analitico"]


@dataclass
class SubjectInfo:
    tipo: TipoResultado
    codigo: str               # "PM2602458"
    prefixo_codigo: str       # "PM" | "EC" | "AB"
    processo: str             # chave de PROCESSOS (ex: "LIXIVIACAO")
    subcategoria: str | None  # "Sol. Rica" | "CE0001" | "Cianeto WAD" | ...
    batelada: str | None      # "BAT-386"
    turno: str | None         # "T2"
    data_amostra_assunto: date | None
    is_reply: bool
    raw_subject: str


def normalize(text: str) -> str:
    """Remove acentos, deixa upper, normaliza espacos."""
    nfkd = unicodedata.normalize("NFKD", text)
    no_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", no_accents.upper()).strip()


_REGEX_CODIGO = re.compile(
    r"\b(" + "|".join(PREFIXOS_CODIGO) + r")(\d{4,})\b"
)
_REGEX_BAT = re.compile(r"\bBAT[\s\-]?(\d{1,5})\b", re.IGNORECASE)
_REGEX_TURNO = re.compile(r"TURNO\s*:?\s*T(\d)", re.IGNORECASE)
_REGEX_DATA_LONGA = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")
_REGEX_DATA_CURTA = re.compile(r"\b(\d{1,2})/(\d{1,2})\b")


def _detectar_processo(after_code_norm: str) -> tuple[str, str | None]:
    """Identifica processo e subcategoria a partir do trecho apos o codigo.

    Estrategia: testa tokens de cada processo na ordem de especificidade.
    Detox tem prioridade quando aparece 'CIANETO' (mesmo sem 'DETOX').
    """
    # 1) Processos com tokens de alta especificidade primeiro
    ordem = [
        "LIXIVIACAO",
        "AGUA_PROCESSO",
        "TANQUES",
        "ELUICAO",
        "BULLION",
        "DETOX",
        "ELETROLISE",
        "ACACIA",
    ]
    for proc in ordem:
        cfg = PROCESSOS[proc]
        for token in cfg["tokens"]:
            if normalize(token) in after_code_norm:
                # Resolve subcategoria
                sub = None
                if cfg["subcategoria_token"]:
                    for sub_name, sub_tokens in cfg["subcategoria_token"].items():
                        if any(normalize(t) in after_code_norm for t in sub_tokens):
                            sub = sub_name
                            break
                return proc, sub
    # Fallback
    return "DESCONHECIDO", None


def _detectar_data_amostra(after_code: str) -> date | None:
    """Extrai data da amostra quando vem no assunto.

    Bullion usa formato longo (DD/MM/YYYY); outros usam DD/MM.
    Para DD/MM, assume o ano corrente.
    """
    m = _REGEX_DATA_LONGA.search(after_code)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            return None

    m = _REGEX_DATA_CURTA.search(after_code)
    if m:
        try:
            return date(datetime.now().year, int(m.group(2)), int(m.group(1)))
        except ValueError:
            return None
    return None


def parse_subject(subject: str) -> SubjectInfo | None:
    """Extrai metadados do assunto.

    Retorna None se o email nao parece ser do laboratorio (sem codigo, sem
    palavras-chave 'Analitico'/'Preliminar', etc.).
    """
    if not subject:
        return None

    norm = normalize(subject)

    # Re: indica resposta -- importante para deduplicacao
    is_reply = bool(re.match(r"^\s*(\[EXTERNAL\])?\s*RE\s*:", norm))

    # Tipo
    if "PRELIMINAR" in norm:
        tipo: TipoResultado = "Preliminar"
    elif "ANALITICO" in norm:
        tipo = "Analitico"
    elif "ENVIO DE RESULTADO" in norm:
        # Fallback: alguns assuntos so dizem "Envio de Resultado" sem qualificar.
        # Assumimos Analitico (mais comum). Veja PRD secao 5.5.
        tipo = "Analitico"
    else:
        return None  # nao e email de resultado do lab

    # Codigo (PM/EC/AB)
    m = _REGEX_CODIGO.search(norm)
    if not m:
        return None
    prefixo = m.group(1)
    numero = m.group(2)
    codigo = f"{prefixo}{numero}"

    # Trecho apos o codigo (onde estao processo, batelada, etc.)
    after_code_norm = norm[m.end():].strip(" -:")
    after_code_raw = subject[subject.upper().find(prefixo + numero) + len(codigo):].strip(" -:")

    processo, subcategoria = _detectar_processo(after_code_norm)

    batelada = None
    bm = _REGEX_BAT.search(after_code_norm)
    if bm:
        batelada = f"BAT-{bm.group(1)}"

    turno = None
    tm = _REGEX_TURNO.search(after_code_norm)
    if tm:
        turno = f"T{tm.group(1)}"

    data_amostra = _detectar_data_amostra(after_code_raw)

    return SubjectInfo(
        tipo=tipo,
        codigo=codigo,
        prefixo_codigo=prefixo,
        processo=processo,
        subcategoria=subcategoria,
        batelada=batelada,
        turno=turno,
        data_amostra_assunto=data_amostra,
        is_reply=is_reply,
        raw_subject=subject,
    )
