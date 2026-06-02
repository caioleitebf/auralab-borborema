"""AuraLab Borborema -- Dashboard Streamlit (v3).

Aplica todas as Ponderacoes G-M:
- G: Logo PNG oficial Aura Borborema (arquivo do manual de marca)
- H: Menu lateral com fundo azul-marinho solido (alto contraste)
- I: Lixiviacao consolidada por TURNO (1o/2o/3o) com regra de transicao
- J: Grafico Recuperacao CIL com eixo categorico + range dinamico + cor por meta
- K: Acacia formato planilha oficial (BATELADA num, cabecalho agrupado, OVER 1h..)
- L: Acacia com 2 graficos separados (Rica e Rejeito)
- M: Eletrolise 1 linha por medicao (Data, Hora, Bat, Entrada/Saida, Au)
"""
from __future__ import annotations

import sys
from datetime import date, datetime, timedelta
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent.parent))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_option_menu import option_menu

from app.config import Cores
from app.database import estatisticas, get_conn, get_estado, init_db
from app.dashboard import theme, canonical, exporter, auth

# Garante que TODAS as tabelas existem.
init_db()


# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AuraLab Borborema",
    page_icon="🟧",
    layout="wide",
    initial_sidebar_state="expanded",
)
theme.apply()

# --- LOGIN OBRIGATORIO (so quando rodar com secrets configurados) ---
usuario_atual = auth.login_obrigatorio()


# =============================================================================
# Sidebar: logo + menu
# =============================================================================
theme.aura_logo_sidebar()

with st.sidebar:
    pagina = option_menu(
        menu_title=None,
        options=[
            "Visão Geral",
            "Lixiviação",
            "TQ's 1045",
            "Acácia",
            "Eluição",
            "Eletrólise",
            "Água de Processo",
            "Detox",
            "Bullion",
        ],
        icons=[
            "speedometer2",
            "droplet-half",
            "database-fill",
            "arrow-clockwise",
            "arrow-repeat",
            "lightning-charge-fill",
            "moisture",
            "shield-exclamation",
            "coin",
        ],
        default_index=0,
        styles={
            "container": {"padding": "0", "background-color": "transparent"},
            "icon": {"color": "#fff", "font-size": "16px"},
            "nav-link": {
                "font-size": "13.5px",
                "text-align": "left",
                "margin": "6px 10px",
                "padding": "11px 14px",
                "border-radius": "6px",
                "color": "#fff",
                "background-color": Cores.AZUL_MARINHO,
                "border": f"1px solid {Cores.AZUL_MEDIO}",
                "font-weight": "500",
                "--hover-color": Cores.CORAL_MEDIO,
            },
            "nav-link-selected": {
                "background-color": Cores.CORAL,
                "color": "#fff",
                "font-weight": "600",
                "border": f"1px solid {Cores.CORAL}",
            },
        },
    )

    # --- BOTAO DE REFRESH MANUAL ---
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    if st.sidebar.button("🔄 Atualizar dados", use_container_width=True,
                          type="primary",
                          help="Lê novos emails do laboratório (últimas 48h) e atualiza o banco."):
        with st.spinner("Coletando emails novos..."):
            try:
                from app import collector
                from datetime import datetime, timedelta
                since = datetime.now() - timedelta(days=2)
                stats = collector.run(since=since, somente_processos=None)
                st.cache_data.clear()
                st.sidebar.success(f"✅ {stats.get('ok', 0)} emails processados")
            except Exception as e:
                st.sidebar.error(f"Erro: {e}")

    # --- BOTAO DE EXPORTAR EXCEL CONSOLIDADO ---
    st.sidebar.markdown(
        f'<div style="color:#fff; font-size:11pt; font-weight:600; '
        f'margin-top:18px; margin-bottom:6px; padding-left:4px;">'
        f'📅 Período para exportar</div>',
        unsafe_allow_html=True,
    )
    hoje = date.today()
    col_de, col_ate = st.sidebar.columns(2)
    de = col_de.date_input("De", hoje - timedelta(days=30), key="exp_de",
                            format="DD/MM/YYYY")
    ate = col_ate.date_input("Até", hoje, key="exp_ate",
                              format="DD/MM/YYYY")
    try:
        excel_bytes = exporter.gerar_excel_consolidado(de, ate)
        st.sidebar.download_button(
            label="📥 Exportar Excel (todas as abas)",
            data=excel_bytes,
            file_name=f"AuraLab_Borborema_{de:%Y%m%d}_{ate:%Y%m%d}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            help="Baixa um Excel com uma aba para cada processo no período selecionado.",
        )
    except Exception as e:
        st.sidebar.caption(f"⚠️ Erro ao gerar Excel: {e}")

    # --- ULTIMA ATUALIZACAO ---
    ultima = get_estado("ultima_execucao")
    if ultima:
        try:
            ts = datetime.fromisoformat(ultima)
            agora = datetime.now()
            delta = agora - ts
            mins = int(delta.total_seconds() / 60)
            if mins < 60:
                ult_txt = f"há {mins} min"
            elif mins < 1440:
                ult_txt = f"há {mins // 60}h {mins % 60}min"
            else:
                ult_txt = ts.strftime("%d/%m %H:%M")
        except Exception:
            ult_txt = ultima[:16]
        st.sidebar.markdown(
            f'<div style="font-size:9pt; color:{Cores.CORAL_BG}; text-align:center; '
            f'padding:4px 0;">Última atualização: <strong style="color:#fff">{ult_txt}</strong></div>',
            unsafe_allow_html=True,
        )

    st.sidebar.markdown(
        f'<div style="font-size:9pt; color:{Cores.CORAL_BG}; padding:14px 12px 8px 12px; '
        f'border-top:1px solid rgba(255,255,255,0.15); margin-top:14px;">'
        '<strong style="color:#fff;">v0.2 — Fase 2:</strong><br>'
        '9 processos ativos com dados reais.<br>'
        '⏰ Coletor automático: 30 min.</div>',
        unsafe_allow_html=True,
    )


