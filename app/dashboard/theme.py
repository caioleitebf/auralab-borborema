"""CSS, logo e helpers de tema da identidade visual oficial Aura Borborema.

Cores e logo extraidos de:
  C:\\Users\\caio.ferreira\\OneDrive - Aura Minerals\\Area de Trabalho\\Modelo de Cores.pptx

Cores oficiais:
- Azul-marinho #2D3D70 (principal)
- Coral #F4614D (destaque)
"""
from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

from ..config import Cores, LOGO_PNG_WHITE


CSS = f"""
<style>
/* ---- Variaveis ---- */
:root {{
    --aura-blue: {Cores.AZUL_MARINHO};
    --aura-blue-dark: {Cores.AZUL_ESCURO};
    --aura-blue-med: {Cores.AZUL_MEDIO};
    --aura-coral: {Cores.CORAL};
    --aura-coral-med: {Cores.CORAL_MEDIO};
    --aura-coral-light: {Cores.CORAL_CLARO};
    --aura-coral-bg: {Cores.CORAL_BG};
    --aura-grey: {Cores.CINZA};
    --aura-grey-light: {Cores.CINZA_CLARO};
    --aura-bg-alt: {Cores.BG_ALT};
    --aura-border: {Cores.BORDA};
}}

/* ---- Sidebar customizada ---- */
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, var(--aura-blue) 0%, var(--aura-blue-dark) 100%);
    padding-top: 0;
}}
[data-testid="stSidebar"] * {{
    color: #fff !important;
}}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {{
    color: #fff !important;
}}

/* ---- HEADER: bloco unico azul-marinho ---- */
.aura-header {{
    background: linear-gradient(135deg, var(--aura-blue) 0%, var(--aura-blue-med) 100%);
    color: #fff;
    padding: 24px 32px;
    border-radius: 10px;
    margin-bottom: 22px;
    border-left: 6px solid var(--aura-coral);
}}
.aura-header .breadcrumb {{
    color: var(--aura-coral);
    font-size: 10.5pt;
    letter-spacing: 3px;
    margin-bottom: 6px;
    font-weight: 600;
    text-transform: uppercase;
}}
.aura-header h1 {{
    margin: 0;
    font-size: 24pt;
    font-weight: 600;
    color: #ffffff;   /* B2: titulo BRANCO */
    line-height: 1.1;
}}

/* ---- Cards de KPI ---- */
.kpi-card {{
    background: #fff;
    border: 1px solid var(--aura-border);
    border-radius: 10px;
    padding: 18px 20px;
    border-left: 5px solid var(--aura-coral);
    box-shadow: 0 1px 3px rgba(45,61,112,0.06);
    height: 100%;
}}
.kpi-card .label {{
    color: var(--aura-grey);
    font-size: 9.5pt;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    font-weight: 600;
}}
.kpi-card .value {{
    color: var(--aura-blue);
    font-size: 28pt;
    font-weight: 700;
    margin-top: 4px;
    line-height: 1.0;
}}
.kpi-card .sub {{
    color: var(--aura-grey);
    font-size: 9.5pt;
    margin-top: 6px;
}}

/* ---- Badges ---- */
.badge {{
    display: inline-block;
    padding: 3px 12px;
    border-radius: 12px;
    font-size: 9pt;
    font-weight: 600;
    letter-spacing: 0.5px;
}}
.badge-final {{ background: #e6f4ea; color: #1e7e34; }}
.badge-preliminar {{ background: var(--aura-coral-bg); color: var(--aura-coral); }}

/* ---- Tabela: cabecalho azul, batelada coral ---- */
[data-testid="stDataFrame"] thead tr th {{
    background-color: var(--aura-blue) !important;
    color: #fff !important;
    font-weight: 600 !important;
}}
[data-testid="stDataFrame"] tbody tr td {{
    font-size: 11pt;
}}

/* ---- Botoes ---- */
.stButton > button {{
    border-radius: 6px;
}}
.stButton > button[kind="primary"] {{
    background-color: var(--aura-coral);
    color: #fff;
    border: none;
}}
.stButton > button[kind="primary"]:hover {{
    background-color: var(--aura-coral-med);
}}

/* ---- Sub-secao com titulo de bloco ---- */
.bloco-titulo {{
    color: var(--aura-blue);
    font-size: 13pt;
    font-weight: 600;
    padding: 8px 0 4px 12px;
    border-left: 4px solid var(--aura-coral);
    margin: 18px 0 8px 0;
}}

/* ---- Separador limpo ---- */
hr {{
    border: 0;
    border-top: 1px solid var(--aura-border);
    margin: 24px 0;
}}

/* ---- Logo no topo da sidebar (PNG do manual de marca) ---- */
.aura-sidebar-logo {{
    padding: 24px 12px 28px 12px;
    border-bottom: 2px solid var(--aura-coral);
    margin: 0 0 14px 0;
    text-align: center;
    background: transparent;
}}
.aura-sidebar-logo img {{
    width: 230px;
    max-width: 100%;
    height: auto;
    display: block;
    margin: 0 auto;
}}

/* ---- streamlit-option-menu overrides para casar com o tema ---- */
.css-1y4p8pa {{ padding-top: 0 !important; }}

/* ---- Inputs DENTRO da sidebar (contraste no fundo azul-marinho) ---- */
/* Campos de texto e date_input precisam de texto LEGIVEL (azul-marinho) em fundo branco */
[data-testid="stSidebar"] input[type="text"],
[data-testid="stSidebar"] input[type="date"],
[data-testid="stSidebar"] input[type="password"],
[data-testid="stSidebar"] input[type="email"] {{
    background-color: #fff !important;
    color: var(--aura-blue) !important;
    border: 1px solid var(--aura-coral) !important;
    font-weight: 600;
}}
/* Placeholder mais visivel */
[data-testid="stSidebar"] input::placeholder {{
    color: var(--aura-grey) !important;
    opacity: 0.7;
}}
/* Date input: container e icone */
[data-testid="stSidebar"] [data-testid="stDateInput"] > div > div {{
    background-color: #fff !important;
    border: 1px solid var(--aura-coral) !important;
    border-radius: 6px;
}}
[data-testid="stSidebar"] [data-testid="stDateInput"] input {{
    color: var(--aura-blue) !important;
    font-weight: 600;
}}
/* Labels de input na sidebar */
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown p {{
    color: #fff !important;
    font-weight: 500;
}}

/* ---- Botao "Sair" do streamlit-authenticator (contraste correto) ---- */
[data-testid="stSidebar"] button[kind="secondary"] {{
    background-color: var(--aura-coral) !important;
    color: #fff !important;
    border: 1px solid var(--aura-coral) !important;
    font-weight: 600 !important;
    padding: 8px 16px !important;
}}
[data-testid="stSidebar"] button[kind="secondary"]:hover {{
    background-color: var(--aura-coral-med) !important;
    border-color: var(--aura-coral-med) !important;
    color: #fff !important;
}}
[data-testid="stSidebar"] button[kind="secondary"] p,
[data-testid="stSidebar"] button[kind="secondary"] span {{
    color: #fff !important;
    font-weight: 600 !important;
}}

/* ---- Download button na sidebar (mesmo destaque do "Atualizar dados") ---- */
[data-testid="stSidebar"] [data-testid="stDownloadButton"] button {{
    background-color: var(--aura-coral) !important;
    color: #fff !important;
    border: none !important;
    font-weight: 600;
    padding: 10px 14px;
}}
[data-testid="stSidebar"] [data-testid="stDownloadButton"] button:hover {{
    background-color: var(--aura-coral-med) !important;
    color: #fff !important;
}}
[data-testid="stSidebar"] [data-testid="stDownloadButton"] button p {{
    color: #fff !important;
    font-weight: 600;
}}

/* ---- Tabela HTML inline (para MultiIndex headers do pandas Styler) ---- */
.dataframe {{
    width: 100% !important;
    border-collapse: collapse !important;
    font-size: 10.5pt;
    font-family: 'Segoe UI', sans-serif;
    margin: 0;
}}
/* Esconde o index (numeros 0,1,2,...) que vem por padrao do pandas Styler */
.dataframe tbody th.row_heading,
.dataframe thead th.blank,
.dataframe thead th.index_name {{
    display: none !important;
}}
.dataframe thead th {{
    background-color: var(--aura-blue) !important;
    color: #fff !important;
    text-align: center !important;
    vertical-align: middle !important;
    padding: 8px 10px !important;
    border: 1px solid #fff !important;
    font-weight: 600;
}}
/* V1: Celulas vazias do nivel 0 (acima de DATA/TURNO) — invisiveis.
   O pandas mescla colunas contiguas com mesmo valor: como DATA/TURNO tem
   nivel0="" + ""  ela vira um unico TH com colspan=2 em nth-child(1). */
.dataframe thead tr:nth-child(1) th:nth-child(1),
.dataframe thead tr th:empty,
.dataframe thead tr th.blank,
.dataframe thead tr th.index_name {{
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    border-color: transparent !important;
    box-shadow: none !important;
    padding: 0 !important;
}}

/* V2: Garante centralizacao em TODAS as celulas de cabecalho */
.dataframe th.col_heading,
.dataframe th.col_heading.level0,
.dataframe th.col_heading.level1,
.dataframe th.row_heading {{
    text-align: center !important;
    vertical-align: middle !important;
}}
.dataframe tbody td,
.dataframe tbody th {{
    padding: 7px 10px !important;
    border: 1px solid var(--aura-border) !important;
    vertical-align: middle;
    text-align: center !important;              /* CENTRALIZADO em todas as celulas */
}}
.dataframe tbody tr:nth-child(even) td {{
    background-color: var(--aura-bg-alt);
}}
.dataframe tbody tr:hover td {{
    background-color: var(--aura-coral-bg) !important;
}}

/* Bordas sutis (sem contornos grossos entre grupos) */
.dataframe thead tr th,
.dataframe tbody td {{
    border-right: 1px solid var(--aura-border) !important;
}}
</style>
"""


