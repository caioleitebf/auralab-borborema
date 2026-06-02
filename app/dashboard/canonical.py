"""Canonicalizacao: labels brutos do banco -> tabelas estruturadas conforme
planilha oficial 'Resultados Laboratorio_Oficial NOVA.xlsx'.

Aplica Ponderacoes I, K, M.
"""
from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from datetime import date, datetime, timedelta

import pandas as pd

from ..database import get_conn


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).upper()


# Lookarounds em vez de \b: \b falha em "_00:00" porque _ é word-char.
_REGEX_HORA = re.compile(r"(?<!\d)(\d{1,2}):(\d{2})(?!\d)")


def _fmt_data_br(v) -> str:
    """Converte date/datetime/string ISO para 'dd/mm/aaaa' (vazio se nao houver)."""
    if v is None:
        return ""
    try:
        return pd.to_datetime(v).strftime("%d/%m/%Y")
    except Exception:
        return str(v)


def formatar_datas_br(df: pd.DataFrame, colunas: list[str] | None = None) -> pd.DataFrame:
    """Converte colunas de data (DATA, Data, data, etc.) para string dd/mm/aaaa."""
    if df.empty:
        return df
    df = df.copy()
    if colunas is None:
        # Auto-detecta colunas que parecem ser data
        colunas = [c for c in df.columns
                   if str(c).upper() in ("DATA", "DATE")
                   or "DATA" in str(c).upper()]
    for col in colunas:
        if col in df.columns:
            df[col] = df[col].apply(_fmt_data_br)
    return df


def _hora_para_turno(hora_int: int) -> str:
    """Hora (0-23) -> turno (1o/2o/3o).

    Regra do Caio: a hora da amostra eh o FIM do turno.
      1o turno: 00h as 08h  -> amostras coletadas 01..08 = 1o
      2o turno: 08h as 16h  -> amostras coletadas 09..16 = 2o
      3o turno: 16h as 00h  -> amostras coletadas 17..23 e 00 = 3o
    """
    if hora_int == 0 or hora_int > 16:
        return "3º"
    if hora_int <= 8:
        return "1º"
    return "2º"


# =============================================================================
# LIXIVIACAO (I): 1 linha por turno consolidada
# =============================================================================
def _classifica_lixiviacao(raw_label: str) -> tuple[str, str, int] | None:
    """Retorna (fluxo, tipo_medida, hora_int) ou None.

    fluxo: 'ALIM' | 'RJT'
    tipo_medida: 'SOLIDO_g_t' | 'SOLUVEL_mg_L'  (POLPA descartado, e peso bruto)
    """
    n = _norm(raw_label)
    if "REJEITO" in n or n.startswith("REJ"):
        fluxo = "RJT"
    elif "ALIMENT" in n or "ALIM" in n:
        fluxo = "ALIM"
    else:
        return None

    if "SOLUVEL" in n:
        tipo = "SOLUVEL_mg_L"
    elif "SOLIDO" in n:
        tipo = "SOLIDO_g_t"
    else:
        # POLPA (peso bruto) e descartado para a tabela gerencial
        return None

    m = _REGEX_HORA.search(raw_label)
    if not m:
        return None
    hora = int(m.group(1))
    return fluxo, tipo, hora


