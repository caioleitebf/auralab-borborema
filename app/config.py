"""Configuracoes globais do AuraLab Borborema."""
from __future__ import annotations

from pathlib import Path
from datetime import date


# --- Caminhos do projeto -----------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
ANEXOS_DIR = ROOT / "anexos"
DATABASE_DIR = ROOT / "database"
DATABASE_PATH = DATABASE_DIR / "auralab.db"
LOGS_DIR = ROOT / "logs"


# --- Outlook -----------------------------------------------------------------
# Pasta criada no Outlook com a regra que filtra emails do laboratorio.
PASTA_LABORATORIO = "Resultados_Laboratório"

# Caixa onde o Bullion chega (vai pro Inbox principal, nao pra pasta filtrada).
INBOX_PRINCIPAL = "Caixa de Entrada"


# --- Dominios aceitos como remetentes do laboratorio -------------------------
DOMINIOS_LAB = (
    "@ou.sgsgeosol.com.br",
    "@sgsgeosol.com.br",
)


# --- Identificadores aceitos no assunto --------------------------------------
# PR aparece em "Amostras de processo" -- variacao rara, mas existe.
PREFIXOS_CODIGO = ("PM", "EC", "AB", "PR")


# --- Backlog -----------------------------------------------------------------
BACKLOG_INICIO = date(2026, 1, 1)


# --- Processos e mapeamento de assunto ---------------------------------------
# Tokens (apos normalizacao) que identificam cada processo no assunto.
# Tudo upper, sem acentos.
PROCESSOS = {
    "LIXIVIACAO": {
        "tokens": [
            # Variantes de "Rej./Alim" e "Rej./Ali."
            "REJ./ALIM", "REJ/ALIM", "REJALIM",
            "REJ. / ALI.", "REJ./ ALI.", "REJ. /ALI.",
            "REJ./ALI.", "REJ./ALI", "REJ/ ALI",
            "REJ /ALI", "REJ/ALI",
            "REJ. ALI.", "REJ. ALI", "REJ ALI",
            "REJ.ALIM", "REJ.ALIM.", "REJ.ALI.",        # sem espacos
            "REJ ALM", "REJ. ALM", "REJ.ALM",
            "ALI.REJ", "ALI. REJ", "ALI REJ",
            "ALIM.REJ", "ALIM. REJ", "ALIM REJ",        # Alim. abreviado
            # Variantes "REJEITO/ALIMENTACAO" e similares
            "REJEITO/ALIMENTACAO", "REJEITO ALIMENTACAO",
            "REJEITO/ ALIMENTACAO", "REJEITO /ALIMENTACAO",
            "REJEITO-ALIMENTACAO",                        # com hifen
            "REJEITO E ALIMENTACAO", "REJEITO E ALIM",
            "ALIMENTACAO E REJEITO", "ALIMENTACAO/REJEITO",
            "ALIMENTACAO E REJ", "ALIM E REJEITO", "ALIM E REJ",
        ],
        "subcategoria_token": None,
    },
    "TANQUES": {
        "tokens": ["TQS.DIARIO", "TANQUE.DIARIO", "TQS", "TANQUES", "TANQUE"],
        "subcategoria_token": None,
    },
    "ACACIA": {
        "tokens": [
            "ACACIA", "ACACA",       # 'ACACA' = typo visto em alguns emails
            "SOL.RICA.ACACIA",       # sem espacos
            "SOL.RICA",              # sem espaco depois do ponto
            "SOL RICA",              # sem ponto
            "SOL. RICA",             # Clara/Deyvid
            "SOLUCAO RICA",          # forma extensa
            "REJ. DE ACACIA", "REJ. ACACIA", "REJ ACACIA",
        ],
        "subcategoria_token": {
            "Sol. Rica": ["SOL.RICA", "SOL. RICA", "SOL RICA", "SOLUCAO RICA", "RICA ACACIA"],
            "Over": ["OVER ACACIA", "OVER DO ACACIA", "OVER"],
            "Rejeito": ["REJ. DE ACACIA", "REJ. ACACIA", "REJEITO ACACIA"],
        },
    },
    "ELUICAO": {
        "tokens": [
            "ELUICAO", "CARVAO ELUICAO",
            "CARVAO ELUIDO", "CARVAO ELUDIO",
            "CARVAO RICO",
            "INVENT_ CARVAO", "INVENTARIO CARVAO", "INVENTARIO-CARVAO",
            "CARVAO INVENTARIO", "INVENTARIO",
            "INVENTARIO SOLIDOS", "INVENTARIO-SOLIDOS",
            "CALCIO EM CARVAO", "CA EM CARVAO",
            "CARVAO",
        ],
        "subcategoria_token": {
            "Carvao Eluido": ["CARVAO ELUIDO", "CARVAO ELUDIO", "ELUIDO"],
            "Carvao Rico": ["CARVAO RICO"],
            "Inventario": ["INVENT_ CARVAO", "INVENTARIO CARVAO",
                           "INVENTARIO-CARVAO", "CARVAO INVENTARIO", "INVENTARIO"],
            "Cálcio em Carvão": ["CALCIO EM CARVAO", "CA EM CARVAO"],
            "Inventário Sólidos": ["INVENTARIO SOLIDOS", "INVENTARIO-SOLIDOS"],
        },
    },
    "ELETROLISE": {
        "tokens": [
            "LICOR-CE", "LICOR CE",
            "CE01", "CE02",                                   # sem zero extra
            "CE0001", "CE0002", "CE001", "CE002",
            "CE 01", "CE 02", "CE 001", "CE 002",             # com espaco
            "CE 0001", "CE 0002",
            "CE-001", "CE-002", "CE-0001", "CE-0002",         # com hifen
            "CE-01", "CE-02",
            "CE - 001", "CE - 002", "CE - 0001", "CE - 0002",
            "CE - 01", "CE - 02",
            "E 001", "E 002",                                 # variante sem o C (typo)
            "E 0001", "E 0002",
        ],
        "subcategoria_token": {
            "CE0001": ["CE0001", "CE001", "CE01", "CE 01", "CE 001", "CE 0001",
                       "CE-001", "CE-01", "CE-0001", "CE - 001", "CE - 01", "CE - 0001",
                       "E 001", "E 0001"],
            "CE0002": ["CE0002", "CE002", "CE02", "CE 02", "CE 002", "CE 0002",
                       "CE-002", "CE-02", "CE-0002", "CE - 002", "CE - 02", "CE - 0002",
                       "E 002", "E 0002"],
        },
    },
    "AGUA_PROCESSO": {
        "tokens": [
            "AGUA DE PROCESSO", "AGUA PROCESSO",
            "AGUA DO PROCESSO",
            "AGUA PROC.", "AGUA PROC",      # abreviado
            "AGUA-PROCESSO",
            "AMOSTRA DE PROCESSO",
        ],
        "subcategoria_token": None,
    },
    "DETOX": {
        "tokens": ["DETOX", "CIANETO WAD", "CIANETO LIVRE", "SAIDA DETOX"],
        "subcategoria_token": {
            "Cianeto WAD": ["CIANETO WAD", "CN WAD"],
            "Cianeto Livre": ["CIANETO LIVRE", "CN LIVRE"],
        },
    },
    "BULLION": {
        "tokens": ["BULLION"],
        "subcategoria_token": None,
    },
}

