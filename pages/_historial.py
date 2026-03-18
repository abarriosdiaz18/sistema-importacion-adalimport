# ══════════════════════════════════════════════════════════════════════════════
# ADALIMPORT · pages/_historial.py
# Terminal de Historial — Métricas globales + lotes archivados en SQLite
# Design System v2.0 — Tipografía unificada Syne / Inter / DM Mono
# ══════════════════════════════════════════════════════════════════════════════
import streamlit as st
import sys, os, builtins as _builtins

# ── FIX sys.path: raíz + subcarpeta database/ ────────────────────────────────
_PROJECT_ROOT = getattr(_builtins, "_ADALIMPORT_ROOT",   os.getcwd())
_DB_DIR       = getattr(_builtins, "_ADALIMPORT_DB_DIR",
                        os.path.join(_PROJECT_ROOT, "database"))

for _p in (_DB_DIR, _PROJECT_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)
# ─────────────────────────────────────────────────────────────────────────────

# ── Design System — OBLIGATORIO al inicio de cada página ─────────────────────
from styles_adalimport import aplicar_estilos
aplicar_estilos()

# ── DB ────────────────────────────────────────────────────────────────────────
from db_manager import (
    obtener_todos_los_lotes,
    obtener_estadisticas_globales,
    obtener_items_de_lote,
    obtener_items_por_lote,
    inicializar_db,
)

try:
    inicializar_db()
except Exception:
    pass

# ══════════════════════════════════════════════════════════════════════════════
# ESTILOS LOCALES — Solo lo que NO está en styles_adalimport.py
# Extiende el sistema sin duplicar tokens. Hereda variables CSS del design system.
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ── KPI Grid del Historial ──────────────────────────────────────────────── */
.ada-kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 28px;
}
@media (max-width: 900px) {
    .ada-kpi-grid { grid-template-columns: repeat(2, 1fr); }
}
/* Tarjeta: hereda .kpi-card del design system, extiende con glow y barra top */
.ada-kpi-card {
    background: linear-gradient(145deg, var(--navy-md) 0%, var(--navy-lt) 100%);
    border: 1px solid rgba(184,150,62,0.18);
    border-radius: 14px;
    padding: 20px 18px 16px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.ada-kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent, var(--gold)), transparent);
    opacity: 0.7;
}
.ada-kpi-card:hover {
    border-color: rgba(184,150,62,0.38);
    box-shadow: 0 0 24px rgba(184,150,62,0.10);
}
/* Icono con glow dorado */
.ada-kpi-icon {
    font-size: 1.4rem;
    margin-bottom: 10px;
    display: block;
    filter: drop-shadow(0 0 8px rgba(184,150,62,0.4));
}
/* Label: DM Mono · mayúsculas · tracking ancho — hereda .kpi-label */
.ada-kpi-label {
    font-family: var(--font-mono) !important;
    font-size: 0.60rem;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 6px;
    display: block;
}
/* Valor: DM Mono grande — hereda .kpi-value + modificadores de color */
.ada-kpi-value {
    font-family: var(--font-mono) !important;
    font-size: 1.65rem;
    font-weight: 500;
    line-height: 1;
    display: block;
    margin-bottom: 4px;
}
.ada-kpi-value.gold  { color: var(--gold); text-shadow: 0 0 18px rgba(184,150,62,0.35); }
.ada-kpi-value.neon  { color: var(--neon); text-shadow: 0 0 18px rgba(0,230,118,0.35); }
.ada-kpi-value.white { color: var(--text); }
.ada-kpi-value.blue  { color: var(--blue); text-shadow: 0 0 14px rgba(96,165,250,0.3); }
/* Sub-label: Inter 400 · pequeño · muted */
.ada-kpi-sub {
    font-family: var(--font-body) !important;
    font-weight: 400;
    font-size: 0.68rem;
    color: var(--muted);
    display: block;
}

/* ── Section Eyebrow Header ──────────────────────────────────────────────── */
/* Usa DM Mono + Oro — consistente con .ada-eyebrow del design system */
.ada-hist-section {
    font-family: var(--font-mono) !important;
    font-size: 0.60rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--gold);
    padding: 10px 0 6px;
    border-bottom: 1px solid rgba(184,150,62,0.14);
    margin-bottom: 16px;
}