def lixiviacao_wide(data_ini: date, data_fim: date) -> pd.DataFrame:
    """Tabela Lixiviacao no formato planilha oficial (USILAB-TURNO).

    Uma linha por (DATA, TURNO). Multiplos PMs de um mesmo turno se
    combinam para formar a linha completa.

    Regra de turno (Ponderacao I3): a HORA do label define o turno.
    Se a hora estiver em 16-23h e o DATE_RECEIVED for do dia seguinte
    entre 00h-08h, a DATA da amostra e o dia anterior (transicao 3o turno).
    """
    with get_conn() as conn:
        df = pd.read_sql_query("""
            SELECT a.codigo_amostra,
                   a.data_amostra,
                   a.data_recebimento_lab,
                   a.status,
                   r.raw_label,
                   r.valor,
                   r.unidade
            FROM amostras a
            JOIN resultados r ON r.codigo_amostra = a.codigo_amostra
            WHERE a.processo = 'LIXIVIACAO'
              AND date(a.data_amostra) BETWEEN ?
                                          AND date(?, '+1 day')   -- janela ampliada (3o turno cross midnight)
              AND r.valor IS NOT NULL
        """, conn, params=(data_ini.isoformat(), data_fim.isoformat()))

    if df.empty:
        return pd.DataFrame()

    # Aglutina por (data_efetiva, turno) -> dict de medidas (calcula media se houver duplicatas)
    bucket: dict[tuple[str, str], dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list))

    for _, r in df.iterrows():
        cls = _classifica_lixiviacao(r["raw_label"])
        if cls is None:
            continue
        fluxo, tipo, hora_int = cls
        turno = _hora_para_turno(hora_int)

        data_amostra = pd.to_datetime(r["data_amostra"]).date()

        # Regra de transicao de turno (I3):
        # Se turno=3 e DATE_RECEIVED esta no dia seguinte entre 00h-08h,
        # a data efetiva eh o dia anterior ao recebimento.
        if turno == "3º":
            try:
                date_recv = pd.to_datetime(r["data_recebimento_lab"])
                if date_recv is not None and not pd.isna(date_recv):
                    if 0 <= date_recv.hour < 8:
                        # Recebido madrugada -> amostra eh do dia anterior
                        candidato = (date_recv - timedelta(days=1)).date()
                        # so ajusta se faz sentido (PO_NUMBER as vezes ja eh dia anterior)
                        if abs((candidato - data_amostra).days) <= 1:
                            data_amostra = candidato
            except Exception:
                pass

        col = f"{fluxo}_{tipo}"
        bucket[(data_amostra.isoformat(), turno)][col].append(float(r["valor"]))

    out = []
    for (data_iso, turno), medidas in bucket.items():
        # Media para cada metrica (se ha varios PMs no mesmo turno)
        m = {k: (sum(v) / len(v)) if v else None for k, v in medidas.items()}
        acil_solido = m.get("ALIM_SOLIDO_g_t")
        acil_soluvel = m.get("ALIM_SOLUVEL_mg_L")
        rcil_solido = m.get("RJT_SOLIDO_g_t")
        rcil_soluvel = m.get("RJT_SOLUVEL_mg_L")

        # Recuperacao CIL = (ACIL Au g/t - RCIL Au g/t) / ACIL Au g/t * 100  -- SOLIDO
        rec = None
        if acil_solido and acil_solido > 0 and rcil_solido is not None:
            rec = (acil_solido - rcil_solido) / acil_solido * 100

        out.append({
            "DATA": data_iso,
            "TURNO": turno,
            "ACIL Au g/t": acil_solido,
            "ACIL Au mg/L": acil_soluvel,
            "RCIL Au g/t": rcil_solido,
            "RCIL Au mg/L": rcil_soluvel,
            "Recuperação CIL (%)": rec,
        })

    if not out:
        return pd.DataFrame()

    df_out = pd.DataFrame(out)
    # Filtra so o intervalo selecionado (data_ini..data_fim)
    df_out["DATA"] = pd.to_datetime(df_out["DATA"]).dt.date
    df_out = df_out[(df_out["DATA"] >= data_ini) & (df_out["DATA"] <= data_fim)]
    # Ordena por DATA desc, TURNO asc
    turno_order = {"1º": 1, "2º": 2, "3º": 3}
    df_out["_t"] = df_out["TURNO"].map(turno_order)
    df_out = df_out.sort_values(["DATA", "_t"], ascending=[False, True]).drop(columns=["_t"])
    return df_out.reset_index(drop=True)


# =============================================================================
# ACACIA (K): cabecalho agrupado, OVER 1h..16h+, BATELADA so numero
# =============================================================================
def _bat_num(batelada_str: str | None) -> int | None:
    """Extrai apenas o numero da batelada (BAT-386 -> 386)."""
    if not batelada_str:
        return None
    m = re.search(r"\d+", str(batelada_str))
    return int(m.group()) if m else None


