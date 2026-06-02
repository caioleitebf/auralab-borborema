"""Parser de Lixiviacao (Rej./Alim CIL).

Layout dos labels observado:
  REJEITO_CIL_(POLPA)_HH:00
  ALIMENTACAO_CIL_(POLPA)_HH:00
  REJEITO_CIL_(SOLUVEL)_HH:00
  ALIMENTACAO_CIL_(SOLUVEL)_HH:00
  REJEITO_CIL_(SOLIDO)_HH:00
  ALIMENTACAO_CIL_(SOLIDO)_HH:00

Colunas (R10):
  - Peso_bruto (kg)        -> metodo PRP_PL
  - Au (ppm)               -> metodo AAS00V_CIP (soluveis)
  - Au (ppm)               -> metodo FAA313 (solidos)
"""
from __future__ import annotations

from . import register
from .base import ParserGenerico


@register("LIXIVIACAO")
class ParserLixiviacao(ParserGenerico):
    """Parser de Lixiviacao -- herda extracao bruta do generico.

    A canonicalizacao (RJT_CIL_SOLIDO etc.) e feita na camada de visualizacao
    para manter o banco fiel ao XLS original.
    """
    pass
