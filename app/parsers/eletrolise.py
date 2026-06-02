"""Parser de Eletrolise (CE0001 e CE0002).

Layout dos labels:
  ENTRADA_CE0001_HH:00_BAT_XXX
  SAIDA_CE0001_HH:00_BAT_XXX
  (mesmo para CE0002)

Cada PM cobre uma batelada de uma das celulas. Serie temporal por hora.
"""
from __future__ import annotations

from . import register
from .base import ParserGenerico


@register("ELETROLISE")
class ParserEletrolise(ParserGenerico):
    """Parser de Eletrolise -- herda extracao bruta do generico."""
    pass