def acacia_wide(data_ini: date, data_fim: date) -> pd.DataFrame:
    """Tabela Acacia conforme Ponderacao K.

    Colunas: BATELADA (so num) | DATA | REJEITO ACÁCIA (g/t) | REJEITO NaCN |
             AMOSTRA RICA (mg/L) | OVER 1h..Nh (mg/L)

    Uma linha por batelada. Ordem: por BATELADA crescente.
    """
    with get_conn() as conn:
        df = pd.read_sql_query("""
            SELECT a.codigo_amostra, a.data_amostra, a.status, a.batelada,
                   a.subcategoria, r.raw_label, r.valor, r.unidade, r.elemento
            FROM amostras a
            JOIN resultados r ON r.codigo_amostra = a.codigo_amostra
            WHERE a.processo = 'ACACIA'
              AND date(a.data_amostra) BETWEEN ? AND ?
              AND r.valor IS NOT NULL
            ORDER BY a.batelada, a.data_amostra
        """, conn, params=(data_ini.isoformat(), data_fim.isoformat()))

    if df.empty:
        return pd.DataFrame()

    bat_data: dict[int, dict] = defaultdict(dict)
    max_hour = 0

    for _, r in df.iterrows():
        bat_num = _bat_num(r["batelada"])
        if bat_num is None:
            # Ignora amostras sem batelada identificada (raras)
            continue

        cell = bat_data[bat_num]
        cell["BATELADA"] = bat_num
        if "DATA" not in cell:
            cell["DATA"] = pd.to_datetime(r["data_amostra"]).date()
        else:
            cell["DATA"] = max(cell["DATA"], pd.to_datetime(r["data_amostra"]).date())

        n = _norm(r["raw_label"])

        # Sol. Rica -> AMOSTRA RICA (mg/L)
        if "SOL_RICA" in n or "SOL RICA" in n or ("RICA" in n and "ACACIA" in n):
            cell["AMOSTRA RICA"] = float(r["valor"])
        # REJ_ACACIA -> REJEITO ACACIA (g/t) ou REJEITO NaCN dependendo do contexto
        elif ("REJ" in n and "ACACIA" in n) or n.startswith("REJ_ACACIA"):
            # Se o elemento eh Au e unidade g/t -> REJEITO ACACIA
            unid = _norm(r["unidade"] or "")
            if "G/T" in unid:
                cell["REJEITO ACÁCIA"] = float(r["valor"])
            elif "MG/L" in unid:
                # NaCN ou outra metrica em mg/L
                cell["REJEITO NaCN"] = float(r["valor"])
            else:
                cell["REJEITO ACÁCIA"] = float(r["valor"])
        # OVER_ACACIA_HHh:mm -> uma coluna por hora
        elif "OVER" in n:
            m = _REGEX_HORA.search(r["raw_label"])
            if m:
                hh = int(m.group(1))
                if hh > 0:                          # ignora 0h se quiser, mas mantem
                    col = f"{hh}h"
                    cell[col] = float(r["valor"])
                    max_hour = max(max_hour, hh)
                else:
                    cell["0h"] = float(r["valor"])

    if not bat_data:
        return pd.DataFrame()

    df_out = pd.DataFrame(list(bat_data.values()))

    # Define ordem de colunas
    cols_base = ["BATELADA", "DATA", "REJEITO ACÁCIA", "REJEITO NaCN", "AMOSTRA RICA"]
    cols_over = []
    if max_hour > 0:
        # detecta as horas existentes (1h..maxH)
        horas_existentes = sorted({
            int(c.replace("h", "")) for c in df_out.columns if c.endswith("h") and c.replace("h", "").isdigit()
        })
        cols_over = [f"{h}h" for h in horas_existentes]
    cols_finais = [c for c in cols_base if c in df_out.columns] + cols_over
    df_out = df_out[cols_finais]

    # Ordena por BATELADA crescente (positivos primeiro)
    df_out = df_out.sort_values("BATELADA", ascending=True).reset_index(drop=True)
    return df_out