# =============================================================================
# Filtros padrao no topo da pagina
# =============================================================================
def filtros_topo() -> tuple[date, date]:
    hoje = date.today()
    col1, col2, col3, col4 = st.columns([1.5, 1.5, 1.5, 4])
    with col1:
        periodo = st.selectbox(
            "Período rápido",
            ["Hoje", "Ontem", "Últimos 7 dias", "Últimos 30 dias", "Mês atual", "Personalizado"],
            index=2,
        )
    if periodo == "Hoje":
        di, df = hoje, hoje
    elif periodo == "Ontem":
        di = df = hoje - timedelta(days=1)
    elif periodo == "Últimos 7 dias":
        di, df = hoje - timedelta(days=7), hoje
    elif periodo == "Últimos 30 dias":
        di, df = hoje - timedelta(days=30), hoje
    elif periodo == "Mês atual":
        di, df = hoje.replace(day=1), hoje
    else:
        with col2:
            di = st.date_input("Data início", hoje - timedelta(days=7),
                                format="DD/MM/YYYY")
        with col3:
            df = st.date_input("Data fim", hoje, format="DD/MM/YYYY")
    return di, df


# =============================================================================
# Helpers
# =============================================================================
def _formata_fmt(decimais: int = 3) -> str:
    """Formato de numero estilo planilha BR (virgula)."""
    return f"{{:,.{decimais}f}}"


def _df_with_units(df: pd.DataFrame, units: dict[str, str]) -> pd.DataFrame:
    """Retorna copia do DF com uma linha de unidades no topo (estilo planilha)."""
    if df.empty:
        return df
    units_row = {c: units.get(c, "") for c in df.columns}
    return pd.concat([pd.DataFrame([units_row], columns=df.columns), df], ignore_index=True)


# =============================================================================
# PAGINA: VISAO GERAL
# =============================================================================
def page_home():
    theme.header("Visão Geral")
    stats = estatisticas()

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(theme.kpi_card("Amostras totais", str(stats["total_amostras"]),
                                "no banco"), unsafe_allow_html=True)
    c2.markdown(theme.kpi_card("Finais", str(stats["finais"]),
                                "analíticos completos"), unsafe_allow_html=True)
    c3.markdown(theme.kpi_card("Preliminares", str(stats["preliminares"]),
                                "aguardando analítico"), unsafe_allow_html=True)
    c4.markdown(theme.kpi_card("Processos ativos",
                                str(len(stats["por_processo"])),
                                "com amostras"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_g, col_t = st.columns([3, 2])

    with col_g:
        theme.bloco_titulo("Distribuição por processo")
        if stats["por_processo"]:
            df_proc = pd.DataFrame(
                [(k, v) for k, v in stats["por_processo"].items()],
                columns=["Processo", "Amostras"],
            ).sort_values("Amostras", ascending=True)
            fig = px.bar(df_proc, x="Amostras", y="Processo", orientation="h",
                         color="Processo",
                         color_discrete_sequence=theme.PALETA_SERIES,
                         text="Amostras")
            fig.update_traces(textposition="outside")
            theme.grafico_layout(fig, height=320)
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    with col_t:
        theme.bloco_titulo("Resumo")
        ok = sum(1 for r in stats["ultimos_logs"] if r["status"] == "ok")
        err = sum(1 for r in stats["ultimos_logs"] if r["status"] == "erro")
        st.markdown(f"**Últimos 20 emails:** {ok} OK · {err} com erro")
        if stats["ultimos_logs"]:
            df_log = pd.DataFrame([dict(r) for r in stats["ultimos_logs"][:10]])
            df_log = df_log[["timestamp", "status", "codigo_amostra"]]
            df_log.columns = ["Quando", "Status", "Código"]
            st.dataframe(df_log, use_container_width=True, hide_index=True, height=320)

    st.markdown("---")
    theme.bloco_titulo("Últimos 20 processamentos")
    if stats["ultimos_logs"]:
        df_log = pd.DataFrame([dict(r) for r in stats["ultimos_logs"]])
        df_log = df_log[["timestamp", "status", "codigo_amostra",
                         "email_subject", "remetente_email"]]
        df_log["timestamp"] = df_log["timestamp"].apply(
            lambda v: pd.to_datetime(v).strftime("%d/%m/%Y %H:%M") if v else "")
        df_log.columns = ["Quando", "Status", "Código", "Assunto", "Remetente"]
        st.dataframe(df_log, use_container_width=True, hide_index=True)


# =============================================================================
# PAGINA: LIXIVIACAO  (Ponderacoes I, J)
# =============================================================================
def page_lixiviacao():
    theme.header("Lixiviação")
    di, dfim = filtros_topo()

    df = canonical.lixiviacao_wide(di, dfim)
    if df.empty:
        st.info("Sem amostras de Lixiviação no período selecionado.")
        return

    # KPIs
    n = len(df)
    rec_validas = df["Recuperação CIL (%)"].dropna()
    rec_media = rec_validas.mean() if not rec_validas.empty else None
    n_meta = (rec_validas >= 80).sum() if not rec_validas.empty else 0
    c1, c2, c3 = st.columns(3)
    c1.markdown(theme.kpi_card("Turnos", str(n), "no período"),
                unsafe_allow_html=True)
    c2.markdown(theme.kpi_card("Recuperação CIL média",
                                f"{rec_media:.2f}%" if rec_media is not None else "—",
                                "sólido (g/t)"), unsafe_allow_html=True)
    c3.markdown(theme.kpi_card("Turnos ≥ Meta 80%", f"{n_meta}/{len(rec_validas)}",
                                "compliant"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- LAYOUT: V3 — 50/50, tabela à esquerda e gráficos preenchendo TODO o lado direito ---
    col_t, col_g = st.columns([1, 1], gap="small")

    with col_t:
        theme.bloco_titulo("Resultados — Amostras de Turno")

        # Cabecalho PLANO, sem MultiIndex, sem grupos em cima.
        df_show = df.copy()
        df_show.columns = [
            "DATA", "TURNO",
            "ACIL Au g/t", "ACIL Au mg/L",
            "RCIL Au g/t", "RCIL Au mg/L",
            "Recuperação CIL (%)",
        ]
        sty = (
            df_show.style
            .hide(axis="index")
            .format({
                "DATA": canonical._fmt_data_br,
                "ACIL Au g/t": "{:.3f}",
                "ACIL Au mg/L": "{:.3f}",
                "RCIL Au g/t": "{:.3f}",
                "RCIL Au mg/L": "{:.3f}",
                "Recuperação CIL (%)": "{:.2f}",
            }, na_rep="")
            .set_table_styles([
                {"selector": "thead th",
                 "props": [("background-color", Cores.AZUL_MARINHO),
                           ("color", "#fff"),
                           ("font-weight", "600"),
                           ("text-align", "center"),
                           ("vertical-align", "middle"),
                           ("padding", "10px 8px"),
                           ("font-size", "10.5pt"),
                           ("border", "1px solid #fff")]},
                {"selector": "tbody td",
                 "props": [("text-align", "center"),
                           ("vertical-align", "middle"),
                           ("padding", "8px")]},
            ])
        )
        # Destaque coluna TURNO em coral suave
        sty = sty.apply(
            lambda s: [f"background-color: {Cores.CORAL_BG}; color: {Cores.AZUL_MARINHO}; font-weight: 700; text-align: center"] * len(s),
            subset=["TURNO"],
        )

        st.markdown(sty.to_html(escape=False), unsafe_allow_html=True)

    with col_g:
        theme.bloco_titulo("Au solúvel — ACIL vs RCIL")
        df_plot = df.copy()
        df_plot["X"] = df_plot["DATA"].astype(str) + " " + df_plot["TURNO"]
        # Reordenar X cronologicamente
        turno_order = {"1º": 1, "2º": 2, "3º": 3}
        df_plot["_ord"] = df_plot["DATA"].astype(str) + df_plot["TURNO"].map(turno_order).astype(str)
        df_plot = df_plot.sort_values("_ord")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_plot["X"], y=df_plot["ACIL Au mg/L"],
            name="ACIL (Alimentação)", mode="lines+markers",
            line=dict(color=Cores.AZUL_MARINHO, width=2.5),
            marker=dict(size=9, line=dict(width=1.5, color="#fff")),
            fill="tozeroy", fillcolor="rgba(45,61,112,0.08)",
        ))
        fig.add_trace(go.Scatter(
            x=df_plot["X"], y=df_plot["RCIL Au mg/L"],
            name="RCIL (Rejeito)", mode="lines+markers",
            line=dict(color=Cores.CORAL, width=2.5),
            marker=dict(size=9, line=dict(width=1.5, color="#fff")),
            fill="tozeroy", fillcolor="rgba(244,97,77,0.08)",
        ))
        fig.update_xaxes(type="category", title_text="Data + Turno")
        fig.update_yaxes(title_text="Au (mg/L)")
        theme.grafico_layout(fig, height=320)
        st.plotly_chart(fig, use_container_width=True)

        # --- Grafico Recuperacao CIL (J) ---
        theme.bloco_titulo("Recuperação CIL (sólido)")
        if not rec_validas.empty:
            df_rec = df_plot[df_plot["Recuperação CIL (%)"].notna()].copy()
            cores_barras = [
                Cores.AZUL_MARINHO if v >= 80 else Cores.CORAL
                for v in df_rec["Recuperação CIL (%)"]
            ]
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                x=df_rec["X"], y=df_rec["Recuperação CIL (%)"],
                marker_color=cores_barras,
                text=df_rec["Recuperação CIL (%)"].apply(lambda v: f"{v:.1f}%"),
                textposition="outside",
                textfont=dict(size=11, color=Cores.AZUL_MARINHO),
                hovertemplate="<b>%{x}</b><br>Recuperação: %{y:.2f}%<extra></extra>",
            ))
            # Linha de meta 80%
            fig2.add_hline(y=80, line_dash="dash", line_color=Cores.CORAL,
                            annotation_text="Meta 80%",
                            annotation_position="bottom right")
            # Eixo Y de Recuperacao CIL: 50 a 100 (escala focada na faixa de operacao)
            fig2.update_xaxes(type="category", title_text="")
            fig2.update_yaxes(title_text="Recup CIL (%)", range=[50, 100])
            theme.grafico_layout(fig2, height=280)
            fig2.update_layout(showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)


