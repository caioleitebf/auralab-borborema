"""Parser base SGS Geosol -- estrutura comum a todos os relatorios.

Layout observado:
  R0  COA: PM<n>
  R1  CLIENT: Cascar Brasil Mineracao Ltda
  R2  # OF SAMPLES: <n>
  R3  DATE RECEIVED: <dd/mm/yyyy hh:mm:ss>
  R4  DATE FINALIZED: <dd/mm/yyyy hh:mm:ss>
  R5  PROJECT : Borborema
  R6  CERTIFICATE COMMENTS : ...
  R7  LAB PACK : ...
  R8  PO NUMBER : <descricao>
  R9  METHOD: <metodo_col_1> | <metodo_col_2> | ...
  R10 SAMPLE   | <elemento col_1> | <elemento col_2> | ...
  R11 DESCRIPTION | <unidade col_1> | <unidade col_2> | ...
  R12 LD       | <ld col_1>       | <ld col_2>       | ...
  R13+ <nome_amostra> | <valor_1> | <valor_2> | ...
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import xlrd
from loguru import logger

from ..subject_parser import SubjectInfo


# Constantes do layout SGS
HEADER_ROWS = 13         # cabecalho fixo
ROW_COA = 0
ROW_CLIENT = 1
ROW_DATE_RECEIVED = 3
ROW_DATE_FINALIZED = 4
ROW_PROJECT = 5
ROW_PO_NUMBER = 8
ROW_METHOD = 9
ROW_ELEMENT = 10         # Au, Ag, etc.
ROW_UNIT = 11
ROW_LD = 12
ROW_DATA_START = 13


@dataclass
class ResultadoParseado:
    """Uma linha de resultado (uma metrica de uma amostra)."""
    raw_label: str            # nome bruto da amostra (col 0)
    raw_value: str            # texto bruto do valor
    valor: float | None       # None se NA/vazio/nao numerico
    flag_ld: str              # "igual" | "menor_que" | "maior_que"
    unidade: str              # "ppm", "g/t", etc.
    elemento: str             # "Au", "Ag", "Peso_bruto", etc.
    metodo: str               # "AAS00V_CIP", "FAA313", etc.
    coluna_xls: int           # indice da coluna no Excel (debugging)


@dataclass
class AnexoParseado:
    """Saida completa do parsing de um anexo."""
    codigo: str                          # PM2602468
    processo: str
    subcategoria: str | None
    batelada: str | None
    turno: str | None
    data_amostra: datetime | None
    data_recebimento_lab: datetime | None
    data_finalizacao_lab: datetime | None
    projeto: str
    po_number: str
    metodos: list[str]
    resultados: list[ResultadoParseado] = field(default_factory=list)
    metadados_extras: dict[str, Any] = field(default_factory=dict)


_REGEX_HORARIO = re.compile(r"(?<!\d)(\d{1,2}):(\d{2})(?!\d)")
_REGEX_DATA_BR = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")


def _parse_value(raw: Any) -> tuple[float | None, str, str]:
    """Converte celula em (valor_float, flag_ld, raw_str).

    Trata:
    - "NA" -> (None, "igual", "NA")
    - "<0,01" -> (0.01, "menor_que", "<0,01")
    - ">50" -> (50.0, "maior_que", ">50")
    - "  679.515" -> (679.515, "igual", "...")  (ponto = decimal US)
    - "" -> (None, "igual", "")
    - 0.05 -> (0.05, "igual", "0.05")  (numero ja float)
    """
    if raw is None:
        return None, "igual", ""
    if isinstance(raw, (int, float)):
        return float(raw), "igual", str(raw)

    s = str(raw).strip()
    if not s or s.upper() == "NA":
        return None, "igual", s

    flag = "igual"
    if s.startswith("<"):
        flag = "menor_que"
        s_num = s[1:].strip()
    elif s.startswith(">"):
        flag = "maior_que"
        s_num = s[1:].strip()
    else:
        s_num = s

    # Normalizar separador decimal: lab usa ponto (US); PT-BR usa virgula.
    # Heuristica: se tem virgula E nao tem ponto, virgula e decimal.
    # Se tem ambos -> ponto = milhar, virgula = decimal (raro mas possivel).
    s_num = s_num.replace(" ", "")
    if "," in s_num and "." not in s_num:
        s_num = s_num.replace(",", ".")
    elif "," in s_num and "." in s_num:
        s_num = s_num.replace(".", "").replace(",", ".")

    try:
        valor = float(s_num)
        return valor, flag, str(raw).strip()
    except ValueError:
        return None, "igual", s


def _parse_datetime(raw: Any) -> datetime | None:
    """Converte celula em datetime, tentando varios formatos."""
    if raw is None or raw == "":
        return None
    if isinstance(raw, (int, float)) and raw > 0:
        try:
            # xlrd nao expande para datetime automaticamente
            return xlrd.xldate.xldate_as_datetime(raw, 0)
        except Exception:
            return None
    s = str(raw).strip()
    for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


class ParserGenerico:
    """Parser que extrai TUDO do anexo, sem mapeamento por processo.

    Funciona para qualquer relatorio que siga o layout SGS Geosol padrao.
    Subclasses podem sobrescrever para enriquecimento especifico.
    """

    def parse(self, xls_path: Path, info: SubjectInfo) -> AnexoParseado:
        book = xlrd.open_workbook(str(xls_path))
        if not book.sheet_names():
            raise ValueError(f"{xls_path}: arquivo sem sheets")
        sheet = book.sheet_by_index(0)

        coa = self._cell_str(sheet, ROW_COA, 1).strip()
        if coa and coa != info.codigo:
            logger.warning(
                f"COA do XLS ({coa!r}) difere do codigo do assunto ({info.codigo!r}); "
                "usando o codigo do assunto."
            )

        # Metadados do cabecalho
        po_number = self._cell_str(sheet, ROW_PO_NUMBER, 1).strip()
        projeto = self._cell_str(sheet, ROW_PROJECT, 1).strip()
        date_received = _parse_datetime(self._cell_raw(sheet, ROW_DATE_RECEIVED, 1))
        date_finalized = _parse_datetime(self._cell_raw(sheet, ROW_DATE_FINALIZED, 1))

        # Detecta variante "Bullion" / sample-id: quando col 0 e "Type" e col 1 e "Sample ID",
        # o label real esta na col 1 e os dados comecam na col 2.
        col_amostra = 0
        data_start_col = 1
        # No layout Bullion, header pode estar em R10 (formato diferente: 'Type'|'Sample ID'|elem|elem)
        # Detectamos olhando algumas linhas iniciais (R10 mesmo padrao SGS).
        sample_header_alt = self._cell_str(sheet, ROW_ELEMENT, 1).strip().lower()
        if sample_header_alt in ("sample id", "sample_id", "id"):
            col_amostra = 1
            data_start_col = 2

        # Identifica colunas de dados
        ncols = sheet.ncols
        colunas_dados = []
        for c in range(data_start_col, ncols):
            elemento = self._cell_str(sheet, ROW_ELEMENT, c).strip()
            metodo = self._cell_str(sheet, ROW_METHOD, c).strip()
            unidade = self._cell_str(sheet, ROW_UNIT, c).strip()
            if elemento or metodo or unidade:
                colunas_dados.append({
                    "col": c,
                    "elemento": elemento,
                    "metodo": metodo,
                    "unidade": unidade,
                })

        metodos = [c["metodo"] for c in colunas_dados if c["metodo"]]

        # Le amostras (linhas R13+)
        resultados: list[ResultadoParseado] = []
        for r in range(ROW_DATA_START, sheet.nrows):
            label = self._cell_str(sheet, r, col_amostra).strip()
            if not label:
                continue
            # Ignora 'SMP'/'STD' genericos quando col_amostra=0 -- isso indica
            # que o XLS tem o ID na coluna 1 (Sample ID) ja capturada acima.
            if col_amostra == 0 and label.upper() in ("SMP", "STD", "DUP", "STD-BLANK", "BLANK"):
                # Tenta col 1 como label alternativo
                label_alt = self._cell_str(sheet, r, 1).strip()
                if label_alt:
                    label = label_alt
            for cd in colunas_dados:
                raw = self._cell_raw(sheet, r, cd["col"])
                valor, flag, raw_str = _parse_value(raw)
                resultados.append(ResultadoParseado(
                    raw_label=label,
                    raw_value=raw_str,
                    valor=valor,
                    flag_ld=flag,
                    unidade=cd["unidade"],
                    elemento=cd["elemento"],
                    metodo=cd["metodo"],
                    coluna_xls=cd["col"],
                ))

        # Tenta extrair data da amostra do PO_NUMBER (ex: 11_REJ_CIL_..._DATA:22/05/2026)
        data_amostra = info.data_amostra_assunto
        if data_amostra is None:
            m = _REGEX_DATA_BR.search(po_number)
            if m:
                try:
                    from datetime import date
                    data_amostra = date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
                except ValueError:
                    pass

        # Tenta extrair turno do PO_NUMBER ou dos labels
        turno = info.turno
        if not turno:
            for hr_match in _REGEX_HORARIO.finditer(po_number + " " + " ".join(r.raw_label for r in resultados)):
                hh = int(hr_match.group(1))
                if hh in (7, 8, 9):
                    turno = "T1"
                    break
                elif hh in (15, 16, 17):
                    turno = "T2"
                    break
                elif hh in (22, 23, 0):
                    turno = "T3"
                    break

        return AnexoParseado(
            codigo=info.codigo,
            processo=info.processo,
            subcategoria=info.subcategoria,
            batelada=info.batelada,
            turno=turno,
            data_amostra=data_amostra,
            data_recebimento_lab=date_received,
            data_finalizacao_lab=date_finalized,
            projeto=projeto,
            po_number=po_number,
            metodos=metodos,
            resultados=resultados,
        )

    # --- helpers --------------------------------------------------------------
    @staticmethod
    def _cell_str(sheet, r: int, c: int) -> str:
        try:
            val = sheet.cell_value(r, c)
        except IndexError:
            return ""
        return str(val) if val is not None else ""

    @staticmethod
    def _cell_raw(sheet, r: int, c: int) -> Any:
        try:
            return sheet.cell_value(r, c)
        except IndexError:
            return None