# =============================================================================
# ELETROLISE (M): 1 linha por medicao (Data, Hora, Bat num, Entrada/Saida, Au)
# =============================================================================
# =============================================================================
# TANQUES (TQ's 1045): 1 linha por (DATA, HORA) com Au g/t por tanque
# =============================================================================
def tanques_wide(data_ini: date, data_fim: date) -> pd.DataFrame:
    """Tabela 1045-TK E e S no formato planilha oficial.

    Colunas: DATA | HORA | Au Entrada TQ-001 g/t | Au Saída TQ-001 g/t |
             Recup TQ-001 % | Au Saída TQ-002..TQ-007 g/t
    """
    with get_conn() as conn:
        df = pd.read_sql_query("""
            SELECT a.data_amostra, r.raw_label, r.valor, r.elemento, r.metodo, r.unidade
            FROM amostras a
            JOIN resultados r ON r.codigo_amostra = a.codigo_amostra
            WHERE a.processo = 'TANQUES'
              AND date(a.data_amostra) BETWEEN ? AND ?
              AND r.valor IS NOT NULL
        """, conn, params=(data_ini.isoformat(), data_fim.isoformat()))

    if df.empty:
        return pd.DataFrame()

    rows: dict[tuple, dict] = defaultdict(dict)

    for _, r in df.iterrows():
        lbl = r["raw_label"]
        n = _norm(lbl)
        # Ignora amostras de controle
        if n.startswith("OREAS") or n in ("STD", "DUP", "BLANK"):
            continue
        # Apenas SOLIDO (FAA313) interessa para Au g/t por tanque
        if "SOLIDO" not in n:
            continue
        # Identifica tanque: TQ0001, TQ0002, ... TQ0007
        m_tq = re.search(r"TQ0*(\d+)", n)
        if not m_tq:
            continue
        tq = int(m_tq.group(1))
        # Identifica fluxo
        if "ENTRADA" in n:
            fluxo = "Entrada"
        elif "SAIDA" in n or "SAÍDA" in n:
            fluxo = "Saida"
        else:
            continue
        # Hora
        m_h = _REGEX_HORA.search(lbl)
        hora = f"{int(m_h.group(1)):02d}:{m_h.group(2)}" if m_h else ""
        data_amostra = pd.to_datetime(r["data_amostra"]).date()
        key = (data_amostra, hora)

        col = f"{fluxo} TQ-{tq:03d}"
        rows[key][col] = float(r["valor"])
        rows[key]["DATA"] = data_amostra
        rows[key]["HORA"] = hora

    if not rows:
        return pd.DataFrame()
    df_out = pd.DataFrame(list(rows.values()))

    # Calcula Recuperacao TQ-001 (% = (entrada - saida) / entrada * 100)
    if "Entrada TQ-001" in df_out.columns and "Saida TQ-001" in df_out.columns:
        df_out["Recup TQ-001 (%)"] = (
            (df_out["Entrada TQ-001"] - df_out["Saida TQ-001"])
            / df_out["Entrada TQ-001"] * 100
        )

    # Ordem das colunas
    cols = ["DATA", "HORA", "Entrada TQ-001"]
    if "Saida TQ-001" in df_out.columns:
        cols += ["Saida TQ-001", "Recup TQ-001 (%)"]
    for n in range(2, 8):
        c = f"Saida TQ-{n:03d}"
        if c in df_out.columns:
            cols.append(c)
    cols = [c for c in cols if c in df_out.columns]
    df_out = df_out[cols]
    return df_out.sort_values(["DATA", "HORA"], ascending=[False, True]).reset_index(drop=True)


