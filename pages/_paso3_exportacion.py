import streamlit as st
import sys, os, builtins as _builtins

# ── FIX sys.path ──────────────────────────────────────────────────────────────
_PROJECT_ROOT = getattr(_builtins, "_ADALIMPORT_ROOT",   os.getcwd())
_DB_DIR       = getattr(_builtins, "_ADALIMPORT_DB_DIR",
                        os.path.join(_PROJECT_ROOT, "database"))
for _p in (_DB_DIR, _PROJECT_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)
# ── Garantizar que modules/ esté en sys.path ──────────────────────────────────
_MODULES_DIR = os.path.join(_PROJECT_ROOT, "modules")
if _MODULES_DIR not in sys.path:
    sys.path.insert(0, _MODULES_DIR)
# ─────────────────────────────────────────────────────────────────────────────

# ══════════════════════════════════════════════════════════════════════════════
#  ADALIMPORT — pages/_paso3_exportacion.py  ·  v1.1
#  Paso 3 del Pipeline Wizard — Exportación Excel para CMS Web
#
#  v1.1 — CAMBIOS:
#    · Banner de imágenes faltantes mejorado: muestra la lista de productos
#      sin URL, nivel de riesgo (color) y botón directo "← Ir al Paso 2".
#    · El botón "Ir al Paso 2" solo aparece si el Paso 2 está habilitado
#      (lote aprobado), evitando navegación rota.
#    · Banner de éxito 100% imágenes con indicador verde neón.
#
#  Módulos core: exportador_reportes.py — NO SE MODIFICA.
#  Comunicación: EXCLUSIVAMENTE via st.session_state.
# ══════════════════════════════════════════════════════════════════════════════

# ── Componentes del wizard ────────────────────────────────────────────────────
try:
    from modules._wizard_nav      import render_wizard_nav, guard_prerequisito
    from modules._estado_pipeline import ESTADO_PASO, paso_habilitado
    _WIZARD_OK = True
except ImportError:
    _WIZARD_OK = False
    def render_wizard_nav(paso_actual: int) -> None: pass
    def guard_prerequisito(n: int, pagina_retroceso: str = "paso1") -> bool: return True
    def paso_habilitado(n: int) -> bool: return True
    ESTADO_PASO = {}

# ── Guard de prerequisito ─────────────────────────────────────────────────────
# v1.1: Paso 3 requiere: lote_id + resultados_lote + _lote_modo (contrato v1.1)
guard_prerequisito(3, pagina_retroceso="paso1")

# ── Design System ─────────────────────────────────────────────────────────────
from styles_adalimport import aplicar_estilos
aplicar_estilos()

# ── Módulo core de exportación ────────────────────────────────────────────────
try:
    from exportador_reportes import (
        generar_excel_reporte,
        generar_excel_importacion_web,
    )
    _EXPORTADOR_OK = True
except ImportError:
    _EXPORTADOR_OK = False
    def generar_excel_reporte(*a, **kw) -> bytes: return b""
    def generar_excel_importacion_web(*a, **kw) -> bytes: return b""

import copy as _copy

# ══════════════════════════════════════════════════════════════════════════════
# BARRA WIZARD
# ══════════════════════════════════════════════════════════════════════════════
render_wizard_nav(paso_actual=3)

# ══════════════════════════════════════════════════════════════════════════════
# HEADER DE PÁGINA
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div style="background:linear-gradient(135deg,rgba(13,20,36,0.9) 0%,rgba(5,9,15,0.95) 100%);
            border:1px solid rgba(184,150,62,0.2);border-top:2px solid var(--gold);
            border-radius:14px;padding:20px 24px;margin-bottom:24px;
            display:flex;align-items:center;gap:16px;">
  <span style="font-size:2rem;line-height:1;
               filter:drop-shadow(0 0 10px rgba(184,150,62,0.4));">📊</span>
  <div style="flex:1">
    <div style="font-family:'DM Mono',monospace;font-size:0.58rem;letter-spacing:3px;
                text-transform:uppercase;color:var(--gold);margin-bottom:4px;">
      Pipeline · Paso 3 de 4
    </div>
    <div style="font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:800;
                color:var(--text);line-height:1.1;margin-bottom:4px;">
      Exportación <span style="color:var(--gold);">Excel</span>
    </div>
    <div style="font-family:'Inter',sans-serif;font-size:0.82rem;color:var(--muted);">
      Consolida resultados e imágenes en un Excel listo para carga masiva en el CMS web.
      También disponible el reporte financiero completo del lote.
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# LEER DATOS DEL SESSION_STATE
# ══════════════════════════════════════════════════════════════════════════════
_resultados_raw   = st.session_state.get("resultados_lote", [])
_lote_id          = (
    st.session_state.get("lote_id")
    or st.session_state.get("_lote_id_reg")
    or st.session_state.get("lote_activo_marketing", {}).get("lote_id", "LOTE")
)
_modo             = st.session_state.get("_lote_modo", "aereo")
_costo_total      = float(st.session_state.get("_lote_costo_total", 0) or 0)
_ganancia_total   = float(st.session_state.get("_lote_ganancia",    0) or 0)
_env_total        = float(st.session_state.get("_lote_env_total",   0) or 0)
_urls_imagenes    = st.session_state.get("excel_urls_imagenes", {})   # dict {nombre: url}