def _img_data_uri(img_path: Path) -> str:
    """Retorna data: URI da imagem (PNG ou SVG), util em <img src=...>."""
    if not img_path.exists():
        return ""
    raw = img_path.read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    mime = "image/png" if img_path.suffix.lower() == ".png" else "image/svg+xml"
    return f"data:{mime};base64,{b64}"


def apply():
    """Aplica CSS global."""
    st.markdown(CSS, unsafe_allow_html=True)


def aura_logo_sidebar():
    """Logo OFICIAL Aura Borborema na sidebar (PNG do manual de marca).

    Arquivo: app/assets/aura_borborema_white.png
    (versao para fundo escuro: 'aura' em branco + simbolo coral + BORBOREMA coral)
    """
    uri = _img_data_uri(LOGO_PNG_WHITE)
    st.sidebar.markdown(
        f"""
        <div class="aura-sidebar-logo">
            <img src="{uri}" alt="aura BORBOREMA" />
        </div>
        """,
        unsafe_allow_html=True,
    )


def header(titulo: str, breadcrumb: str = "Controle Analítico de Amostras - Aura BBR"):
    """Header customizado da pagina."""
    st.markdown(
        f"""
        <div class="aura-header">
            <div class="breadcrumb">{breadcrumb}</div>
            <h1>{titulo}</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value: str, sub: str = "") -> str:
    return f"""
    <div class="kpi-card">
        <div class="label">{label}</div>
        <div class="value">{value}</div>
        <div class="sub">{sub}</div>
    </div>
    """


def badge(status: str) -> str:
    cls = "badge-final" if status == "final" else "badge-preliminar"
    return f'<span class="badge {cls}">{status.upper()}</span>'


def bloco_titulo(texto: str):
    st.markdown(f'<div class="bloco-titulo">{texto}</div>', unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Style helpers para DataFrames (pandas Styler)
# -----------------------------------------------------------------------------
def style_amostras(df, batelada_col: str | None = "Batelada"):
    """Aplica estilo Aura a tabela de amostras:
    - cabecalho azul (via CSS global ja faz, mas reforca)
    - coluna BATELADA com fundo coral
    - status final = verde, preliminar = coral
    """
    sty = df.style.set_table_styles([
        {"selector": "thead th",
         "props": [("background-color", Cores.AZUL_MARINHO),
                   ("color", "#fff"),
                   ("font-weight", "600"),
                   ("text-align", "center")]},
    ])
    if batelada_col and batelada_col in df.columns:
        def _bat_color(v):
            if v and str(v) != "nan" and str(v) != "None":
                return f"background-color: {Cores.CORAL_BG}; color: {Cores.AZUL_MARINHO}; font-weight: 600"
            return ""
        sty = sty.map(_bat_color, subset=[batelada_col])
    if "Status" in df.columns:
        def _status_color(v):
            v = str(v)
            if "Final" in v or "final" in v.lower():
                return "background-color: #e6f4ea; color: #1e7e34"
            elif "Preliminar" in v or "preliminar" in v.lower():
                return f"background-color: {Cores.CORAL_BG}; color: {Cores.CORAL}"
            return ""
        sty = sty.map(_status_color, subset=["Status"])
    return sty


def grafico_layout(fig, height: int = 380):
    """Aplica layout Aura padronizado a um grafico Plotly (visual mais limpo)."""
    fig.update_layout(
        height=height,
        plot_bgcolor="#fff",
        paper_bgcolor="#fff",
        margin=dict(l=10, r=10, t=30, b=40),
        font=dict(family="Segoe UI, sans-serif", size=11, color=Cores.CINZA),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1, bgcolor="rgba(255,255,255,0)"),
        xaxis=dict(showgrid=True, gridcolor=Cores.BORDA, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor=Cores.BORDA, zeroline=False),
        hovermode="x unified",
    )
    # Aplica seletivamente: 'line' so existe em Scatter, nao em Bar/Heatmap.
    try:
        fig.update_traces(
            selector=dict(type="scatter"),
            marker=dict(size=9, line=dict(width=1.5, color="#fff")),
            line=dict(width=2.5),
        )
    except Exception:
        pass
    try:
        fig.update_traces(
            selector=dict(type="bar"),
            marker=dict(line=dict(width=0)),
        )
    except Exception:
        pass
    return fig


# Paleta para uso em graficos com varias series
PALETA_SERIES = [
    Cores.AZUL_MARINHO,
    Cores.CORAL,
    Cores.AZUL_MEDIO,
    Cores.CORAL_MEDIO,
    Cores.CINZA,
    Cores.AZUL_ESCURO,
    Cores.CORAL_ESCURO,
    Cores.CINZA_CLARO,
]