/* ── Tabla maestra — Navy/Oro, hereda .res-table del design system ───────── */
.ada-table-wrap {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid rgba(184,150,62,0.14);
    margin-bottom: 28px;
}
.ada-table {
    width: 100%;
    border-collapse: collapse;
    font-family: var(--font-body) !important;
    font-size: 0.82rem;
}
.ada-table thead tr {
    background: var(--navy-md);
}
.ada-table thead th {
    font-family: var(--font-mono) !important;
    font-size: 0.57rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--muted);
    padding: 12px 14px;
    text-align: left;
    border-bottom: 1px solid rgba(184,150,62,0.14);
    white-space: nowrap;
}
.ada-table tbody tr {
    background: var(--navy);
    transition: background 0.15s;
}
.ada-table tbody tr:nth-child(even) {
    background: var(--navy-md);
}
.ada-table tbody tr:hover {
    background: rgba(184,150,62,0.06);
}
.ada-table tbody td {
    padding: 11px 14px;
    color: var(--text-muted);
    border-bottom: 1px solid rgba(20,30,48,0.8);
    vertical-align: middle;
}
/* Modificadores de celda — hereda clases de .res-table */
.ada-table .mono  { font-family: var(--font-mono) !important; }
.ada-table .gold  { color: var(--gold); font-family: var(--font-mono) !important; }
.ada-table .neon  { color: var(--neon); font-family: var(--font-mono) !important; }
.ada-table .muted { color: var(--muted); font-size: 0.78rem; }

/* ── Badges de modo ──────────────────────────────────────────────────────── */
.ada-badge {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 20px;
    font-family: var(--font-mono) !important;
    font-size: 0.62rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    font-weight: 500;
}
.ada-badge.aereo {
    background: rgba(96,165,250,0.12);
    color: var(--blue);
    border: 1px solid rgba(96,165,250,0.25);
}
.ada-badge.maritimo {
    background: rgba(0,230,118,0.10);
    color: var(--neon);
    border: 1px solid rgba(0,230,118,0.25);
}

/* ── Pills de distribución ───────────────────────────────────────────────── */
.ada-dist-row { display: flex; gap: 10px; margin-top: 4px; flex-wrap: wrap; }
.ada-dist-pill {
    font-family: var(--font-mono) !important;
    font-size: 0.62rem;
    letter-spacing: 1px;
    padding: 3px 10px;
    border-radius: 20px;
    border: 1px solid rgba(184,150,62,0.2);
    color: var(--text-muted);
    background: rgba(255,255,255,0.03);
}

/* ── Empty State ─────────────────────────────────────────────────────────── */
.ada-empty-state {
    text-align: center;
    padding: 64px 32px;
    background: linear-gradient(145deg, var(--navy-md) 0%, var(--navy) 100%);
    border: 1px dashed rgba(184,150,62,0.22);
    border-radius: 16px;
    margin: 24px 0;
}
.ada-empty-state .ico { font-size: 3.2rem; margin-bottom: 16px; display: block; }
/* h3 ya está en Syne por el design system global */
.ada-empty-state h3 {
    font-family: var(--font-display) !important;
    color: var(--text);
    font-size: 1.1rem;
    margin-bottom: 8px;
}
.ada-empty-state p {
    font-family: var(--font-body) !important;
    font-weight: 400;
    color: var(--muted);
    font-size: 0.85rem;
    max-width: 360px;
    margin: 0 auto;
}

/* ── Info chip del lote seleccionado ─────────────────────────────────────── */
.ada-lote-info-chip {
    padding: 10px 16px;
    background: rgba(184,150,62,0.06);
    border: 1px solid rgba(184,150,62,0.18);
    border-radius: 10px;
    display: flex;
    gap: 24px;
    flex-wrap: wrap;
    align-items: center;
}
.ada-lote-info-chip .chip-id {
    font-family: var(--font-mono) !important;
    font-size: 0.72rem;
    color: var(--gold);
}
.ada-lote-info-chip .chip-fecha {
    font-family: var(--font-mono) !important;
    font-size: 0.70rem;
    color: var(--muted);
}
.ada-lote-info-chip .chip-modo {
    font-family: var(--font-body) !important;
    font-weight: 400;
    font-size: 0.72rem;
    color: var(--text-muted);
}
.ada-lote-info-chip .chip-roi {
    font-family: var(--font-mono) !important;
    font-size: 0.72rem;
    color: var(--neon);
}