# =============================================================================
# PAGINA: ACACIA  (Ponderacoes K, L)
# =============================================================================
def page_acacia():
    theme.header("Acácia")
    di, dfim = filtros_topo()

    df = canonical.acacia_wide(di, dfim)
    if df.empty:
        st.info("Sem amostras de Acácia no período selecionado.")
        return

    # KPIs
    n_bat = df["BATELADA"].nunique()
    rica_med = df["AMOSTRA RICA"].dropna().mean() if "AMOSTRA RICA" in df else None
    rej_med = df["REJEITO ACÁCIA"].dropna().mean() if "REJEITO ACÁCIA" in df else None
    c1, c2, c3 = st.columns(3)
    c1.markdown(theme.kpi_card("Bateladas", str(n_bat), "no período"),
                unsafe_allow_html=True)
    c2.markdown(theme.kpi_card("Rica média",
                                f"{rica_med:.1f} mg/L" if rica_med else "—",
                                "Au na solução"), unsafe_allow_html=True)
    c3.markdown(theme.kpi_card("Rejeito médio",
                                f"{rej_med:.1f} g/t" if rej_med else "—",
                                "Au no rejeito"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- TABELA (K) - cabecalho mesclado em TODAS as colunas via MultiIndex ---
    theme.bloco_titulo("Resultados por batelada")

    cols_over = [c for c in df.columns if c.endswith("h") and c.replace("h", "").isdigit()]
    cols_base = [c for c in df.columns if c not in cols_over]

    # MultiIndex: super-cabecalho azul "OURO NA SOLUCAO..." cobre TODAS as colunas
    SUPER = "OURO NA SOLUÇÃO — OVER DO ACÁCIA"
    df_show = df.copy()
    df_show.columns = pd.MultiIndex.from_tuples([(SUPER, c) for c in df.columns])

    fmt = {(SUPER, c): "{:.1f}" for c in cols_over}
    fmt.update({
        (SUPER, "DATA"): canonical._fmt_data_br,
        (SUPER, "AMOSTRA RICA"): "{:.1f}",
        (SUPER, "REJEITO ACÁCIA"): "{:.1f}",
        (SUPER, "REJEITO NaCN"): "{:.2f}",
    })

    sty = (
        df_show.style
        .hide(axis="index")
        .format(fmt, na_rep="")
        .set_table_styles([
            # Super-cabecalho (nivel 0): unico, mesclado sobre todas colunas
            {"selector": "thead tr:nth-child(1) th",
             "props": [("background-color", Cores.AZUL_MARINHO),
                       ("color", "#fff"),
                       ("font-weight", "700"),
                       ("text-align", "center"),
                       ("font-size", "11pt"),
                       ("letter-spacing", "2px"),
                       ("padding", "10px 6px"),
                       ("border", "2px solid #fff")]},
            # Subcabecalho (nivel 1): nomes das colunas
            {"selector": "thead tr:nth-child(2) th",
             "props": [("background-color", "#3a4970"),
                       ("color", "#fff"),
                       ("font-weight", "500"),
                       ("text-align", "center"),
                       ("font-size", "10pt"),
                       ("padding", "7px 6px")]},
        ])
    )
    # Coluna BATELADA destacada em coral
    sty = sty.apply(
        lambda s: [f"background-color: {Cores.CORAL_BG}; color: {Cores.AZUL_MARINHO}; font-weight: 700; text-align: center"] * len(s),
        subset=[(SUPER, "BATELADA")],
    )

    st.markdown(sty.to_html(escape=False), unsafe_allow_html=True)

    # --- L: 2 GRAFICOS SEPARADOS ---
    st.markdown("---")
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        theme.bloco_titulo("Tendência — Amostra Rica")
        if "AMOSTRA RICA" in df.columns:
            df_r = df.dropna(subset=["AMOSTRA RICA"]).sort_values("DATA")
            if not df_r.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_r["DATA"], y=df_r["AMOSTRA RICA"],
                    mode="lines+markers",
                    line=dict(color=Cores.AZUL_MARINHO, width=2.5),
                    marker=dict(size=10, line=dict(width=1.5, color="#fff")),
                    fill="tozeroy", fillcolor="rgba(45,61,112,0.10)",
                    name="Rica",
                    hovertemplate="<b>%{x}</b><br>Rica: %{y:.2f} mg/L<extra></extra>",
                ))
                fig.update_yaxes(title_text="Au (mg/L)")
                fig.update_xaxes(title_text="Data")
                theme.grafico_layout(fig, height=320)
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.caption("Sem dados de Rica no período.")

    with col_g2:
        theme.bloco_titulo("Tendência — Rejeito Acácia")
        if "REJEITO ACÁCIA" in df.columns:
            df_rej = df.dropna(subset=["REJEITO ACÁCIA"]).sort_values("DATA")
            if not df_rej.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_rej["DATA"], y=df_rej["REJEITO ACÁCIA"],
                    mode="lines+markers",
                    line=dict(color=Cores.CORAL, width=2.5),
                    marker=dict(size=10, line=dict(width=1.5, color="#fff")),
                    fill="tozeroy", fillcolor="rgba(244,97,77,0.10)",
                    name="Rejeito",
                    hovertemplate="<b>%{x}</b><br>Rejeito: %{y:.2f} g/t<extra></extra>",
                ))
                fig.update_yaxes(title_text="Au (g/t)")
                fig.update_xaxes(title_text="Data")
                theme.grafico_layout(fig, height=320)
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.caption("Sem dados de Rejeito no período.")

    # --- Heatmap Over (ja existia, mantido) ---
    if cols_over:
        st.markdown("---")
        theme.bloco_titulo("Over do Acácia — perfil horário (heatmap das últimas bateladas)")
        n_show = min(10, len(df))
        df_h = df.tail(n_show).copy()
        z = df_h[cols_over].values
        fig = go.Figure(data=go.Heatmap(
            z=z,
            x=cols_over,
            y=df_h["BATELADA"].astype(str),
            colorscale=[[0, Cores.AZUL_BG], [0.5, Cores.AZUL_MEDIO],
                        [1, Cores.AZUL_MARINHO]],
            colorbar=dict(title="Au (mg/L)"),
            hoverongaps=False,
            hovertemplate="Batelada %{y} - %{x}<br>Au: %{z:.1f} mg/L<extra></extra>",
        ))
        fig.update_xaxes(title_text="Hora")
        fig.update_yaxes(title_text="Batelada")
        theme.grafico_layout(fig, height=340)
        st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# PAGINA: ELETROLISE  (Ponderacao M)