# =============================================================================
# ELUICAO: METAIS NO CARVÃO CARREGADO/ELUÍDO + EFICIÊNCIA
# =============================================================================
def eluicao_wide(data_ini: date, data_fim: date) -> pd.DataFrame:
    """Tabela Eluicao estilo planilha oficial (1050 - ELUICAO).

    Colunas: DATA | BATELADA | Au Carregado g/t | Au Eluído g/t | Eficiencia %
    """
    with get_conn() as conn:
        df = pd.read_sql_query("""
            SELECT a.codigo_amostra, a.data_amostra, a.batelada, a.subcategoria,
                   r.raw_label, r.valor, r.elemento, r.unidade, r.metodo
            FROM amostras a
            JOIN resultados r ON r.codigo_amostra = a.codigo_amostra
            WHERE a.processo = 'ELUICAO'
              AND date(a.data_amostra) BETWEEN ? AND ?
              AND r.valor IS NOT NULL
        """, conn, params=(data_ini.isoformat(), data_fim.isoformat()))

    if df.empty:
        return pd.DataFrame()

    bat_data: dict[int, dict] = defaultdict(dict)

    for _, r in df.iterrows():
        n = _norm(r["raw_label"])
        if n.startswith("OREAS") or n in ("STD", "DUP", "BLANK"):
            continue

        # Batelada: extrai do label "CARV_01_RICO_BAT_469" ou usa a do banco
        bat = _bat_num(r["batelada"])
        if bat is None:
            m_bat = re.search(r"BAT[_\s-]?(\d+)", n)
            if m_bat:
                bat = int(m_bat.group(1))
        if bat is None:
            continue

        # So elemento Au
        if (r["elemento"] or "").upper() not in ("AU", ""):
            continue
        unid = _norm(r["unidade"] or "")
        if "G/T" not in unid and "PPM" not in unid:
            continue

        cell = bat_data[bat]
        cell["BATELADA"] = bat
        if "DATA" not in cell:
            cell["DATA"] = pd.to_datetime(r["data_amostra"]).date()

        if "RICO" in n:
            cell["Au Carregado (g/t)"] = float(r["valor"])
        elif "ELUIDO" in n or "ELUDIO" in n:
            cell["Au Eluído (g/t)"] = float(r["valor"])

    if not bat_data:
        return pd.DataFrame()

    df_out = pd.DataFrame(list(bat_data.values()))

    # Eficiencia
    if "Au Carregado (g/t)" in df_out and "Au Eluído (g/t)" in df_out:
        df_out["Eficiência (%)"] = (
            (df_out["Au Carregado (g/t)"] - df_out["Au Eluído (g/t)"])
            / df_out["Au Carregado (g/t)"] * 100
        )

    cols = ["DATA", "BATELADA", "Au Carregado (g/t)", "Au Eluído (g/t)", "Eficiência (%)"]
    cols = [c for c in cols if c in df_out.columns]
    return df_out[cols].sort_values("BATELADA", ascending=False).reset_index(drop=True)


# =============================================================================
# AGUA DE PROCESSO: matriz dia x hora
# =============================================================================
def agua_processo_wide(data_ini: date, data_fim: date) -> pd.DataFrame:
    """Tabela Agua de Processo: matriz DATA x HORA com Au (mg/L) em cada celula."""
    with get_conn() as conn:
        df = pd.read_sql_query("""
            SELECT a.data_amostra, r.raw_label, r.valor, r.unidade
            FROM amostras a
            JOIN resultados r ON r.codigo_amostra = a.codigo_amostra
            WHERE a.processo = 'AGUA_PROCESSO'
              AND date(a.data_amostra) BETWEEN ? AND ?
              AND r.valor IS NOT NULL
        """, conn, params=(data_ini.isoformat(), data_fim.isoformat()))

    if df.empty:
        return pd.DataFrame()

    rows: dict[date, dict] = defaultdict(dict)
    for _, r in df.iterrows():
        n = _norm(r["raw_label"])
        if n.startswith("OREAS"):
            continue
        m = _REGEX_HORA.search(r["raw_label"])
        if not m:
            continue
        hh = int(m.group(1))
        col = f"{hh:02d}:00"
        data_amostra = pd.to_datetime(r["data_amostra"]).date()
        rows[data_amostra][col] = float(r["valor"])
        rows[data_amostra]["DATA"] = data_amostra

    if not rows:
        return pd.DataFrame()
    df_out = pd.DataFrame(list(rows.values()))

    # Ordena colunas de hora
    horas = sorted([c for c in df_out.columns if re.match(r"\d{2}:\d{2}", c)])
    cols = ["DATA"] + horas
    return df_out[cols].sort_values("DATA", ascending=False).reset_index(drop=True)