/* ── Totales del lote (pie del expander) ─────────────────────────────────── */
.ada-totales-row {
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
    padding: 14px 0 4px;
    border-top: 1px solid rgba(184,150,62,0.12);
    margin-top: 4px;
}
.ada-totales-row .tot-label {
    font-family: var(--font-mono) !important;
    font-size: 0.58rem;
    letter-spacing: 2px;
    color: var(--muted);
    text-transform: uppercase;
    display: block;
    margin-bottom: 2px;
}
/* Valores monetarios en DM Mono — regla de oro del sistema */
.ada-totales-row .tot-val-gold  { font-family: var(--font-mono) !important; font-size: 1.1rem; color: var(--gold); }
.ada-totales-row .tot-val-neon  { font-family: var(--font-mono) !important; font-size: 1.1rem; color: var(--neon); }
.ada-totales-row .tot-val-blue  { font-family: var(--font-mono) !important; font-size: 1.1rem; color: var(--blue); }
.ada-totales-row .tot-val-white { font-family: var(--font-mono) !important; font-size: 1.1rem; color: var(--text); }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# HEADER DE PÁGINA — Syne (display) + Inter (body) + DM Mono (eyebrow)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div style="margin-bottom:6px">
  <span class="ada-eyebrow" style="color:var(--gold);">
    📊 HISTORIAL · BASE DE DATOS PERMANENTE
  </span>
</div>
<h2 class="ada-subtitle-white" style="margin:4px 0 4px;">
  Lotes Archivados
</h2>
<p style="font-family:var(--font-body);font-weight:400;font-size:0.82rem;
          color:var(--muted);margin:0 0 24px;">
  Métricas consolidadas de todos los lotes aprobados · SQLite local persistente
</p>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CARGAR DATOS
# ══════════════════════════════════════════════════════════════════════════════
_lotes = obtener_todos_los_lotes()
_stats = obtener_estadisticas_globales()

def _safe_lote(raw: dict) -> dict:
    """Convierte sqlite3.Row o dict parcial en dict completo con valores por defecto."""
    if not isinstance(raw, dict):
        raw = dict(raw)
    return {
        "id":              raw.get("id", 0),
        "lote_id_text":    str(raw.get("lote_id_text") or "—"),
        "fecha":           str(raw.get("fecha") or "—"),
        "courier":         str(raw.get("courier") or "—"),
        "modo":            str(raw.get("modo") or "Marítimo"),
        "origen":          str(raw.get("origen") or ""),
        "costo_flete":     float(raw.get("costo_flete") or 0),
        "inversion_total": float(raw.get("inversion_total") or 0),
        "ganancia_total":  float(raw.get("ganancia_total") or 0),
        "roi":             float(raw.get("roi") or 0),
        "notas":           str(raw.get("notas") or ""),
        "total_items":     int(raw.get("total_items") or 0),
    }

_lotes    = [_safe_lote(l) for l in _lotes]
_hay_datos = len(_lotes) > 0

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — KPIs GLOBALES
# Usa .ada-kpi-card (local) + variables del design system (--gold, --neon, etc.)
# Valores monetarios en DM Mono (.ada-kpi-value)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="ada-hist-section">▸ Métricas Globales</div>', unsafe_allow_html=True)

_inv_fmt = f"${_stats['inversion_acumulada']:,.0f}"
_gan_fmt = f"${_stats['ganancia_acumulada']:,.0f}"
_roi_fmt = f"{_stats['roi_promedio']:.1f}%"

_aereo_n   = _stats.get("lotes_aereo", 0)
_mar_n     = _stats.get("lotes_maritimo", 0)
_dist_html = f"""
<div class="ada-dist-row">
  <span class="ada-dist-pill">✈ Aéreo: {_aereo_n}</span>
  <span class="ada-dist-pill">🚢 Marítimo: {_mar_n}</span>
</div>"""