# =============================================================================
def page_eletrolise():
    theme.header("Eletrólise")
    di, dfim = filtros_topo()

    # Pega contagens basicas
    with get_conn() as conn:
        df_amostras = pd.read_sql_query("""
            SELECT subcategoria, batelada, status FROM amostras
            WHERE processo = 'ELETROLISE'
              AND date(data_amostra) BETWEEN ? AND ?
        """, conn, params=(di.isoformat(), dfim.isoformat()))

    if df_amostras.empty:
        st.info("Sem amostras de Eletrólise no período selecionado.")
        return

    ce1 = (df_amostras["subcategoria"] == "CE0001").sum()
    ce2 = (df_amostras["subcategoria"] == "CE0002").sum()
    n_bat = df_amostras["batelada"].nunique(dropna=True)
    n_fin = (df_amostras["status"] == "final").sum()
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(theme.kpi_card("CE0001", str(int(ce1)), "amostras"),
                unsafe_allow_html=True)
    c2.markdown(theme.kpi_card("CE0002", str(int(ce2)), "amostras"),
                unsafe_allow_html=True)
    c3.markdown(theme.kpi_card("Bateladas", str(int(n_bat)), "no período"),
                unsafe_allow_html=True)
    c4.markdown(theme.kpi_card("Finais", str(int(n_fin)), "analítico"),
                unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 2 celulas, cada uma com tabela + grafico
    for ce in ["CE0001", "CE0002"]:
        df_ce = canonical.eletrolise_wide(di, dfim, ce)
        if df_ce.empty:
            continue
        theme.bloco_titulo(f"Célula {ce}")

        col_t, col_g = st.columns([3, 2])

        with col_t:
            df_show = df_ce.copy()
            sty = df_show.style.hide(axis="index").format(
                {"Au": "{:.3f}", "DATA": canonical._fmt_data_br}, na_rep=""
            ).set_table_styles([
                {"selector": "thead th",
                 "props": [("background-color", Cores.AZUL_MARINHO),
                           ("color", "#fff"),
                           ("font-weight", "600"),
                           ("text-align", "center")]},
            ])
            def _highlight_bat(s):
                return [f"background-color: {Cores.CORAL_BG}; color: {Cores.AZUL_MARINHO}; font-weight: 700"] * len(s)
            if "BATELADA" in df_show.columns:
                sty = sty.apply(_highlight_bat, subset=["BATELADA"])
            def _highlight_fluxo(v):
                if v == "Entrada":
                    return f"color: {Cores.AZUL_MARINHO}; font-weight: 600"
                elif v == "Saída":
                    return f"color: {Cores.CORAL}; font-weight: 600"
                return ""
            sty = sty.map(_highlight_fluxo, subset=["ENTRADA/SAÍDA"])
            st.dataframe(sty, use_container_width=True, hide_index=True, height=380)

        with col_g:
            df_plot = df_ce.copy()
            df_plot["X"] = (df_plot["DATA"].astype(str) + " " + df_plot["HORA DA COLETA"].astype(str))
            df_plot = df_plot.sort_values(["DATA", "HORA DA COLETA"])
            entrada = df_plot[df_plot["ENTRADA/SAÍDA"] == "Entrada"]
            saida = df_plot[df_plot["ENTRADA/SAÍDA"] == "Saída"]
            fig = go.Figure()
            if not entrada.empty:
                fig.add_trace(go.Scatter(
                    x=entrada["X"], y=entrada["Au"],
                    name="Entrada", mode="lines+markers",
                    line=dict(color=Cores.AZUL_MARINHO, width=2.5),
                    marker=dict(size=9, line=dict(width=1.5, color="#fff")),
                ))
            if not saida.empty:
                fig.add_trace(go.Scatter(
                    x=saida["X"], y=saida["Au"],
                    name="Saída", mode="lines+markers",
                    line=dict(color=Cores.CORAL, width=2.5),
                    marker=dict(size=9, line=dict(width=1.5, color="#fff")),
                ))
            fig.update_xaxes(type="category", title_text="Data + Hora", tickangle=-30)
            fig.update_yaxes(title_text="Au (mg/L)")
            theme.grafico_layout(fig, height=380)
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("---")


# =============================================================================
# PAGINA: TANQUES (TQ's 1045)
# =============================================================================
def page_tanques():
    theme.header("TQ's 1045 — Tanques de Lixiviação")
    di, dfim = filtros_topo()

    df = canonical.tanques_wide(di, dfim)
    if df.empty:
        st.info("Sem amostras de Tanques no período selecionado.")
        return

    n_amostras = len(df)
    rec_validas = df["Recup TQ-001 (%)"].dropna() if "Recup TQ-001 (%)" in df else pd.Series(dtype=float)
    rec_media = rec_validas.mean() if not rec_validas.empty else None
    c1, c2, c3 = st.columns(3)
    c1.markdown(theme.kpi_card("Amostragens", str(n_amostras), "no período"),
                unsafe_allow_html=True)
    c2.markdown(theme.kpi_card("Recup TQ-001 média",
                                f"{rec_media:.1f}%" if rec_media is not None else "—",
                                "do tanque principal"), unsafe_allow_html=True)
    c3.markdown(theme.kpi_card("Tanques monitorados",
                                str(sum(1 for c in df.columns if c.startswith("Saida TQ-"))),
                                "TQ-001 a TQ-007"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    theme.bloco_titulo("Resultados — Teor Au por tanque")
    fmt = {c: "{:.3f}" for c in df.columns if c.startswith("Entrada") or c.startswith("Saida")}
    fmt["Recup TQ-001 (%)"] = "{:.2f}"
    fmt["DATA"] = canonical._fmt_data_br
    sty = df.style.hide(axis="index").format(fmt, na_rep="").set_table_styles([
        {"selector": "thead th",
         "props": [("background-color", Cores.AZUL_MARINHO),
                   ("color", "#fff"),
                   ("font-weight", "600"),
                   ("text-align", "center")]},
    ])
    st.dataframe(sty, use_container_width=True, hide_index=True, height=450)

    # Grafico: serie temporal por tanque (saidas)
    st.markdown("---")
    theme.bloco_titulo("Série temporal — Saída por tanque")
    df_plot = df.copy()
    df_plot["X"] = df_plot["DATA"].astype(str) + " " + df_plot["HORA"]
    df_plot = df_plot.sort_values(["DATA", "HORA"])
    fig = go.Figure()
    colors = theme.PALETA_SERIES
    for i, n in enumerate(range(1, 8)):
        col = f"Saida TQ-{n:03d}"
        if col in df_plot:
            fig.add_trace(go.Scatter(
                x=df_plot["X"], y=df_plot[col],
                name=f"TQ-{n:03d}", mode="lines+markers",
                line=dict(color=colors[i % len(colors)], width=2),
                marker=dict(size=7, line=dict(width=1, color="#fff")),
            ))
    fig.update_xaxes(type="category", title_text="", tickangle=-30)
    fig.update_yaxes(title_text="Au (g/t)")
    theme.grafico_layout(fig, height=380)
    st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# PAGINA: ELUICAO
# =============================================================================
def page_eluicao():
    theme.header("Eluição")
    di, dfim = filtros_topo()

    df = canonical.eluicao_wide(di, dfim)
    if df.empty:
        st.info("Sem amostras de Eluição no período selecionado.")
        return

    n_bat = df["BATELADA"].nunique() if "BATELADA" in df else 0
    ef_validas = df["Eficiência (%)"].dropna() if "Eficiência (%)" in df else pd.Series(dtype=float)
    ef_media = ef_validas.mean() if not ef_validas.empty else None
    carregado_med = df["Au Carregado (g/t)"].dropna().mean() if "Au Carregado (g/t)" in df else None
    eluido_med = df["Au Eluído (g/t)"].dropna().mean() if "Au Eluído (g/t)" in df else None

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(theme.kpi_card("Bateladas", str(n_bat), "no período"),
                unsafe_allow_html=True)
    c2.markdown(theme.kpi_card("Carregado médio",
                                f"{carregado_med:.1f} g/t" if carregado_med else "—",
                                "Au no carvão"), unsafe_allow_html=True)
    c3.markdown(theme.kpi_card("Eluído médio",
                                f"{eluido_med:.1f} g/t" if eluido_med else "—",
                                "Au residual"), unsafe_allow_html=True)
    c4.markdown(theme.kpi_card("Eficiência média",
                                f"{ef_media:.1f}%" if ef_media is not None else "—",
                                "dessorção"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_t, col_g = st.columns([3, 2])

    with col_t:
        theme.bloco_titulo("Resultados por batelada")
        fmt = {c: "{:.2f}" for c in ["Au Carregado (g/t)", "Au Eluído (g/t)", "Eficiência (%)"]
               if c in df.columns}
        fmt["DATA"] = canonical._fmt_data_br
        sty = df.style.hide(axis="index").format(fmt, na_rep="").set_table_styles([
            {"selector": "thead th",
             "props": [("background-color", Cores.AZUL_MARINHO),
                       ("color", "#fff"), ("font-weight", "600"),
                       ("text-align", "center")]},
        ])
        if "BATELADA" in df.columns:
            sty = sty.apply(
                lambda s: [f"background-color: {Cores.CORAL_BG}; color: {Cores.AZUL_MARINHO}; font-weight: 700"] * len(s),
                subset=["BATELADA"],
            )
        st.dataframe(sty, use_container_width=True, hide_index=True, height=420)

    with col_g:
        theme.bloco_titulo("Tendência — Carregado vs Eluído")
        df_p = df.sort_values("BATELADA")
        fig = go.Figure()
        if "Au Carregado (g/t)" in df_p:
            fig.add_trace(go.Scatter(
                x=df_p["BATELADA"], y=df_p["Au Carregado (g/t)"],
                mode="lines+markers", name="Carregado",
                line=dict(color=Cores.AZUL_MARINHO, width=2.5),
                marker=dict(size=9),
            ))
        if "Au Eluído (g/t)" in df_p:
            fig.add_trace(go.Scatter(
                x=df_p["BATELADA"], y=df_p["Au Eluído (g/t)"],
                mode="lines+markers", name="Eluído",
                line=dict(color=Cores.CORAL, width=2.5),
                marker=dict(size=9),
            ))
        fig.update_xaxes(type="category", title_text="Batelada")
        fig.update_yaxes(title_text="Au (g/t)")
        theme.grafico_layout(fig, height=320)
        st.plotly_chart(fig, use_container_width=True)

        theme.bloco_titulo("Eficiência de dessorção")
        if "Eficiência (%)" in df.columns and df["Eficiência (%)"].notna().any():
            df_e = df.dropna(subset=["Eficiência (%)"]).sort_values("BATELADA")
            cores_b = [Cores.AZUL_MARINHO if v >= 80 else Cores.CORAL
                        for v in df_e["Eficiência (%)"]]
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                x=df_e["BATELADA"], y=df_e["Eficiência (%)"],
                marker_color=cores_b,
                text=df_e["Eficiência (%)"].apply(lambda v: f"{v:.0f}%"),
                textposition="outside",
            ))
            fig2.add_hline(y=80, line_dash="dash", line_color=Cores.CORAL,
                            annotation_text="Meta 80%")
            fig2.update_xaxes(type="category", title_text="Batelada")
            fig2.update_yaxes(title_text="Eficiência (%)", range=[0, 100])
            theme.grafico_layout(fig2, height=280)
            fig2.update_layout(showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)


# =============================================================================
# PAGINA: AGUA DE PROCESSO
# =============================================================================
def page_agua_processo():
    theme.header("Água de Processo")
    di, dfim = filtros_topo()

    df = canonical.agua_processo_wide(di, dfim)
    if df.empty:
        st.info("Sem amostras de Água de Processo no período selecionado.")
        return

    cols_hora = [c for c in df.columns if c != "DATA"]
    n_dias = df["DATA"].nunique()
    n_medicoes = int(df[cols_hora].notna().sum().sum())
    media = df[cols_hora].stack().mean() if cols_hora else None

    c1, c2, c3 = st.columns(3)
    c1.markdown(theme.kpi_card("Dias amostrados", str(n_dias), "no período"),
                unsafe_allow_html=True)
    c2.markdown(theme.kpi_card("Medições", str(n_medicoes), "Au mg/L"),
                unsafe_allow_html=True)
    c3.markdown(theme.kpi_card("Au médio",
                                f"{media:.3f} mg/L" if media is not None else "—",
                                "no período"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    theme.bloco_titulo("Matriz dia × hora — Au (mg/L)")
    fmt = {c: "{:.3f}" for c in cols_hora}
    fmt["DATA"] = canonical._fmt_data_br
    sty = df.style.hide(axis="index").format(fmt, na_rep="").set_table_styles([
        {"selector": "thead th",
         "props": [("background-color", Cores.AZUL_MARINHO),
                   ("color", "#fff"), ("font-weight", "600"),
                   ("text-align", "center")]},
    ])
    st.dataframe(sty, use_container_width=True, hide_index=True, height=400)

    # Heatmap
    st.markdown("---")
    theme.bloco_titulo("Heatmap dia × hora")
    df_h = df.set_index("DATA")[cols_hora]
    fig = go.Figure(data=go.Heatmap(
        z=df_h.values,
        x=df_h.columns,
        y=df_h.index.astype(str),
        colorscale=[[0, Cores.AZUL_BG], [0.5, Cores.AZUL_MEDIO], [1, Cores.AZUL_MARINHO]],
        colorbar=dict(title="Au (mg/L)"),
        hoverongaps=False,
    ))
    fig.update_xaxes(title_text="Hora")
    fig.update_yaxes(title_text="Data")
    theme.grafico_layout(fig, height=380)
    st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# PAGINA: DETOX
# =============================================================================
def page_detox():
    theme.header("Detox")
    di, dfim = filtros_topo()

    df = canonical.detox_wide(di, dfim)
    if df.empty:
        st.info("Sem amostras de Detox no período selecionado.")
        return

    abat_validos = df["Abatimento (%)"].dropna() if "Abatimento (%)" in df else pd.Series(dtype=float)
    abat_medio = abat_validos.mean() if not abat_validos.empty else None
    n_amostras = len(df)
    n_wad = (df["Subcategoria"] == "Cianeto WAD").sum() if "Subcategoria" in df else 0

    c1, c2, c3 = st.columns(3)
    c1.markdown(theme.kpi_card("Amostragens", str(n_amostras), "no período"),
                unsafe_allow_html=True)
    c2.markdown(theme.kpi_card("Cianeto WAD", str(int(n_wad)), "análises"),
                unsafe_allow_html=True)
    c3.markdown(theme.kpi_card("Abatimento médio",
                                f"{abat_medio:.1f}%" if abat_medio is not None else "—",
                                "destruição CN"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_t, col_g = st.columns([3, 2])

    with col_t:
        theme.bloco_titulo("Resultados Cianetos WAD e Livre")
        fmt = {c: "{:.2f}" for c in
               ["Entrada DETOX (mg/L)", "Saída DETOX (mg/L)", "Abatimento (%)"]
               if c in df.columns}
        fmt["DATA"] = canonical._fmt_data_br
        sty = df.style.hide(axis="index").format(fmt, na_rep="").set_table_styles([
            {"selector": "thead th",
             "props": [("background-color", Cores.AZUL_MARINHO),
                       ("color", "#fff"), ("font-weight", "600"),
                       ("text-align", "center")]},
        ])
        st.dataframe(sty, use_container_width=True, hide_index=True, height=420)

    with col_g:
        theme.bloco_titulo("Tendência — CN WAD entrada vs saída")
        df_p = df.dropna(subset=["Entrada DETOX (mg/L)"], how="any").sort_values("DATA")
        fig = go.Figure()
        if "Entrada DETOX (mg/L)" in df_p:
            fig.add_trace(go.Scatter(
                x=df_p["DATA"], y=df_p["Entrada DETOX (mg/L)"],
                mode="lines+markers", name="Entrada",
                line=dict(color=Cores.AZUL_MARINHO, width=2.5),
                marker=dict(size=10),
            ))
        if "Saída DETOX (mg/L)" in df_p:
            fig.add_trace(go.Scatter(
                x=df_p["DATA"], y=df_p["Saída DETOX (mg/L)"],
                mode="lines+markers", name="Saída",
                line=dict(color=Cores.CORAL, width=2.5),
                marker=dict(size=10),
            ))
        fig.update_yaxes(title_text="CN (mg/L)")
        theme.grafico_layout(fig, height=380)
        st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# PAGINA: BULLION
# =============================================================================
def page_bullion():
    theme.header("Bullion")
    di, dfim = filtros_topo()

    df = canonical.bullion_wide(di, dfim)
    if df.empty:
        st.info("Sem amostras de Bullion no período selecionado.")
        return

    n_barras = len(df)
    n_g = (df["Origem"] == "Gravimetria").sum() if "Origem" in df else 0
    n_h = (df["Origem"] == "Hidrometalurgia").sum() if "Origem" in df else 0
    au_med = df["Au (%)"].dropna().mean() if "Au (%)" in df else None
    ag_med = df["Ag (%)"].dropna().mean() if "Ag (%)" in df else None

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(theme.kpi_card("Barras", str(n_barras), "fundidas"),
                unsafe_allow_html=True)
    c2.markdown(theme.kpi_card("Gravimetria / Hidromet.", f"{n_g} / {n_h}",
                                "origem das barras"), unsafe_allow_html=True)
    c3.markdown(theme.kpi_card("Au médio",
                                f"{au_med:.2f}%" if au_med is not None else "—",
                                "teor de ouro"), unsafe_allow_html=True)
    c4.markdown(theme.kpi_card("Ag médio",
                                f"{ag_med:.2f}%" if ag_med is not None else "—",
                                "teor de prata"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_t, col_g = st.columns([3, 2])

    with col_t:
        theme.bloco_titulo("Barras fundidas")
        fmt = {"Au (%)": "{:.2f}", "Ag (%)": "{:.2f}", "DATA": canonical._fmt_data_br}
        sty = df.style.hide(axis="index").format(fmt, na_rep="").set_table_styles([
            {"selector": "thead th",
             "props": [("background-color", Cores.AZUL_MARINHO),
                       ("color", "#fff"), ("font-weight", "600"),
                       ("text-align", "center")]},
        ])
        def _origem_color(v):
            if v == "Gravimetria":
                return f"background-color: {Cores.AZUL_BG}; color: {Cores.AZUL_MARINHO}; font-weight: 600"
            elif v == "Hidrometalurgia":
                return f"background-color: {Cores.CORAL_BG}; color: {Cores.CORAL}; font-weight: 600"
            return ""
        if "Origem" in df.columns:
            sty = sty.map(_origem_color, subset=["Origem"])
        st.dataframe(sty, use_container_width=True, hide_index=True, height=420)

    with col_g:
        # --- Grafico 1: Gravimetria ---
        df_grav = df[df["Origem"] == "Gravimetria"].sort_values("ID Externo")
        theme.bloco_titulo("Au % — Gravimetria (GBBR)")
        if not df_grav.empty:
            fig_g = go.Figure()
            fig_g.add_trace(go.Bar(
                x=df_grav["ID Externo"], y=df_grav["Au (%)"],
                name="Gravimetria", marker_color=Cores.AZUL_MARINHO,
                text=df_grav["Au (%)"].apply(lambda v: f"{v:.1f}%"),
                textposition="outside",
                textfont=dict(size=10, color=Cores.AZUL_MARINHO),
            ))
            fig_g.update_xaxes(type="category", title_text="ID Externo", tickangle=-30)
            fig_g.update_yaxes(title_text="Au (%)", range=[0, 100])
            theme.grafico_layout(fig_g, height=300)
            fig_g.update_layout(showlegend=False)
            st.plotly_chart(fig_g, use_container_width=True)
        else:
            st.caption("Sem barras de Gravimetria no período.")

        # --- Grafico 2: Hidrometalurgia ---
        df_hidro = df[df["Origem"] == "Hidrometalurgia"].sort_values("ID Externo")
        theme.bloco_titulo("Au % — Hidrometalurgia (HBBR)")
        if not df_hidro.empty:
            fig_h = go.Figure()
            fig_h.add_trace(go.Bar(
                x=df_hidro["ID Externo"], y=df_hidro["Au (%)"],
                name="Hidrometalurgia", marker_color=Cores.CORAL,
                text=df_hidro["Au (%)"].apply(lambda v: f"{v:.1f}%"),
                textposition="outside",
                textfont=dict(size=10, color=Cores.CORAL),
            ))
            fig_h.update_xaxes(type="category", title_text="ID Externo", tickangle=-30)
            fig_h.update_yaxes(title_text="Au (%)", range=[0, 100])
            theme.grafico_layout(fig_h, height=300)
            fig_h.update_layout(showlegend=False)
            st.plotly_chart(fig_h, use_container_width=True)
        else:
            st.caption("Sem barras de Hidrometalurgia no período.")


# =============================================================================
# PAGINA: ADMINISTRACAO (gerenciamento de usuarios)
# =============================================================================
def page_admin():
    theme.header("Administração — Usuários")

    import bcrypt as _bcrypt_check
    # Lista usuarios cadastrados
    with get_conn() as conn:
        df_u = pd.read_sql_query("""
            SELECT username, nome_completo, email, perfil, ativo, criado_em
            FROM usuarios ORDER BY criado_em DESC
        """, conn)

    c1, c2, c3 = st.columns(3)
    c1.markdown(theme.kpi_card("Usuários", str(len(df_u)), "cadastrados"),
                unsafe_allow_html=True)
    c2.markdown(theme.kpi_card("Admins",
                                str((df_u["perfil"] == "admin").sum() if not df_u.empty else 0),
                                "perfil administrador"), unsafe_allow_html=True)
    c3.markdown(theme.kpi_card("Ativos",
                                str((df_u["ativo"] == 1).sum() if not df_u.empty else 0),
                                "podem fazer login"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_lista, col_form = st.columns([3, 2])

    with col_lista:
        theme.bloco_titulo("Usuários cadastrados")
        if df_u.empty:
            st.info("Nenhum usuário cadastrado ainda.")
        else:
            df_show = df_u.copy()
            df_show["ativo"] = df_show["ativo"].map({1: "✅ Ativo", 0: "❌ Inativo"})
            df_show["perfil"] = df_show["perfil"].map(
                {"admin": "🔑 Admin", "user": "👤 User"}).fillna(df_show["perfil"])
            df_show["criado_em"] = df_show["criado_em"].apply(
                lambda v: pd.to_datetime(v).strftime("%d/%m/%Y") if v else "")
            df_show.columns = ["Usuário", "Nome", "Email", "Perfil", "Status", "Criado em"]
            sty = df_show.style.hide(axis="index").set_table_styles([
                {"selector": "thead th",
                 "props": [("background-color", Cores.AZUL_MARINHO),
                           ("color", "#fff"), ("font-weight", "600"),
                           ("text-align", "center"), ("padding", "8px")]},
            ])
            st.markdown(sty.to_html(escape=False), unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            theme.bloco_titulo("Desativar / Reativar")
            col_u, col_b = st.columns([3, 1])
            with col_u:
                usuario_sel = st.selectbox("Usuário",
                                            options=df_u["username"].tolist(),
                                            label_visibility="collapsed",
                                            key="admin_select_user")
            row = df_u[df_u["username"] == usuario_sel].iloc[0]
            with col_b:
                novo_status = 0 if row["ativo"] == 1 else 1
                if st.button("Desativar" if row["ativo"] == 1 else "Reativar",
                              use_container_width=True, key="admin_toggle_user"):
                    with get_conn() as conn:
                        conn.execute("UPDATE usuarios SET ativo = ? WHERE username = ?",
                                      (novo_status, usuario_sel))
                    st.success(f"Usuário {usuario_sel} atualizado.")
                    st.rerun()

    with col_form:
        theme.bloco_titulo("Adicionar usuário")
        with st.form("form_novo_usuario", clear_on_submit=True):
            novo_user = st.text_input("Usuário (login)", placeholder="ex: joao.silva")
            novo_nome = st.text_input("Nome completo")
            novo_email = st.text_input("E-mail")
            novo_perfil = st.selectbox("Perfil", ["user", "admin"])
            nova_senha = st.text_input("Senha inicial", type="password",
                                        placeholder="Mínimo 6 caracteres")
            submit = st.form_submit_button("➕ Cadastrar usuário",
                                            type="primary",
                                            use_container_width=True)
            if submit:
                if not novo_user or not novo_nome or not nova_senha:
                    st.error("Preencha usuário, nome e senha.")
                elif len(nova_senha) < 6:
                    st.error("Senha deve ter ao menos 6 caracteres.")
                else:
                    try:
                        h = _bcrypt_check.hashpw(nova_senha.encode("utf-8"),
                                                  _bcrypt_check.gensalt()).decode("utf-8")
                        with get_conn() as conn:
                            conn.execute("""
                                INSERT INTO usuarios (username, nome_completo, email, senha_hash, perfil, ativo)
                                VALUES (?, ?, ?, ?, ?, 1)
                            """, (novo_user, novo_nome, novo_email, h, novo_perfil))
                        st.success(f"Usuário '{novo_user}' criado!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")

    st.markdown("---")
    st.caption(
        "💡 **Próximo passo:** quando o app for publicado externamente "
        "(Streamlit Cloud), o login passa a ser obrigatório usando as "
        "credenciais cadastradas aqui. Por enquanto, esta tela serve para "
        "preparar a lista de usuários do time."
    )


# =============================================================================
# Dispatch
# =============================================================================
PAGINAS = {
    "Visão Geral": page_home,
    "Lixiviação": page_lixiviacao,
    "TQ's 1045": page_tanques,
    "Acácia": page_acacia,
    "Eluição": page_eluicao,
    "Eletrólise": page_eletrolise,
    "Água de Processo": page_agua_processo,
    "Detox": page_detox,
    "Bullion": page_bullion,
}

PAGINAS[pagina]()