# =============================================================================
# DETOX: por ponto de coleta x CN Livre/WAD
# =============================================================================
def detox_wide(data_ini: date, data_fim: date) -> pd.DataFrame:
    """Tabela Detox: cada linha = 1 amostra com CN Livre e CN WAD em pontos."""
    with get_conn() as conn:
        df = pd.read_sql_query("""
            SELECT a.codigo_amostra, a.data_amostra, a.subcategoria,
                   r.raw_label, r.valor, r.elemento, r.unidade, r.metodo
            FROM amostras a
            JOIN resultados r ON r.codigo_amostra = a.codigo_amostra
            WHERE a.processo = 'DETOX'
              AND date(a.data_amostra) BETWEEN ? AND ?
              AND r.valor IS NOT NULL
        """, conn, params=(data_ini.isoformat(), data_fim.isoformat()))

    if df.empty:
        return pd.DataFrame()

    # Agrupa por (codigo_amostra) — cada PM eh uma linha
    pm_data: dict[str, dict] = defaultdict(dict)

    for _, r in df.iterrows():
        n = _norm(r["raw_label"])
        elem = _norm(r["elemento"] or "")
        unid = _norm(r["unidade"] or "")

        # So CNWAD em mg/L interessa (filtra peso bruto, NACN, %)
        if "CNWAD" not in elem and "CN" not in elem:
            continue
        if "MG/L" not in unid:
            continue

        cod = r["codigo_amostra"]
        cell = pm_data[cod]
        cell["PM"] = cod
        cell["DATA"] = pd.to_datetime(r["data_amostra"]).date()
        cell["Subcategoria"] = r["subcategoria"] or ""

        if "ALM" in n or "ENTRADA" in n:
            cell["Entrada DETOX (mg/L)"] = float(r["valor"])
        elif "SAIDA" in n:
            cell["Saída DETOX (mg/L)"] = float(r["valor"])

    if not pm_data:
        return pd.DataFrame()
    df_out = pd.DataFrame(list(pm_data.values()))

    # Abatimento %
    if "Entrada DETOX (mg/L)" in df_out and "Saída DETOX (mg/L)" in df_out:
        df_out["Abatimento (%)"] = (
            (df_out["Entrada DETOX (mg/L)"] - df_out["Saída DETOX (mg/L)"])
            / df_out["Entrada DETOX (mg/L)"] * 100
        )

    cols = ["DATA", "PM", "Subcategoria",
            "Entrada DETOX (mg/L)", "Saída DETOX (mg/L)", "Abatimento (%)"]
    cols = [c for c in cols if c in df_out.columns]
    return df_out[cols].sort_values("DATA", ascending=False).reset_index(drop=True)