# ── Calcular totales si no están en session_state (fallback) ─────────────────
if _costo_total == 0 and _resultados_raw:
    _costo_total   = sum(r.get("costo_real", 0) * r.get("cantidad", 1) for r in _resultados_raw)
if _ganancia_total == 0 and _resultados_raw:
    _ganancia_total = sum(
        r.get("ganancia_objetivo", r.get("ganancia_neta", 0)) * r.get("cantidad", 1)
        for r in _resultados_raw
    )
if _env_total == 0 and _resultados_raw:
    _env_total = sum(r.get("envio_courier", r.get("flete_proporcional", 0)) * r.get("cantidad", 1)
                     for r in _resultados_raw)

# ══════════════════════════════════════════════════════════════════════════════
# ENRIQUECER RESULTADOS CON URLs DE IMÁGENES (del Paso 2)
# ══════════════════════════════════════════════════════════════════════════════
# Hace una copia profunda para no mutar el session_state original
_resultados_enriquecidos = _copy.deepcopy(_resultados_raw)

_n_con_url = 0
for _item in _resultados_enriquecidos:
    _nombre_item = _item.get("nombre", "").strip()
    # Buscar URL por nombre exacto o coincidencia parcial
    _url_encontrada = _urls_imagenes.get(_nombre_item, "")
    if not _url_encontrada:
        # Fallback: buscar en resultados_lote directamente (ya inyectado por Paso 2)
        _url_encontrada = _item.get("imagen_url", _item.get("image_url", ""))
    if _url_encontrada:
        _item["image_url"] = _url_encontrada
        _item["image"]     = _url_encontrada
        _n_con_url += 1

_n_total   = len(_resultados_enriquecidos)
_pct_url   = int(_n_con_url / _n_total * 100) if _n_total > 0 else 0
_modo_txt  = "AÉREO ✈️" if _modo == "aereo" else "MARÍTIMO 🚢"

# ══════════════════════════════════════════════════════════════════════════════
# KPIs DEL LOTE
# ══════════════════════════════════════════════════════════════════════════════
_roi = round((_ganancia_total / _costo_total * 100) if _costo_total > 0 else 0, 1)

_k1, _k2, _k3, _k4 = st.columns(4)

_k1.markdown(f"""
<div style="background:var(--navy-md);border:1px solid rgba(184,150,62,0.18);
            border-top:2px solid var(--gold);border-radius:12px;
            padding:16px 14px;text-align:center;">
  <div style="font-family:'DM Mono',monospace;font-size:0.55rem;letter-spacing:2px;
              text-transform:uppercase;color:var(--muted);margin-bottom:6px;">Lote ID</div>
  <div style="font-family:'DM Mono',monospace;font-size:1.1rem;font-weight:700;
              color:var(--gold);">{_lote_id}</div>
  <div style="font-family:'DM Mono',monospace;font-size:0.65rem;
              color:var(--muted);margin-top:3px;">{_modo_txt}</div>
</div>""", unsafe_allow_html=True)

_k2.markdown(f"""
<div style="background:var(--navy-md);border:1px solid rgba(184,150,62,0.18);
            border-top:2px solid var(--gold);border-radius:12px;
            padding:16px 14px;text-align:center;">
  <div style="font-family:'DM Mono',monospace;font-size:0.55rem;letter-spacing:2px;
              text-transform:uppercase;color:var(--muted);margin-bottom:6px;">Inversión</div>
  <div style="font-family:'DM Mono',monospace;font-size:1.3rem;font-weight:700;
              color:var(--text);">${_costo_total:,.2f}</div>
  <div style="font-family:'DM Mono',monospace;font-size:0.65rem;
              color:var(--muted);margin-top:3px;">Flete: ${_env_total:,.2f}</div>
</div>""", unsafe_allow_html=True)

