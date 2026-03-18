# ══════════════════════════════════════════════════════════════════════════════
# ADALIMPORT · pages/_estudio_visual.py  ·  v3.0 (Flujo Inyector + Exportación Web)
# Estudio Visual — Generador de Imágenes Multi-plataforma
# Página atómica: no importa de otras páginas.
#
# CAMBIOS v3.0:
# · Tabs: Solo ML, Instagram Post e Instagram Story (eliminados WhatsApp y Supabase).
# · Botones de descarga específicos por pestaña.
# · Eliminados botones globales: "Abrir carpeta local", "Generar ZIP Master", "Limpiar Todo".
# · Flujo Inyector: al procesar, sube imagen ML a Supabase y actualiza automáticamente
#   st.session_state["excel_lote_en_Estudio_Visual"]["image"] con la URL pública.
# · Nueva sección "📦 Exportación Web Final" con botón de descarga del Excel .xlsx.
# ══════════════════════════════════════════════════════════════════════════════
import streamlit as st
import sys, os, builtins as _builtins

# ── FIX sys.path (mismo patrón que el resto de páginas) ──────────────────────
_PROJECT_ROOT = getattr(_builtins, "_ADALIMPORT_ROOT",   os.getcwd())
_DB_DIR       = getattr(_builtins, "_ADALIMPORT_DB_DIR",
                        os.path.join(_PROJECT_ROOT, "database"))