# Processos cobertos na Fase 1 (MVP)
PROCESSOS_FASE1 = {"LIXIVIACAO", "ACACIA", "ELETROLISE"}


# --- Status de amostras ------------------------------------------------------
STATUS_PRELIMINAR = "preliminar"
STATUS_FINAL = "final"


# --- Identidade visual Aura Borborema (cores oficiais extraidas do PPTX) -----
class Cores:
    """Paleta oficial Aura Borborema (Modelo de Cores.pptx)."""
    # Cores PRIMARIAS
    AZUL_MARINHO = "#2D3D70"   # cor principal do logo + sidebar
    CORAL = "#F4614D"          # destaque (texto BORBOREMA, batelada, alertas)
    # Variantes (do mesmo PPTX)
    AZUL_ESCURO = "#18213D"    # variante mais escura
    AZUL_MEDIO = "#3C4788"     # variante intermediaria
    CORAL_ESCURO = "#BB4D3D"
    CORAL_MEDIO = "#FF9477"
    CORAL_CLARO = "#FFB5A2"
    CORAL_BG = "#FFCFC3"       # background coral suave
    AZUL_BG = "#E7EEFF"        # background azul suave
    CINZA = "#4D5054"
    CINZA_CLARO = "#A0A9D1"
    BG_ALT = "#F7F9FC"
    BORDA = "#E5E7EF"


# --- Paths dos assets visuais ------------------------------------------------
ASSETS_DIR = Path(__file__).resolve().parent / "assets"
# PNG oficial do manual de marca Aura Borborema (Consultas Rapidas)
LOGO_PNG_WHITE = ASSETS_DIR / "aura_borborema_white.png"  # fundo escuro (sidebar)
LOGO_PNG_DARK = ASSETS_DIR / "aura_borborema_dark.png"    # fundo claro (headers)
# SVGs antigos (fallback, marca corporativa Aura 360 Mining sem 'Borborema')
LOGO_DARK_SVG = ASSETS_DIR / "aura_logo_dark.svg"
LOGO_WHITE_SVG = ASSETS_DIR / "aura_logo_white.svg"


# --- Locale -----------------------------------------------------------------
LOCALE_BR = "pt_BR.UTF-8"
