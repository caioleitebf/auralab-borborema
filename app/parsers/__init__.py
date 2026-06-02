"""Parsers de anexos Excel por tipo de processo.

Cada parser converte um arquivo .XLS do SGS Geosol em um AnexoParseado.
A escolha do parser e feita pelo dispatcher abaixo, baseado no processo
identificado no assunto do email.
"""
from __future__ import annotations

from pathlib import Path

from ..subject_parser import SubjectInfo
from .base import AnexoParseado, ParserGenerico, ResultadoParseado  # noqa: F401


# Registry de parsers especificos (sobrescrevem o generico para regras especiais)
_PARSERS_ESPECIFICOS: dict[str, type] = {}


def register(processo: str):
    """Decorator para registrar parser de processo especifico."""
    def _wrap(cls):
        _PARSERS_ESPECIFICOS[processo] = cls
        return cls
    return _wrap


def parse(xls_path: Path, subject_info: SubjectInfo) -> AnexoParseado:
    """Despacha para o parser correto baseado no processo."""
    parser_cls = _PARSERS_ESPECIFICOS.get(subject_info.processo, ParserGenerico)
    return parser_cls().parse(xls_path, subject_info)


# Importa modulos especificos para registrar os decorators
from . import lixiviacao  # noqa: E402,F401
from . import acacia      # noqa: E402,F401
from . import eletrolise  # noqa: E402,F401