_k3.markdown(f"""
<div style="background:var(--navy-md);border:1px solid rgba(0,230,118,0.18);
            border-top:2px solid var(--neon);border-radius:12px;
            padding:16px 14px;text-align:center;">
  <div style="font-family:'DM Mono',monospace;font-size:0.55rem;letter-spacing:2px;
              text-transform:uppercase;color:var(--muted);margin-bottom:6px;">Ganancia</div>
  <div style="font-family:'DM Mono',monospace;font-size:1.3rem;font-weight:700;
              color:var(--neon);">${_ganancia_total:,.2f}</div>
  <div style="font-family:'DM Mono',monospace;font-size:0.65rem;
              color:var(--muted);margin-top:3px;">ROI: {_roi:.1f}%</div>
</div>""", unsafe_allow_html=True)

_k4.markdown(f"""
<div style="background:var(--navy-md);border:1px solid rgba({'0,230,118' if _pct_url == 100 else '184,150,62'},0.18);
            border-top:2px solid {'var(--neon)' if _pct_url == 100 else 'var(--gold)'};
            border-radius:12px;padding:16px 14px;text-align:center;">
  <div style="font-family:'DM Mono',monospace;font-size:0.55rem;letter-spacing:2px;
              text-transform:uppercase;color:var(--muted);margin-bottom:6px;">Imágenes</div>
  <div style="font-family:'DM Mono',monospace;font-size:1.3rem;font-weight:700;
              color:{'var(--neon)' if _pct_url == 100 else 'var(--gold)'};">
      {_n_con_url}/{_n_total}
  </div>
  <div style="font-family:'DM Mono',monospace;font-size:0.65rem;
              color:var(--muted);margin-top:3px;">{_pct_url}% con URL</div>
</div>""", unsafe_allow_html=True)

st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# BANNER DE ESTADO DE IMÁGENES (v1.1 — reemplaza el aviso inline del expander)
# ── Se muestra FUERA del expander para máxima visibilidad ─────────────────────
# ══════════════════════════════════════════════════════════════════════════════
_n_faltantes = _n_total - _n_con_url