# KPI grid — 4 tarjetas con valores en DM Mono y sub-labels en Inter 400
st.markdown(f"""
<div class="ada-kpi-grid">

  <!-- Total Lotes -->
  <div class="ada-kpi-card" style="--accent:var(--gold)">
    <span class="ada-kpi-icon">📦</span>
    <span class="ada-kpi-label">Total Lotes</span>
    <span class="ada-kpi-value white">{_stats['total_lotes']}</span>
    <span class="ada-kpi-sub">{_stats['total_items']} ítems totales</span>
    {_dist_html}
  </div>

  <!-- Inversión Acumulada — valor monetario en DM Mono, clase .gold -->
  <div class="ada-kpi-card" style="--accent:var(--gold)">
    <span class="ada-kpi-icon">💰</span>
    <span class="ada-kpi-label">Inversión Acumulada</span>
    <span class="ada-kpi-value gold">{_inv_fmt}</span>
    <span class="ada-kpi-sub">costo total histórico</span>
  </div>

  <!-- Ganancia Acumulada — valor en Verde Neón (éxito) -->
  <div class="ada-kpi-card" style="--accent:var(--neon)">
    <span class="ada-kpi-icon">📈</span>
    <span class="ada-kpi-label">Ganancia Acumulada</span>
    <span class="ada-kpi-value neon">{_gan_fmt}</span>
    <span class="ada-kpi-sub">ganancia neta proyectada</span>
  </div>

  <!-- ROI Promedio — azul informativo -->
  <div class="ada-kpi-card" style="--accent:var(--blue)">
    <span class="ada-kpi-icon">🎯</span>
    <span class="ada-kpi-label">ROI Promedio</span>
    <span class="ada-kpi-value blue">{_roi_fmt}</span>
    <span class="ada-kpi-sub">promedio sobre todos los lotes</span>
  </div>

</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ESTADO VACÍO
# ══════════════════════════════════════════════════════════════════════════════
if not _hay_datos:
    st.markdown("""
    <div class="ada-empty-state">
      <span class="ico">🗄️</span>
      <h3>Aún no hay lotes archivados</h3>
      <p>Los lotes aprobados en la pestaña <strong style="color:var(--gold)">LOTE</strong>
         quedan almacenados aquí de forma permanente.<br>
         Aprueba tu primer análisis para verlo reflejado en este historial.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — TABLA MAESTRA DE LOTES
# Usa st.dataframe() — los th/td ya están estilizados en el design system global
# (div[data-testid="stDataFrame"] th/td → DM Mono)
# ══════════════════════════════════════════════════════════════════════════════
import pandas as pd

st.markdown('<div class="ada-hist-section">▸ Tabla Maestra de Lotes</div>', unsafe_allow_html=True)

# ── Filtro por prefijo AER / MAR — ahora que la nomenclatura es estándar ─────
_col_filt1, _col_filt2, _col_filt3 = st.columns([1, 1, 2])
with _col_filt1:
    _filtro_modo = st.selectbox(
        "Filtrar por modo",
        ["Todos", "✈️ Aéreo (AER-)", "🚢 Marítimo (MAR-)"],
        key="hist_filtro_modo",
        label_visibility="visible",
    )
with _col_filt2:
    _couriers_disponibles = sorted(set(_l.get("courier","—") for _l in _lotes if _l.get("courier")))
    _filtro_courier = st.selectbox(
        "Filtrar por courier",
        ["Todos"] + _couriers_disponibles,
        key="hist_filtro_courier",
        label_visibility="visible",
    )

# Aplicar filtros
_lotes_filtrados = _lotes
if _filtro_modo == "✈️ Aéreo (AER-)":
    _lotes_filtrados = [l for l in _lotes_filtrados
                        if str(l.get("lote_id_text","")).startswith("AER-") or l.get("modo") == "Aéreo"]
elif _filtro_modo == "🚢 Marítimo (MAR-)":
    _lotes_filtrados = [l for l in _lotes_filtrados
                        if str(l.get("lote_id_text","")).startswith("MAR-") or l.get("modo") == "Marítimo"]
if _filtro_courier != "Todos":
    _lotes_filtrados = [l for l in _lotes_filtrados if l.get("courier") == _filtro_courier]

# Badge de conteo de resultados — DM Mono
_n_filtrados = len(_lotes_filtrados)
_n_total     = len(_lotes)
if _n_filtrados < _n_total:
    st.markdown(
        f'<span style="font-family:var(--font-mono);font-size:0.68rem;'
        f'color:var(--gold);letter-spacing:1px;">'
        f'Mostrando {_n_filtrados} de {_n_total} lotes</span>',
        unsafe_allow_html=True,
    )

_origen_map = {"us": "🇺🇸  USA", "cn": "🇨🇳  China", "": "—"}

_rows_maestra = []
for _l in _lotes_filtrados:
    _modo_str   = ("✈ Aéreo" if _l["modo"] == "Aéreo" else "🚢 Marítimo")
    _origen_str = _origen_map.get(_l.get("origen", ""), _l.get("origen", "—"))
    _rows_maestra.append({
        "Lote ID":    _l["lote_id_text"],
        "Fecha":      _l["fecha"],
        "Courier":    _l.get("courier", "—"),
        "Origen":     _origen_str,
        "Modo":       _modo_str,
        "Ítems":      int(_l.get("total_items", 0)),
        "Inversión":  round(_l["inversion_total"], 2),
        "Ganancia":   round(_l["ganancia_total"],  2),
        "ROI %":      round(_l["roi"], 1),
    })

_df_maestra = pd.DataFrame(_rows_maestra)

if _df_maestra.empty:
    st.markdown("""
    <div style="font-family:var(--font-body);font-weight:400;font-size:0.85rem;
                color:var(--muted);text-align:center;padding:24px;
                border:1px dashed rgba(184,150,62,0.18);border-radius:10px;margin:8px 0 20px;">
        📭 No hay lotes que coincidan con los filtros seleccionados.
    </div>""", unsafe_allow_html=True)
else:
    st.dataframe(
    _df_maestra,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Lote ID":   st.column_config.TextColumn("Lote ID",   width="small"),
        "Fecha":     st.column_config.TextColumn("Fecha",     width="small"),
        "Courier":   st.column_config.TextColumn("Courier",   width="medium"),
        "Origen":    st.column_config.TextColumn("Origen",    width="small"),
        "Modo":      st.column_config.TextColumn("Modo",      width="small"),
        "Ítems":     st.column_config.NumberColumn("Ítems",   width="small",  format="%d"),
        "Inversión": st.column_config.NumberColumn("Inversión $", width="small",  format="$%.2f"),
        "Ganancia":  st.column_config.NumberColumn("Ganancia $",  width="small",  format="$%.2f"),
        "ROI %":     st.column_config.ProgressColumn(
                         "ROI %",
                         width="medium",
                         format="%.1f%%",
                         min_value=0,
                         max_value=max((_l["roi"] for _l in _lotes_filtrados), default=100) * 1.2 or 100,
                     ),
    },
    )

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 — VISOR DE DETALLE POR LOTE
# Siempre muestra todos los lotes (sin filtro) para acceso directo al detalle
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="ada-hist-section">▸ Visor de Detalle por Lote</div>', unsafe_allow_html=True)

