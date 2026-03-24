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
#  ADALIMPORT — pages/_paso3_exportacion.py  ·  v1.0
#  Paso 3 del Pipeline Wizard — Exportación Excel para CMS Web
#
#  Responsabilidad:
#    · Consolida los resultados del Paso 1 (cálculo) con las URLs del Paso 2
#      (imágenes Supabase) y genera el Excel de importación masiva para el CMS.
#    · Ofrece 2 tipos de descarga:
#        A) Excel CMS Web  → generar_excel_importacion_web() — para Supabase/tienda
#        B) Excel Reporte  → generar_excel_reporte()         — análisis financiero
#    · Deposita "excel_bytes_cms" en session_state (contrato Paso 3).
#
#  ARCHIVO NUEVO — no reemplaza ningún existente.
#  Módulos core: exportador_reportes.py — NO SE MODIFICA.
#  Comunicación: EXCLUSIVAMENTE via st.session_state.
# ══════════════════════════════════════════════════════════════════════════════

# ── Componentes del wizard ────────────────────────────────────────────────────
try:
    from modules._wizard_nav      import render_wizard_nav, guard_prerequisito
    from modules._estado_pipeline import ESTADO_PASO
    _WIZARD_OK = True
except ImportError:
    _WIZARD_OK = False
    def render_wizard_nav(paso_actual: int) -> None: pass
    def guard_prerequisito(n: int, pagina_retroceso: str = "paso1") -> bool: return True
    class ESTADO_PASO: pass

# ── Guard de prerequisito ─────────────────────────────────────────────────────
# Paso 3 requiere: lote_id + resultados_lote
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
<div style="background:var(--navy-md);border:1px solid rgba(184,150,62,0.18);
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

    if _n_con_url < _n_total:
        _faltantes = [r.get("nombre", "")[:40] for r in _resultados_enriquecidos
                      if not r.get("image_url") and not r.get("image")]
        st.markdown(
            f'<div style="font-family:\'Inter\',sans-serif;font-size:0.78rem;'
            f'color:#B8963E;margin-top:6px;">'
            f'⚠️ {_n_total - _n_con_url} producto(s) sin URL de imagen — '
            f'puedes generar el Excel igualmente o volver al Paso 2 para procesarlas.'
            f'</div>', unsafe_allow_html=True,
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
                "lote_id":      _lote_id,
                "modo":         _modo,
                "resultados":   _resultados_enriquecidos,
                "costo_total":  _costo_total,
                "ganancia_total": _ganancia_total,
                "env_total":    _env_total,
            }
        st.session_state["_llegada_pub"]  = True
        st.session_state["pagina_activa"] = "paso4"
        st.rerun()