if _n_faltantes > 0:
    # ── Calcular nivel de riesgo ──────────────────────────────────────────────
    # Alto  (>50% sin URL): borde rojo, no bloquea pero advierte fuerte
    # Medio (1-50% sin URL): borde oro, aviso suave
    _riesgo_alto   = _pct_url < 50
    _border_color  = "#ef4444" if _riesgo_alto else "#B8963E"
    _bg_color      = "rgba(239,68,68,0.06)" if _riesgo_alto else "rgba(184,150,62,0.06)"
    _icono         = "🔴" if _riesgo_alto else "⚠️"
    _titulo        = f"{_icono} {_n_faltantes} producto(s) sin imagen vinculada"
    _subtitulo     = (
        "El Excel CMS se generará con celdas vacías en la columna <code>image</code>. "
        "Esto puede causar errores en la carga masiva de la tienda." if _riesgo_alto
        else
        "El Excel se generará correctamente. Las celdas de imagen quedarán vacías "
        "para los productos listados abajo."
    )

    # ── Lista de productos faltantes (máx 5 visibles) ─────────────────────────
    _nombres_faltantes = [
        r.get("nombre", "—")[:48]
        for r in _resultados_enriquecidos
        if not r.get("image_url") and not r.get("image")
    ]
    _items_html = "".join(
        f'<span style="display:inline-block;background:rgba(255,255,255,0.05);'
        f'border:1px solid rgba(255,255,255,0.08);border-radius:4px;'
        f'padding:2px 8px;margin:2px 3px 2px 0;font-size:0.72rem;'
        f'font-family:\'DM Mono\',monospace;color:#94a3b8;">{n}</span>'
        for n in _nombres_faltantes[:5]
    )
    _mas_html = (
        f'<span style="font-size:0.72rem;color:#64748b;font-family:\'Inter\',sans-serif;">'
        f'  +{len(_nombres_faltantes) - 5} más...</span>'
        if len(_nombres_faltantes) > 5 else ""
    )

    # ── Verificar si Paso 2 está habilitado para mostrar botón ────────────────
    _paso2_ok = paso_habilitado(2)

    st.markdown(f"""
    <div style="background:{_bg_color};
                border:1px solid {_border_color};
                border-left:3px solid {_border_color};
                border-radius:10px;
                padding:14px 18px;
                margin-bottom:18px;">
        <div style="font-family:'Syne',sans-serif;font-size:0.92rem;font-weight:700;
                    color:{'#fca5a5' if _riesgo_alto else '#B8963E'};margin-bottom:5px;">
            {_titulo}
        </div>
        <div style="font-family:'Inter',sans-serif;font-size:0.78rem;color:#94a3b8;
                    margin-bottom:10px;">{_subtitulo}</div>
        <div style="margin-bottom:6px;">{_items_html}{_mas_html}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Botón de navegación al Paso 2 (solo si está habilitado) ──────────────
    if _paso2_ok:
        _b_col1, _b_col2, _b_col3 = st.columns([1, 2, 1])
        with _b_col2:
            if st.button(
                "🎨  ← Ir al Paso 2 para procesar imágenes",
                key="paso3_ir_paso2",
                use_container_width=True,
            ):
                st.session_state["pagina_activa"] = "paso2"
                st.rerun()
        st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

elif _n_total > 0:
    # ── Todas las imágenes vinculadas — banner de éxito ───────────────────────
    st.markdown(f"""
    <div style="background:rgba(0,230,118,0.06);
                border:1px solid rgba(0,230,118,0.3);
                border-left:3px solid #00E676;
                border-radius:10px;padding:12px 18px;margin-bottom:18px;
                display:flex;align-items:center;gap:10px;">
        <span style="font-size:1.2rem;">✅</span>
        <div>
            <span style="font-family:'Syne',sans-serif;font-size:0.88rem;font-weight:700;
                         color:#00E676;">100% de imágenes vinculadas</span>
            <span style="font-family:'Inter',sans-serif;font-size:0.78rem;color:#64748b;
                         margin-left:8px;">— El Excel incluirá URLs para todos los {_n_total} productos.</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TABLA DE PREVIEW
# ══════════════════════════════════════════════════════════════════════════════
with st.expander(f"👁️ Preview del Excel — {_n_total} producto(s)", expanded=True):
    import pandas as pd

    _filas_preview = []
    for _r in _resultados_enriquecidos:
        _precio_ml = _r.get("precio_ml_objetivo", _r.get("precio_ml", 0))
        _url_prev  = _r.get("image_url", _r.get("image", ""))
        _filas_preview.append({
            "Producto":    _r.get("nombre", "")[:55],
            "Stock":       _r.get("cantidad", 1),
            "Categoría":   _r.get("category", _r.get("categoria", "—")),
            "Precio ML":   f"${float(_precio_ml):,.2f}",
            "Costo Real":  f"${float(_r.get('costo_real', 0)):,.2f}",
            "Ganancia":    f"${float(_r.get('ganancia_objetivo', _r.get('ganancia_neta', 0))):,.2f}",
            "Decisión":    _r.get("decision", "—"),
            "URL imagen":  "✓ vinculada" if _url_prev else "— sin URL",
        })

    _df_preview = pd.DataFrame(_filas_preview)
    st.dataframe(
        _df_preview,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Precio ML":  st.column_config.TextColumn(width="small"),
            "Costo Real": st.column_config.TextColumn(width="small"),
            "Ganancia":   st.column_config.TextColumn(width="small"),
            "URL imagen": st.column_config.TextColumn(width="medium"),
        }
    )