_opciones_lote = [_l["lote_id_text"] for _l in _lotes]  # todos, sin filtro

_col_sel, _col_info = st.columns([2, 3])
with _col_sel:
    _lote_sel = st.selectbox(
        "Seleccionar Lote",
        options=_opciones_lote,
        index=0,
        help="Elige un lote para ver el detalle completo de sus ítems",
        label_visibility="collapsed",
    )

_lote_header = next((l for l in _lotes if l["lote_id_text"] == _lote_sel), None)

if _lote_header:
    with _col_info:
        _modo_i = "✈ Aéreo" if _lote_header["modo"] == "Aéreo" else "🚢 Marítimo"
        # Info chip — fuentes Inter (texto) y DM Mono (IDs y valores)
        st.markdown(f"""
        <div class="ada-lote-info-chip">
          <span class="chip-id">{_lote_header['lote_id_text']}</span>
          <span class="chip-fecha">📅 {_lote_header['fecha']}</span>
          <span class="chip-modo">{_modo_i} · {_lote_header.get('courier','—')}</span>
          <span class="chip-roi">ROI {_lote_header['roi']:.1f}%</span>
        </div>
        """, unsafe_allow_html=True)

st.markdown('<div style="margin-top:12px"></div>', unsafe_allow_html=True)

def _safe_item(raw: dict) -> dict:
    """Normaliza un ítem de BD con valores por defecto para evitar KeyError/AttributeError."""
    if not isinstance(raw, dict):
        raw = dict(raw)
    return {
        "nombre":           str(raw.get("nombre") or "—"),
        "cantidad":         int(raw.get("cantidad") or 1),
        "tienda":           str(raw.get("tienda") or "—"),
        "costo_unitario":   float(raw.get("costo_unitario") or 0),
        "flete_individual": float(raw.get("flete_individual") or 0),
        "costo_real":       float(raw.get("costo_real") or 0),
        "precio_venta":     float(raw.get("precio_venta") or 0),
        "ganancia_neta":    float(raw.get("ganancia_neta") or 0),
        "margen_pct":       float(raw.get("margen_pct") or 0),
    }

