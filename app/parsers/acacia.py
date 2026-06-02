"""Parser de Acacia (Sol. Rica / Over / Rejeito).

Cada email de Acacia traz APENAS UMA das medidas da batelada:
- Sol. Rica: amostra rica
- Over: serie horaria do over (0h, 1h, 2h, ...)
- Rejeito: rejeito da acacia

O dashboard agrega varios PMs por batelada.
"""
from __future__ import annotations

from . import register
from .base import ParserGenerico


@register("ACACIA")
class ParserAcacia(ParserGenerico):
    """Parser de Acacia -- herda extracao bruta do generico."""
    pass