# =============================================================================
# BULLION: barras com Au% e Ag% + origem (G/H)
# =============================================================================
def bullion_wide(data_ini: date, data_fim: date) -> pd.DataFrame:
    """Tabela Bullion: 1 linha por barra. Colunas: DATA | ID | Origem | Au% | Ag%."""
    with get_conn() as conn:
        df = pd.read_sql_query("""
            SELECT a.codigo_amostra, a.data_amostra,
                   r.raw_label, r.valor, r.elemento, r.unidade
            FROM amostras a
            JOIN resultados r ON r.codigo_amostra = a.codigo_amostra
            WHERE a.processo = 'BULLION'
              AND date(a.data_amostra) BETWEEN ? AND ?
              AND r.valor IS NOT NULL
        """, conn, params=(data_ini.isoformat(), data_fim.isoformat()))

    if df.empty:
        return pd.DataFrame()

    rows: dict[str, dict] = defaultdict(dict)
    for _, r in df.iterrows():
        lbl = r["raw_label"]
        # ID externo: HBBR-261, GBBR-62, etc.
        if not re.match(r"^[A-Z]{2,}-\d+$", lbl):
            continue

        # XLS do Bullion tem layout deslocado: o elemento real (Au/Ag) caiu
        # na coluna 'unidade' do banco e o metodo (FAG00_BUL) caiu em 'elemento'.
        # Usamos a coluna que de fato contem 'Au' ou 'Ag'.
        elem_candidates = [
            (r["elemento"] or "").strip(),
            (r["unidade"] or "").strip(),
        ]
        elem = next((x for x in elem_candidates if x in ("Au", "Ag")), "")

        cell = rows[lbl]
        cell["DATA"] = pd.to_datetime(r["data_amostra"]).date()
        cell["ID Externo"] = lbl
        cell["EC"] = r["codigo_amostra"]
        # Origem pelo prefixo
        if lbl.startswith("G"):
            cell["Origem"] = "Gravimetria"
        elif lbl.startswith("H"):
            cell["Origem"] = "Hidrometalurgia"
        else:
            cell["Origem"] = "Outro"

        if elem == "Au":
            cell["Au (%)"] = float(r["valor"])
        elif elem == "Ag":
            cell["Ag (%)"] = float(r["valor"])

    if not rows:
        return pd.DataFrame()
    df_out = pd.DataFrame(list(rows.values()))
    cols = ["DATA", "ID Externo", "Origem", "EC", "Au (%)", "Ag (%)"]
    cols = [c for c in cols if c in df_out.columns]
    return df_out[cols].sort_values(["DATA", "ID Externo"], ascending=[False, True]).reset_index(drop=True)


# =============================================================================
# Helper antigo (compatibilidade) — Eletrolise
# =============================================================================
def eletrolise_wide(data_ini: date, data_fim: date, celula: str) -> pd.DataFrame:
    """Tabela Eletrolise por celula no formato planilha manual.

    Colunas: DATA | HORA DA COLETA | BATELADA | ENTRADA/SAIDA | Au (mg/L)

    Uma linha por medicao do XLS (1 hora x 1 fluxo x 1 batelada).
    """
    with get_conn() as conn:
        df = pd.read_sql_query("""
            SELECT a.codigo_amostra, a.data_amostra, a.status, a.batelada,
                   a.subcategoria, r.raw_label, r.valor, r.unidade
            FROM amostras a
            JOIN resultados r ON r.codigo_amostra = a.codigo_amostra
            WHERE a.processo = 'ELETROLISE'
              AND a.subcategoria = ?
              AND date(a.data_amostra) BETWEEN ? AND ?
              AND r.valor IS NOT NULL
            ORDER BY a.data_amostra, a.codigo_amostra
        """, conn, params=(celula, data_ini.isoformat(), data_fim.isoformat()))

    if df.empty:
        return pd.DataFrame()

    rows = []
    for _, r in df.iterrows():
        n = _norm(r["raw_label"])
        if "ENTRADA" in n:
            fluxo = "Entrada"
        elif "SAIDA" in n:
            fluxo = "Saída"
        else:
            continue

        m = _REGEX_HORA.search(r["raw_label"])
        if not m:
            continue
        hora = f"{int(m.group(1)):02d}:{m.group(2)}:00"

        rows.append({
            "DATA": pd.to_datetime(r["data_amostra"]).date(),
            "HORA DA COLETA": hora,
            "BATELADA": _bat_num(r["batelada"]),
            "ENTRADA/SAÍDA": fluxo,
            "Au": float(r["valor"]),
        })

    if not rows:
        return pd.DataFrame()
    df_out = pd.DataFrame(rows)
    df_out = df_out.sort_values(
        ["DATA", "BATELADA", "HORA DA COLETA", "ENTRADA/SAÍDA"],
        ascending=[False, False, True, True],
    ).reset_index(drop=True)
    return df_out