_items_raw = obtener_items_de_lote(_lote_sel) if _lote_sel else []
_items = [_safe_item(it) for it in _items_raw]

with st.expander(f"📋 Ítems de {_lote_sel}  ({len(_items)} productos)", expanded=True):
    if not _items:
        st.markdown(
            '<p style="font-family:var(--font-body);font-weight:400;'
            'color:var(--muted);padding:12px 0;">'
            'Este lote no tiene ítems registrados.</p>',
            unsafe_allow_html=True,
        )
    else:
        # DataFrame de ítems — headers en DM Mono por el design system global
        _rows_items = []
        for _idx, _it in enumerate(_items, 1):
            _rows_items.append({
                "#":            _idx,
                "Producto":     _it["nombre"],
                "Qty":          int(_it["cantidad"]),
                "Tienda":       _it["tienda"],
                "Costo U.":     round(_it["costo_unitario"],   2),
                "Flete":        round(_it["flete_individual"], 2),
                "Costo Real":   round(_it["costo_real"],       2),
                "P. Venta":     round(_it["precio_venta"],     2),
                "Ganancia":     round(_it["ganancia_neta"],    2),
                "Margen %":     round(_it["margen_pct"],       1),
            })

        _df_items = pd.DataFrame(_rows_items)
        _max_gan  = max((_it["ganancia_neta"] for _it in _items), default=100) * 1.2 or 100
        _max_mar  = max((_it["margen_pct"]    for _it in _items), default=100) * 1.2 or 100

        st.dataframe(
            _df_items,
            use_container_width=True,
            hide_index=True,
            column_config={
                "#":          st.column_config.NumberColumn("#",             width="small",  format="%d"),
                "Producto":   st.column_config.TextColumn("Producto",        width="large"),
                "Qty":        st.column_config.NumberColumn("Qty",           width="small",  format="%d"),
                "Tienda":     st.column_config.TextColumn("Tienda",          width="small"),
                "Costo U.":   st.column_config.NumberColumn("Costo U. $",   width="small",  format="$%.2f"),
                "Flete":      st.column_config.NumberColumn("Flete $",       width="small",  format="$%.2f"),
                "Costo Real": st.column_config.NumberColumn("Costo Real $",  width="small",  format="$%.2f"),
                "P. Venta":   st.column_config.NumberColumn("P. Venta $",    width="small",  format="$%.2f"),
                "Ganancia":   st.column_config.ProgressColumn(
                                  "Ganancia $",
                                  width="medium",
                                  format="$%.2f",
                                  min_value=0,
                                  max_value=_max_gan,
                              ),
                "Margen %":   st.column_config.ProgressColumn(
                                  "Margen %",
                                  width="medium",
                                  format="%.1f%%",
                                  min_value=0,
                                  max_value=_max_mar,
                              ),
            },
        )

        # ── Totales del lote — valores monetarios en DM Mono (.tot-val-*) ─────
        st.markdown(f"""
        <div class="ada-totales-row">
          <div>
            <span class="tot-label">Costo Real Total</span>
            <span class="tot-val-gold">${_lote_header['inversion_total']:,.2f}</span>
          </div>
          <div>
            <span class="tot-label">Ganancia Proyectada</span>
            <span class="tot-val-neon">${_lote_header['ganancia_total']:,.2f}</span>
          </div>
          <div>
            <span class="tot-label">ROI del Lote</span>
            <span class="tot-val-blue">{_lote_header['roi']:.1f}%</span>
          </div>
          <div>
            <span class="tot-label">Total Ítems</span>
            <span class="tot-val-white">{sum(_it['cantidad'] for _it in _items)} unidades</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

# ── Footer informativo ────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:32px;padding:12px 16px;
            border-top:1px solid rgba(184,150,62,0.10);
            font-family:var(--font-mono);font-size:0.58rem;
            letter-spacing:1.5px;color:var(--muted);text-align:center;">
  ADALIMPORT · HISTORIAL · SQLite Local Persistente
</div>
""", unsafe_allow_html=True)