st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
st.markdown('<hr style="border:none;border-top:1px solid #141e30;margin:0 0 1.4rem 0;">',
            unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# BOTONES DE DESCARGA
# ══════════════════════════════════════════════════════════════════════════════
if not _EXPORTADOR_OK:
    st.error("**exportador_reportes.py** no encontrado. Verifica que el módulo existe en la raíz.")
    st.stop()

_col_a, _col_b = st.columns(2)

# ── DESCARGA A: Excel CMS Web (para Supabase) ─────────────────────────────────
with _col_a:
    st.markdown("""
    <div style="background:rgba(0,230,118,0.05);border:1px solid rgba(0,230,118,0.2);
                border-radius:10px;padding:14px 16px;margin-bottom:12px;min-height:90px;">
        <div style="font-family:'DM Mono',monospace;font-size:0.62rem;letter-spacing:2px;
                    text-transform:uppercase;color:var(--neon);margin-bottom:6px;">
            ★ Principal — Importación CMS
        </div>
        <div style="font-family:'Inter',sans-serif;font-size:0.80rem;color:var(--muted);">
            Columnas: <code>lote_id · title · description · stock · category · price · image</code>
            <br>Listo para carga masiva directa en Supabase / tienda web.
        </div>
    </div>
    """, unsafe_allow_html=True)

    try:
        _bytes_cms = generar_excel_importacion_web(
            resultados=_resultados_enriquecidos,
            lote_id=_lote_id,
        )
        # Depositar en session_state (contrato Paso 3)
        st.session_state["excel_bytes_cms"] = _bytes_cms

        st.download_button(
            label="📊  Descargar Excel CMS Web",
            data=_bytes_cms,
            file_name=f"ADALIMPORT_{_lote_id}_web.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary",
            key="dl_excel_cms",
        )
    except Exception as _e_cms:
        st.error(f"Error generando Excel CMS: `{_e_cms}`")

# ── DESCARGA B: Excel Reporte Financiero ─────────────────────────────────────
with _col_b:
    st.markdown("""
    <div style="background:rgba(184,150,62,0.05);border:1px solid rgba(184,150,62,0.18);
                border-radius:10px;padding:14px 16px;margin-bottom:12px;min-height:90px;">
        <div style="font-family:'DM Mono',monospace;font-size:0.62rem;letter-spacing:2px;
                    text-transform:uppercase;color:var(--gold);margin-bottom:6px;">
            Reporte Financiero
        </div>
        <div style="font-family:'Inter',sans-serif;font-size:0.80rem;color:var(--muted);">
            Hoja <strong>Detalle</strong>: costos, fletes, márgenes por ítem.
            <br>Hoja <strong>Resumen</strong>: KPIs del lote (inversión, ROI, ganancia).
        </div>
    </div>
    """, unsafe_allow_html=True)

    try:
        _bytes_reporte = generar_excel_reporte(
            resultados=_resultados_enriquecidos,
            modo=_modo,
            lote_id=_lote_id,
            costo_total=_costo_total,
            ganancia_total=_ganancia_total,
            env_total=_env_total,
        )
        st.download_button(
            label="📈  Descargar Reporte Financiero",
            data=_bytes_reporte,
            file_name=f"ADALIMPORT_{_lote_id}_reporte.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="secondary",
            key="dl_excel_reporte",
        )
    except Exception as _e_rep:
        st.error(f"Error generando reporte: `{_e_rep}`")

# ══════════════════════════════════════════════════════════════════════════════
# BOTÓN DE CONTINUACIÓN AL PASO 4
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
st.markdown('<hr style="border:none;border-top:1px solid #141e30;margin:0 0 1.4rem 0;">',
            unsafe_allow_html=True)

st.markdown(f"""
<div style="background:rgba(184,150,62,0.05);border:1px solid rgba(184,150,62,0.18);
            border-radius:10px;padding:14px 18px;margin-bottom:16px;
            font-family:'Inter',sans-serif;font-size:0.85rem;color:#94a3b8;">
    <strong style="color:#B8963E;">Paso 3 completado.</strong>
    El Excel de importación está listo.
    El siguiente paso genera los copys (títulos, descripciones y textos)
    para MercadoLibre, Instagram y WhatsApp.
</div>
""", unsafe_allow_html=True)

_btn_c1, _btn_c2, _btn_c3 = st.columns([1, 2, 1])
with _btn_c2:
    if st.button(
        "Continuar al Paso 4 — Publicaciones  →",
        key="paso3_btn_continuar",
        type="primary",
        use_container_width=True,
    ):
        # Asegurar que lote_activo_marketing esté poblado para el Paso 4
        if not st.session_state.get("lote_activo_marketing"):
            st.session_state["lote_activo_marketing"] = {
                "lote_id":        _lote_id,
                "modo":           _modo,
                "resultados":     _resultados_enriquecidos,
                "costo_total":    _costo_total,
                "ganancia_total": _ganancia_total,
                "env_total":      _env_total,
            }
        st.session_state["_llegada_pub"]  = True
        st.session_state["pagina_activa"] = "paso4"
        st.rerun()