for _p in (_DB_DIR, _PROJECT_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── Design System ─────────────────────────────────────────────────────────────
from styles_adalimport import aplicar_estilos
aplicar_estilos()

# ── Módulo core atómico ───────────────────────────────────────────────────────
try:
    from procesador_imagenes import (
        procesar_version_catalogo,
        procesar_version_ig_post,
        procesar_version_ig_story,
        modulo_disponible,
        rembg_disponible,
        version_info,
    )
    _PROC_OK = True
except Exception as _e_proc:
    _PROC_OK = False
    def procesar_version_catalogo(_b):         return None
    def procesar_version_ig_post(_b, _p, _n):  return None
    def procesar_version_ig_story(_b, _p, _n): return None
    def modulo_disponible():                   return False
    def rembg_disponible():                    return False
    def version_info():                        return {}

# ── Módulo publicador Supabase ────────────────────────────────────────────────
try:
    from publicador_imagenes import subir_imagen_a_supabase
    _SUPA_OK = True
except Exception as _e_supa:
    _SUPA_OK = False
    def subir_imagen_a_supabase(datos_imagen, nombre_archivo): return ""

import re as _re
import io
import zipfile
from datetime import datetime
from pathlib import Path

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def _slug(texto: str, max_len: int = 45) -> str:
    s = _re.sub(r"[^a-zA-Z0-9 _\-]", "", texto).strip()
    s = _re.sub(r"\s+", "_", s)
    return s[:max_len] or "producto"

def _carpeta_salida() -> Path:
    ruta = Path(_PROJECT_ROOT) / "exports" / "imagenes"
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta

def _guardar_en_disco(bytes_img: bytes, nombre_archivo: str) -> Path:
    destino = _carpeta_salida() / nombre_archivo
    destino.write_bytes(bytes_img)
    return destino

# ── Inyector de URL en el DataFrame Web ──────────────────────────────────────
def _inyectar_url_en_excel_web(nombre_producto: str, url_publica: str) -> bool:
    """
    Busca el producto por nombre en st.session_state["excel_lote_en_Estudio_Visual"]
    y actualiza su columna 'image' con la URL pública de Supabase.
    Retorna True si el ítem fue encontrado y actualizado.
    """
    import pandas as _pd
    df = st.session_state.get("excel_lote_en_Estudio_Visual")
    if df is None or not hasattr(df, "iterrows"):
        return False
    nombre_limpio = nombre_producto.strip()
    mascara = df["nombre"].str.strip() == nombre_limpio
    if not mascara.any():
        return False
    df.loc[mascara, "image"] = url_publica
    st.session_state["excel_lote_en_Estudio_Visual"] = df
    return True

def _persistir_image_url_en_lote(nombre_producto: str, url_publica: str) -> bool:
    """
    Actualiza el campo 'image' en st.session_state['resultados_lote']
    para el producto cuyo campo 'nombre' coincide exactamente con nombre_producto.
    También actualiza lote_activo_marketing['resultados'] para consistencia total.
    Retorna True si encontró y actualizó el ítem, False si no hubo match.
    """
    resultados = st.session_state.get("resultados_lote", [])
    actualizado = False
    for item in resultados:
        if item.get("nombre", "").strip() == nombre_producto.strip():
            item["image"] = url_publica
            actualizado = True
            break

    if actualizado:
        st.session_state["resultados_lote"] = resultados
        _lam = st.session_state.get("lote_activo_marketing")
        if _lam and "resultados" in _lam:
            for item in _lam["resultados"]:
                if item.get("nombre", "").strip() == nombre_producto.strip():
                    item["image"] = url_publica
                    break
            st.session_state["lote_activo_marketing"] = _lam

    return actualizado

# ══════════════════════════════════════════════════════════════════════════════
# ESTILOS LOCALES
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
.ev-page-header { padding: 0 0 20px 0; border-bottom: 1px solid rgba(184,150,62,0.12); margin-bottom: 24px; }
.ev-eyebrow { font-family: var(--font-mono) !important; font-size: 0.58rem; letter-spacing: 4px; text-transform: uppercase; color: var(--gold); display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.ev-eyebrow::before { content: ''; display: inline-block; width: 20px; height: 1px; background: var(--gold); opacity: 0.5; }
.ev-page-title { font-family: var(--font-display) !important; font-size: 1.7rem; font-weight: 800; color: var(--text); letter-spacing: -0.5px; line-height: 1.1; margin: 0 0 6px 0; }
.ev-page-title span { color: var(--gold); }
.ev-page-desc { font-family: var(--font-body) !important; font-size: 0.82rem; color: var(--muted); margin: 0; }
.ev-prod-card { background: var(--navy-md); border: 1px solid var(--border); border-radius: 12px; padding: 16px 18px; margin-bottom: 12px; }
.ev-prod-nombre { font-family: var(--font-display) !important; font-size: 0.95rem; font-weight: 700; color: var(--text); margin: 0 0 4px 0; }
.ev-prod-meta { font-family: var(--font-mono) !important; font-size: 0.68rem; color: var(--gold); letter-spacing: 1px; }
.ev-badge-ok { display: inline-flex; align-items: center; gap: 5px; background: rgba(0,230,118,0.07); border: 1px solid rgba(0,230,118,0.25); border-radius: 20px; padding: 3px 10px; font-family: var(--font-mono) !important; font-size: 0.60rem; letter-spacing: 1.5px; text-transform: uppercase; color: var(--neon); }
.ev-badge-warn { display: inline-flex; align-items: center; gap: 5px; background: rgba(255,214,0,0.07); border: 1px solid rgba(255,214,0,0.25); border-radius: 20px; padding: 3px 10px; font-family: var(--font-mono) !important; font-size: 0.60rem; letter-spacing: 1.5px; text-transform: uppercase; color: var(--yellow); }
.ev-folder-box { background: rgba(184,150,62,0.05); border: 1px solid rgba(184,150,62,0.20); border-radius: 10px; padding: 14px 16px; margin-top: 16px; }
.ev-folder-label { font-family: var(--font-mono) !important; font-size: 0.60rem; letter-spacing: 2px; text-transform: uppercase; color: var(--gold); display: block; margin-bottom: 4px; }
.ev-folder-path { font-family: var(--font-mono) !important; font-size: 0.75rem; color: var(--text); background: rgba(0,0,0,0.25); border-radius: 5px; padding: 4px 8px; display: inline-block; margin-top: 4px; word-break: break-all; }
.ev-empty { border: 1px dashed rgba(184,150,62,0.22); border-radius: 12px; padding: 36px 20px; text-align: center; }
.ev-empty-ico { font-size: 2.4rem; display: block; margin-bottom: 10px; }
.ev-empty-title { font-family: var(--font-mono) !important; font-size: 0.72rem; letter-spacing: 2px; text-transform: uppercase; color: var(--muted); }
.ev-empty-desc { font-family: var(--font-body) !important; font-size: 0.80rem; color: rgba(200,200,200,0.35); margin-top: 6px; }
.ev-hr { border: none; border-top: 1px solid rgba(184,150,62,0.10); margin: 1.2rem 0; }
.ev-url-linked { font-family: var(--font-mono) !important; font-size: 0.68rem; color: var(--neon); background: rgba(0,230,118,0.06); border: 1px solid rgba(0,230,118,0.20); border-radius: 6px; padding: 5px 10px; display: block; word-break: break-all; margin-top: 4px; }
/* Sección Exportación Web */
.ev-export-section {
    background: linear-gradient(160deg, #0a1a1a, #061212);
    border: 2px solid rgba(184,150,62,0.35);
    border-radius: 16px;
    padding: 1.6rem 1.8rem;
    margin-top: 2rem;
}
.ev-export-eyebrow {
    font-family: var(--font-mono) !important;
    font-size: 0.58rem;
    letter-spacing: 4px;
    text-transform: uppercase;
    color: var(--gold);
    margin-bottom: 6px;
}
.ev-export-title {
    font-family: var(--font-display) !important;
    font-size: 1.2rem;
    font-weight: 800;
    color: var(--text);
    margin: 0 0 6px 0;
}
.ev-export-title span { color: var(--gold); }
.ev-export-desc {
    font-family: var(--font-body) !important;
    font-size: 0.80rem;
    color: var(--muted);
    margin: 0 0 1.2rem 0;
    line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# HEADER DE PÁGINA
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="ev-page-header">
  <div class="ev-eyebrow">🎨 PUBLICACIONES · ESTUDIO VISUAL</div>
  <h1 class="ev-page-title">Estudio <span>Visual</span></h1>
  <p class="ev-page-desc">
    Genera imágenes de catálogo (ML) e imágenes con branding (Instagram Post / Story).
    Las imágenes ML se suben automáticamente a Supabase y su URL queda vinculada al Excel de importación.
  </p>
</div>
""", unsafe_allow_html=True)

_pil_ok   = modulo_disponible()
_rembg_ok = rembg_disponible()

_col_badge1, _col_badge2, _col_badge3 = st.columns([1, 1, 3])
with _col_badge1:
    if _pil_ok: st.markdown('<span class="ev-badge-ok">✓ Pillow activo</span>', unsafe_allow_html=True)
    else: st.markdown('<span class="ev-badge-warn">✕ Pillow faltante</span>', unsafe_allow_html=True)
with _col_badge2:
    if _rembg_ok: st.markdown('<span class="ev-badge-ok">✓ rembg IA activo</span>', unsafe_allow_html=True)
    else: st.markdown('<span class="ev-badge-warn">◎ rembg opcional</span>', unsafe_allow_html=True)
with _col_badge3:
    if _SUPA_OK: st.markdown('<span class="ev-badge-ok">☁️ Supabase conectado</span>', unsafe_allow_html=True)
    else: st.markdown('<span class="ev-badge-warn">☁️ Supabase no disponible</span>', unsafe_allow_html=True)

if not _pil_ok:
    st.error("**Pillow no está instalado.** Añade `Pillow` a `requirements.txt` y reinicia la app.", icon="📦")
    st.stop()

st.markdown('<hr class="ev-hr">', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# GESTIÓN DE ESTADO (COLA Y LOTE)
# ══════════════════════════════════════════════════════════════════════════════
_lote_mkt     = st.session_state.get("lote_activo_marketing")
_resultados   = st.session_state.get("resultados_lote", [])
_tiene_lote   = bool(_lote_mkt and _resultados)

if "ev_cola" not in st.session_state:
    st.session_state["ev_cola"] = []

def _limpiar_cola():
    st.session_state["ev_cola"] = []

if _tiene_lote:
    _lote_id = _lote_mkt.get("lote_id", "—")
    st.markdown(
        f'<div style="background:rgba(0,230,118,0.06);border:1px solid rgba(0,230,118,0.20);'
        f'border-radius:8px;padding:10px 14px;margin-bottom:16px;">'
        f'<span style="font-family:var(--font-mono);font-size:0.62rem;color:var(--neon);">'
        f'● Lote activo: <strong>{_lote_id}</strong> · {len(_resultados)} producto(s) disponibles</span></div>',
        unsafe_allow_html=True,
    )

_modo_tab_lote, _modo_tab_manual = st.tabs([
    "📦 Desde Lote Activo" if _tiene_lote else "📦 Desde Lote (sin lote activo)",
    "✍️ Entrada Manual",
])

# ══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN DE PROCESAMIENTO UNIFICADA (Genera los 3 formatos + Sube ML a Supabase)
# ══════════════════════════════════════════════════════════════════════════════
def ejecutar_procesamiento_triple(bytes_raw, nombre_prod, precio_prod):
    """
    1. Procesa las 3 imágenes con IA (ML, IG Post, IG Story).
    2. Sube la imagen ML a Supabase Storage (bucket: adalimport_catalogo_temp).
    3. Recupera la URL pública y la inyecta en excel_lote_en_Estudio_Visual.
    4. También actualiza resultados_lote y lote_activo_marketing para consistencia.
    """
    with st.spinner("Procesando 3 formatos con IA (rembg puede tardar 5-15 seg la primera vez)…"):
        _bml   = procesar_version_catalogo(bytes_raw)
        _big   = procesar_version_ig_post(bytes_raw, precio_prod, nombre_prod)
        _bstry = procesar_version_ig_story(bytes_raw, precio_prod, nombre_prod)

    if _bml and _big and _bstry:
        _slug_prod = _slug(nombre_prod)
        _ts        = datetime.now().strftime("%H%M%S")

        # Nombres de archivo
        _name_ml = f"ADALIMPORT_{_slug_prod}_ML_{_ts}.png"
        _name_ig = f"ADALIMPORT_{_slug_prod}_IG_{_ts}.png"
        _name_st = f"ADALIMPORT_{_slug_prod}_STORY_{_ts}.png"

        # Guardar en disco (backup local)
        _guardar_en_disco(_bml,   _name_ml)
        _guardar_en_disco(_big,   _name_ig)
        _guardar_en_disco(_bstry, _name_st)

        # ── FLUJO INYECTOR: Supabase → Excel Web ─────────────────────────────
        _url_publica = ""
        if _SUPA_OK:
            with st.spinner("☁️ Subiendo imagen ML a Supabase…"):
                # Ruta dentro del bucket: lote_id / nombre_archivo
                _lote_id_actual = ""
                if st.session_state.get("lote_activo_marketing"):
                    _lote_id_actual = st.session_state["lote_activo_marketing"].get("lote_id", "sin_lote")
                _ruta_supa = f"{_lote_id_actual}/{_name_ml}" if _lote_id_actual else _name_ml
                _url_publica = subir_imagen_a_supabase(_bml, _ruta_supa)

            if _url_publica:
                # Actualizar el DataFrame Web
                _ok_excel = _inyectar_url_en_excel_web(nombre_prod, _url_publica)
                # Actualizar también resultados_lote y lote_activo_marketing
                _persistir_image_url_en_lote(nombre_prod, _url_publica)

                if _ok_excel:
                    st.success(
                        f"✅ Imagen procesada y URL vinculada al Excel exitosamente.\n\n"
                        f"**Producto:** {nombre_prod}  \n"
                        f"**URL:** `{_url_publica[:80]}{'…' if len(_url_publica) > 80 else ''}`"
                    )
                else:
                    st.info(
                        f"☁️ Imagen subida a Supabase correctamente, pero el producto "
                        f"**{nombre_prod}** no se encontró en el DataFrame Web "
                        f"(¿aún no aprobaste el lote?). La URL se guardó en el lote activo."
                    )
            else:
                st.warning(
                    "⚠️ No se pudo subir la imagen a Supabase. "
                    "Verifica las credenciales en `.streamlit/secrets.toml`. "
                    "Las imágenes fueron generadas y guardadas localmente."
                )
        else:
            st.info("ℹ️ Módulo Supabase no disponible — imágenes generadas y guardadas localmente.")

        # Añadir a la cola visual
        st.session_state["ev_cola"].append({
            "nombre":      nombre_prod,
            "precio":      precio_prod,
            "slug":        _slug_prod,
            "ts":          _ts,
            "bytes_ml":    _bml,
            "bytes_ig":    _big,
            "bytes_story": _bstry,
            "name_ml":     _name_ml,
            "name_ig":     _name_ig,
            "name_st":     _name_st,
            "ruta_base":   str(_carpeta_salida()),
            "supabase_url": _url_publica,
        })
        st.rerun()
    else:
        st.error("Error al procesar. Verifica que la imagen no esté corrupta.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — DESDE LOTE
# ══════════════════════════════════════════════════════════════════════════════
with _modo_tab_lote:
    if not _tiene_lote:
        st.markdown("""
        <div class="ev-empty">
          <span class="ev-empty-ico">📭</span>
          <div class="ev-empty-title">Sin lote activo</div>
          <div class="ev-empty-desc">Ve a <strong>LOTE</strong>, aprueba la vía ganadora y regresa aquí.</div>
        </div>""", unsafe_allow_html=True)
    else:
        _nombres = [r.get("nombre", f"Producto {i+1}") for i, r in enumerate(_resultados)]
        _sel_idx = st.selectbox("Selecciona el producto", options=range(len(_nombres)), format_func=lambda i: _nombres[i], key="ev_sel_prod_lote")
        _prod = _resultados[_sel_idx]
        _nombre_prod  = _prod.get("nombre", "Producto")
        _precio_prod  = float(_prod.get("precio_ml", _prod.get("precio_ml_objetivo", 0.0)))

        st.markdown(f'<div class="ev-prod-card"><div class="ev-prod-nombre">{_nombre_prod}</div><div class="ev-prod-meta">Precio ML: ${_precio_prod:.2f}</div></div>', unsafe_allow_html=True)

        _archivo = st.file_uploader("📷 Sube la foto del producto (JPG, PNG, WEBP)", type=["jpg", "jpeg", "png", "webp"], key="ev_uploader_lote")

        if _archivo:
            _bytes_raw = _archivo.read()
            _col_proc, _col_add = st.columns([2, 1])
            with _col_proc:
                if st.button("⚙️ Procesar 3 Formatos", key="ev_btn_proc_lote", use_container_width=True, type="primary"):
                    ejecutar_procesamiento_triple(_bytes_raw, _nombre_prod, _precio_prod)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — ENTRADA MANUAL
# ══════════════════════════════════════════════════════════════════════════════
with _modo_tab_manual:
    _col_m1, _col_m2 = st.columns([3, 1])
    with _col_m1:
        _nombre_man = st.text_input("Nombre del producto", placeholder="Ej: iPhone 15 Pro 256GB", key="ev_manual_nombre")
    with _col_m2:
        _precio_man = st.number_input("Precio ML ($)", min_value=0.0, step=0.5, value=0.0, key="ev_manual_precio")

    _archivo_man = st.file_uploader("📷 Foto del producto", type=["jpg", "jpeg", "png", "webp"], key="ev_uploader_manual")

    if _archivo_man and _nombre_man.strip():
        _bytes_raw_man = _archivo_man.read()
        if st.button("⚙️ Procesar 3 Formatos", key="ev_btn_proc_manual", use_container_width=True, type="primary"):
            ejecutar_procesamiento_triple(_bytes_raw_man, _nombre_man.strip(), _precio_man)
    elif _archivo_man and not _nombre_man.strip():
        st.warning("⚠️ Ingresa el nombre del producto para poder procesar.")

# ══════════════════════════════════════════════════════════════════════════════
# COLA DE IMÁGENES PROCESADAS (TABS: ML · IG Post · IG Story)
# ══════════════════════════════════════════════════════════════════════════════
_cola = st.session_state.get("ev_cola", [])

if _cola:
    st.markdown('<hr class="ev-hr">', unsafe_allow_html=True)
    st.markdown(
        f'<p style="font-family:var(--font-mono);font-size:0.62rem;letter-spacing:3px;'
        f'text-transform:uppercase;color:var(--gold);margin-bottom:10px;">'
        f'◈ Archivos listos · {len(_cola)} producto(s) procesado(s)</p>',
        unsafe_allow_html=True,
    )

    # ── Mostrar cada producto procesado — 3 pestañas: ML · IG Post · IG Story ──
    for _i, _item in enumerate(reversed(_cola)):
        _i_real = len(_cola) - 1 - _i

        st.markdown(f"""
        <div class="ev-prod-card" style="margin-top:10px; background:var(--navy-lt);">
            <div class="ev-prod-nombre">📸 {_item["nombre"]}</div>
            <div class="ev-prod-meta">Precio asignado: ${_item["precio"]:.2f}
            {"&nbsp; · &nbsp; <span style='color:var(--neon)'>☁️ URL vinculada</span>" if _item.get("supabase_url") else ""}
            </div>
        </div>
        """, unsafe_allow_html=True)

        tab_ml, tab_ig, tab_story = st.tabs([
            "📦 MercadoLibre",
            "📸 Instagram Post",
            "🎬 Instagram Story",
        ])

        # ── TAB ML ──────────────────────────────────────────────────────────
        with tab_ml:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.image(_item["bytes_ml"], use_container_width=True)
            with c2:
                st.download_button(
                    "⬇️ Descargar imagen ML",
                    data=_item["bytes_ml"],
                    file_name=_item["name_ml"],
                    mime="image/png",
                    use_container_width=True,
                    key=f"dl_ml_{_i}",
                )
                st.markdown(
                    '<div style="background:rgba(0,230,118,0.04);border:1px solid rgba(0,230,118,0.15);'
                    'border-radius:8px;padding:9px 13px;margin-top:8px;">'
                    '<span style="font-family:var(--font-mono);font-size:0.58rem;color:var(--neon);">◈ Especificaciones</span><br>'
                    '<span style="font-family:var(--font-body);font-size:0.76rem;color:var(--muted);">'
                    '1080×1080 px · Fondo <strong style="color:var(--text);">blanco puro</strong> · Sin branding</span></div>',
                    unsafe_allow_html=True,
                )
                # Mostrar URL de Supabase si ya está vinculada
                _url_s = _item.get("supabase_url", "")
                if _url_s:
                    st.markdown(
                        f'<div style="margin-top:10px;padding:8px 12px;background:rgba(0,230,118,0.04);'
                        f'border:1px solid rgba(0,230,118,0.20);border-radius:8px;">'
                        f'<span style="font-family:var(--font-mono);font-size:0.58rem;color:var(--neon);">☁️ URL Supabase vinculada</span>'
                        f'<div class="ev-url-linked">{_url_s}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

        # ── TAB IG POST ─────────────────────────────────────────────────────
        with tab_ig:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.image(_item["bytes_ig"], use_container_width=True)
            with c2:
                st.download_button(
                    "⬇️ Descargar Post",
                    data=_item["bytes_ig"],
                    file_name=_item["name_ig"],
                    mime="image/png",
                    use_container_width=True,
                    key=f"dl_ig_{_i}",
                )
                st.markdown(
                    '<div style="background:rgba(225,48,108,0.04);border:1px solid rgba(225,48,108,0.18);'
                    'border-radius:8px;padding:9px 13px;margin-top:8px;">'
                    '<span style="font-family:var(--font-mono);font-size:0.58rem;color:#e1306c;">◈ Especificaciones</span><br>'
                    '<span style="font-family:var(--font-body);font-size:0.76rem;color:var(--muted);">'
                    '1080×1080 px · Fondo <strong style="color:var(--text);">Dark Navy</strong> · Branding Oro · Sin precio</span></div>',
                    unsafe_allow_html=True,
                )

        # ── TAB IG STORY ────────────────────────────────────────────────────
        with tab_story:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.image(_item["bytes_story"], use_container_width=True)
            with c2:
                st.download_button(
                    "⬇️ Descargar Story",
                    data=_item["bytes_story"],
                    file_name=_item["name_st"],
                    mime="image/png",
                    use_container_width=True,
                    key=f"dl_st_{_i}",
                )
                st.markdown(
                    '<div style="background:rgba(184,150,62,0.04);border:1px solid rgba(184,150,62,0.18);'
                    'border-radius:8px;padding:9px 13px;margin-top:8px;">'
                    '<span style="font-family:var(--font-mono);font-size:0.58rem;color:var(--gold);">◈ Especificaciones</span><br>'
                    '<span style="font-family:var(--font-body);font-size:0.76rem;color:var(--muted);">'
                    '1080×1920 px (Vertical) · Fondo Dark Navy · Precio en etiqueta Verde Neón</span></div>',
                    unsafe_allow_html=True,
                )

        st.markdown('<hr class="ev-hr" style="margin:1.5rem 0">', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN FINAL — 📦 EXPORTACIÓN WEB FINAL
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<hr class="ev-hr" style="margin-top:2.5rem">', unsafe_allow_html=True)

st.markdown("""
<div class="ev-export-section">
  <div class="ev-export-eyebrow">📦 EXPORTACIÓN WEB</div>
  <h2 class="ev-export-title">Excel de <span>Importación Web</span></h2>
  <p class="ev-export-desc">
    Descarga el archivo <code>.xlsx</code> con todos los datos del lote aprobado,
    incluyendo las <strong style="color:var(--neon)">URLs de imagen de Supabase</strong>
    inyectadas automáticamente al procesar cada producto en el Estudio Visual.
    Listo para subir a tu tienda o plataforma de e-commerce.
  </p>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)

# ── Verificar si existe el DataFrame Web ─────────────────────────────────────
_df_web = st.session_state.get("excel_lote_en_Estudio_Visual")
_df_web_disponible = _df_web is not None and hasattr(_df_web, "shape") and len(_df_web) > 0

if not _df_web_disponible:
    st.markdown("""
    <div style="background:#1A1200;border:1px solid rgba(184,150,62,0.30);border-radius:10px;
                padding:1rem 1.4rem;text-align:center;">
        <div style="font-family:var(--font-mono);font-size:0.72rem;color:var(--gold);
                    letter-spacing:2px;text-transform:uppercase;margin-bottom:0.4rem">
            ⏳ Sin datos de lote aprobado
        </div>
        <div style="font-family:var(--font-body);font-size:0.80rem;color:var(--muted);">
            Ve a <strong>LOTE</strong>, analiza tus productos y aprueba el lote.
            Al aprobar, el DataFrame se cargará aquí automáticamente.
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    # ── Mostrar resumen del DataFrame Web ────────────────────────────────────
    _total_items = len(_df_web)
    _items_con_url = int((_df_web["image"].str.strip() != "").sum()) if "image" in _df_web.columns else 0
    _pct_completado = int(_items_con_url / _total_items * 100) if _total_items > 0 else 0

    _c1, _c2, _c3 = st.columns(3)
    _c1.markdown(f"""
    <div style="background:var(--navy-md);border:1px solid var(--border);border-radius:10px;
                padding:1rem;text-align:center;">
        <div style="font-family:var(--font-mono);font-size:0.58rem;color:var(--muted);
                    text-transform:uppercase;letter-spacing:1.5px;margin-bottom:4px">Total ítems</div>
        <div style="font-family:var(--font-mono);font-size:1.5rem;font-weight:800;
                    color:var(--text)">{_total_items}</div>
    </div>""", unsafe_allow_html=True)

    _c2.markdown(f"""
    <div style="background:var(--navy-md);border:1px solid var(--border);border-radius:10px;
                padding:1rem;text-align:center;">
        <div style="font-family:var(--font-mono);font-size:0.58rem;color:var(--muted);
                    text-transform:uppercase;letter-spacing:1.5px;margin-bottom:4px">Con URL imagen</div>
        <div style="font-family:var(--font-mono);font-size:1.5rem;font-weight:800;
                    color:var(--neon)">{_items_con_url}</div>
    </div>""", unsafe_allow_html=True)

    _c3.markdown(f"""
    <div style="background:var(--navy-md);border:1px solid var(--border);border-radius:10px;
                padding:1rem;text-align:center;">
        <div style="font-family:var(--font-mono);font-size:0.58rem;color:var(--muted);
                    text-transform:uppercase;letter-spacing:1.5px;margin-bottom:4px">Completado</div>
        <div style="font-family:var(--font-mono);font-size:1.5rem;font-weight:800;
                    color:{'var(--neon)' if _pct_completado == 100 else 'var(--gold)'}">{_pct_completado}%</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)

    # ── Botón de descarga del Excel Web ──────────────────────────────────────
    try:
        from exportador_reportes import generar_excel_importacion_web

        # Nombre de archivo con lote_id si está disponible
        _lote_id_xl = "lote"
        if st.session_state.get("lote_activo_marketing"):
            _lote_id_xl = st.session_state["lote_activo_marketing"].get("lote_id", "lote")

        # ── Convertir el DataFrame a la lista de dicts que espera la función ──
        # El DataFrame tiene las columnas internas del análisis + "category" + "image".
        # generar_excel_importacion_web extrae exactamente lo que necesita:
        #   lote_id, title (nombre→60 chars), stock (cantidad), category, price, image
        _resultados_web = _df_web.to_dict(orient="records")

        # Llamar a la función canónica — aplica regla de 60 chars, mapea columnas
        # y devuelve solo las 6 columnas necesarias para Supabase
        _bytes_xl = generar_excel_importacion_web(
            resultados=_resultados_web,
            lote_id=_lote_id_xl,
        )

        _col_dl1, _col_dl2, _col_dl3 = st.columns([1, 2, 1])
        with _col_dl2:
            st.download_button(
                label="📊 Descargar Excel de Importación Web",
                data=_bytes_xl,
                file_name=f"ADALIMPORT_{_lote_id_xl}_web.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary",
                help=f"Columnas: lote_id · title (60 chars) · stock · category · price · image",
            )

        st.markdown(
            f'<div style="text-align:center;margin-top:0.6rem;font-family:var(--font-mono);'
            f'font-size:0.62rem;color:#3a5a3a;">'
            f'✓ {_items_con_url} de {_total_items} ítems con URL de imagen vinculada · '
            f'Columnas: lote_id · title · stock · category · price · image</div>',
            unsafe_allow_html=True,
        )

    except ImportError:
        st.error(
            "**openpyxl no está instalado.** Añade `openpyxl` a `requirements.txt` y reinicia la app.",
            icon="📦",
        )
    except Exception as _e_xl:
        st.error(f"Error al generar el Excel: `{_e_xl}`", icon="🚨")

st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
