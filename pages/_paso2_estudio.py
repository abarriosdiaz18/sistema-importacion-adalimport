import streamlit as st
import sys, os, builtins as _builtins

# ── FIX sys.path (mismo patrón que el resto de páginas) ──────────────────────
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
#  ADALIMPORT — pages/_paso2_estudio.py  ·  v1.0 (Paso 2 del Pipeline Wizard)
#  Estudio Visual — Generador de Imágenes Multi-plataforma
#
#  Versión: refactor de _estudio_visual.py con:
#    1. Guard de prerequisito (requiere lote aprobado del Paso 1).
#    2. Barra wizard render_wizard_nav(paso_actual=2).
#    3. Depósito de "ev_paso2_completado" al procesar al menos 1 imagen.
#    4. Botón "Continuar al Paso 3" al final.
#    5. Deposita URLs procesadas en "excel_urls_imagenes" para el Paso 3.
#
#  Página atómica: no importa de otras páginas.
#  Módulos core: procesador_imagenes.py y publicador_imagenes.py — SIN CAMBIOS.
#  Comunicación: EXCLUSIVAMENTE via st.session_state.
# ══════════════════════════════════════════════════════════════════════════════

# ── Componentes del wizard ────────────────────────────────────────────────────
try:
    from modules._wizard_nav      import render_wizard_nav, guard_prerequisito
    from modules._estado_pipeline import marcar_paso2_completado
    _WIZARD_OK = True
except ImportError:
    _WIZARD_OK = False
    def render_wizard_nav(paso_actual: int) -> None: pass
    def guard_prerequisito(n: int, pagina_retroceso: str = "paso1") -> bool: return True
    def marcar_paso2_completado() -> None: pass

# ── Guard de prerequisito ─────────────────────────────────────────────────────
# Paso 2 requiere: lote_id + _lote_aprobado (definido en _estado_pipeline.py)
# Si no se cumplen, guard_prerequisito() muestra el banner y llama st.stop()
guard_prerequisito(2, pagina_retroceso="paso1")

# ── Design System ─────────────────────────────────────────────────────────────
from styles_adalimport import aplicar_estilos
aplicar_estilos()

# ── Módulo core: procesador de imágenes ──────────────────────────────────────
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
except Exception:
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
except Exception:
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

def _inyectar_url_en_excel_web(nombre_producto: str, url_publica: str) -> bool:
    """Busca el producto en el DataFrame Web y actualiza su columna 'image'."""
    import pandas as pd
    df = st.session_state.get("excel_lote_en_Estudio_Visual")
    if df is None or not isinstance(df, pd.DataFrame):
        return False
    mask = df["nombre"].str.strip().str.lower() == nombre_producto.strip().lower()
    if not mask.any():
        return False
    df.loc[mask, "image"] = url_publica
    st.session_state["excel_lote_en_Estudio_Visual"] = df
    return True

def _persistir_image_url_en_lote(nombre_producto: str, url_publica: str) -> None:
    """Actualiza resultados_lote y lote_activo_marketing con la URL de imagen."""
    for _key in ("resultados_lote",):
        _lista = st.session_state.get(_key, [])
        for _item in _lista:
            if _item.get("nombre", "").strip().lower() == nombre_producto.strip().lower():
                _item["imagen_url"] = url_publica
    _lmkt = st.session_state.get("lote_activo_marketing")
    if _lmkt and isinstance(_lmkt.get("resultados"), list):
        for _item in _lmkt["resultados"]:
            if _item.get("nombre", "").strip().lower() == nombre_producto.strip().lower():
                _item["imagen_url"] = url_publica
    # ── Depositar también en el dict excel_urls_imagenes (contrato Paso 3) ───
    if "excel_urls_imagenes" not in st.session_state:
        st.session_state["excel_urls_imagenes"] = {}
    st.session_state["excel_urls_imagenes"][nombre_producto.strip()] = url_publica

# ══════════════════════════════════════════════════════════════════════════════
# BARRA WIZARD
# ══════════════════════════════════════════════════════════════════════════════
render_wizard_nav(paso_actual=2)

# ══════════════════════════════════════════════════════════════════════════════
# HEADER DE PÁGINA
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div style="background:linear-gradient(135deg,rgba(13,20,36,0.9) 0%,rgba(5,9,15,0.95) 100%);
            border:1px solid rgba(184,150,62,0.2);border-top:2px solid var(--gold);
            border-radius:14px;padding:20px 24px;margin-bottom:24px;
            display:flex;align-items:center;gap:16px;">
  <span style="font-size:2rem;line-height:1;filter:drop-shadow(0 0 10px rgba(184,150,62,0.4));">🎨</span>
  <div style="flex:1">
    <div style="font-family:'DM Mono',monospace;font-size:0.58rem;letter-spacing:3px;
                text-transform:uppercase;color:var(--gold);margin-bottom:4px;">
      Pipeline · Paso 2 de 4
    </div>
    <div style="font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:800;
                color:var(--text);line-height:1.1;margin-bottom:4px;">
      Estudio <span style="color:var(--gold);">Visual</span>
    </div>
    <div style="font-family:'Inter',sans-serif;font-size:0.82rem;color:var(--muted);">
      Genera imágenes de catálogo (ML) e imágenes con branding (Instagram Post / Story).
      Las imágenes ML se suben automáticamente a Supabase.
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Badges de estado de módulos ───────────────────────────────────────────────
_pil_ok   = modulo_disponible()
_rembg_ok = rembg_disponible()

_col_badge1, _col_badge2, _col_badge3 = st.columns([1, 1, 3])
with _col_badge1:
    if _pil_ok:
        st.markdown('<span style="background:rgba(0,230,118,0.1);border:1px solid rgba(0,230,118,0.3);'
                    'border-radius:6px;padding:3px 10px;font-family:DM Mono,monospace;font-size:0.68rem;'
                    'color:#00E676;">✓ Pillow activo</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span style="background:rgba(248,113,113,0.1);border:1px solid rgba(248,113,113,0.3);'
                    'border-radius:6px;padding:3px 10px;font-family:DM Mono,monospace;font-size:0.68rem;'
                    'color:#f87171;">✕ Pillow faltante</span>', unsafe_allow_html=True)
with _col_badge2:
    if _rembg_ok:
        st.markdown('<span style="background:rgba(0,230,118,0.1);border:1px solid rgba(0,230,118,0.3);'
                    'border-radius:6px;padding:3px 10px;font-family:DM Mono,monospace;font-size:0.68rem;'
                    'color:#00E676;">✓ rembg IA activo</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span style="background:rgba(184,150,62,0.1);border:1px solid rgba(184,150,62,0.3);'
                    'border-radius:6px;padding:3px 10px;font-family:DM Mono,monospace;font-size:0.68rem;'
                    'color:#B8963E;">◎ rembg opcional</span>', unsafe_allow_html=True)
with _col_badge3:
    if _SUPA_OK:
        st.markdown('<span style="background:rgba(0,230,118,0.1);border:1px solid rgba(0,230,118,0.3);'
                    'border-radius:6px;padding:3px 10px;font-family:DM Mono,monospace;font-size:0.68rem;'
                    'color:#00E676;">☁️ Supabase conectado</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span style="background:rgba(184,150,62,0.1);border:1px solid rgba(184,150,62,0.3);'
                    'border-radius:6px;padding:3px 10px;font-family:DM Mono,monospace;font-size:0.68rem;'
                    'color:#B8963E;">☁️ Supabase no disponible</span>', unsafe_allow_html=True)

if not _pil_ok:
    st.error("**Pillow no está instalado.** Añade `Pillow` a `requirements.txt` y reinicia la app.")
    st.stop()

st.markdown('<hr style="border:none;border-top:1px solid #141e30;margin:16px 0;">', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN DE PROCESAMIENTO TRIPLE
# ══════════════════════════════════════════════════════════════════════════════
def ejecutar_procesamiento_triple(bytes_raw, nombre_prod, precio_prod):
    """
    1. Procesa 3 formatos (ML, IG Post, IG Story) con IA.
    2. Sube imagen ML a Supabase Storage.
    3. Inyecta URL en el DataFrame Web y en excel_urls_imagenes (contrato Paso 3).
    4. Marca el Paso 2 como completado en el pipeline.
    """
    with st.spinner("Procesando 3 formatos con IA (rembg puede tardar 5-15 seg la primera vez)…"):
        _bml   = procesar_version_catalogo(bytes_raw)
        _big   = procesar_version_ig_post(bytes_raw, precio_prod, nombre_prod)
        _bstry = procesar_version_ig_story(bytes_raw, precio_prod, nombre_prod)

    if _bml and _big and _bstry:
        _slug_prod = _slug(nombre_prod)
        _ts        = datetime.now().strftime("%H%M%S")

        _name_ml = f"ADALIMPORT_{_slug_prod}_ML_{_ts}.png"
        _name_ig = f"ADALIMPORT_{_slug_prod}_IG_{_ts}.png"
        _name_st = f"ADALIMPORT_{_slug_prod}_STORY_{_ts}.png"

        _guardar_en_disco(_bml,   _name_ml)
        _guardar_en_disco(_big,   _name_ig)
        _guardar_en_disco(_bstry, _name_st)

        _url_publica = ""
        if _SUPA_OK:
            with st.spinner("☁️ Subiendo imagen ML a Supabase…"):
                _lote_id_actual = (
                    st.session_state.get("lote_activo_marketing", {}).get("lote_id", "")
                    or st.session_state.get("lote_id", "sin_lote")
                )
                _ruta_supa = f"{_lote_id_actual}/{_name_ml}" if _lote_id_actual else _name_ml
                _url_publica = subir_imagen_a_supabase(_bml, _ruta_supa)

            if _url_publica:
                _inyectar_url_en_excel_web(nombre_prod, _url_publica)
                _persistir_image_url_en_lote(nombre_prod, _url_publica)
                st.success(
                    f"✅ Imagen procesada y URL vinculada exitosamente.\n\n"
                    f"**Producto:** {nombre_prod}  \n"
                    f"**URL:** `{_url_publica[:80]}{'…' if len(_url_publica) > 80 else ''}`"
                )
            else:
                st.warning(
                    "⚠️ No se pudo subir la imagen a Supabase. "
                    "Verifica las credenciales en `.streamlit/secrets.toml`. "
                    "Las imágenes fueron generadas y guardadas localmente."
                )
        else:
            st.info("ℹ️ Supabase no disponible — imágenes generadas y guardadas localmente.")

        # ── Marcar Paso 2 como completado (contrato del pipeline) ────────────
        marcar_paso2_completado()

        st.session_state.setdefault("ev_cola", []).append({
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
# ESTADO DEL LOTE ACTIVO
# ══════════════════════════════════════════════════════════════════════════════
_lote_mkt   = st.session_state.get("lote_activo_marketing")
_resultados = st.session_state.get("resultados_lote", [])
_tiene_lote = bool(_lote_mkt and _resultados)

if "ev_cola" not in st.session_state:
    st.session_state["ev_cola"] = []

if _tiene_lote:
    _lote_id_disp = _lote_mkt.get("lote_id", "—")
    st.markdown(
        f'<div style="background:rgba(0,230,118,0.06);border:1px solid rgba(0,230,118,0.20);'
        f'border-radius:8px;padding:10px 14px;margin-bottom:16px;">'
        f'<span style="font-family:var(--font-mono);font-size:0.62rem;color:var(--neon);">'
        f'● Lote activo: <strong>{_lote_id_disp}</strong> · {len(_resultados)} producto(s) disponibles</span></div>',
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# TABS: DESDE LOTE ACTIVO / ENTRADA MANUAL
# ══════════════════════════════════════════════════════════════════════════════
_modo_tab_lote, _modo_tab_manual = st.tabs([
    "📦 Desde Lote Activo" if _tiene_lote else "📦 Desde Lote (sin lote activo)",
    "✍️ Entrada Manual",
])

# ── TAB: Desde lote ───────────────────────────────────────────────────────────
with _modo_tab_lote:
    if not _tiene_lote:
        st.markdown("""
        <div style="background:rgba(184,150,62,0.06);border:1px solid rgba(184,150,62,0.2);
                    border-radius:10px;padding:1rem 1.4rem;font-family:'Inter',sans-serif;
                    font-size:0.85rem;color:#94a3b8;">
            ℹ &nbsp; Aprueba un lote en el <strong style="color:#B8963E;">Paso 1</strong>
            para que aparezcan aquí los productos disponibles.
        </div>""", unsafe_allow_html=True)
    else:
        # Selector de producto del lote
        _nombres_lote = [r.get("nombre", f"Producto {i+1}") for i, r in enumerate(_resultados)]
        _sel_nombre = st.selectbox(
            "Selecciona el producto a procesar:",
            options=_nombres_lote,
            key="ev_sel_producto_lote",
        )
        _sel_item = next(
            (r for r in _resultados if r.get("nombre") == _sel_nombre),
            _resultados[0] if _resultados else {},
        )
        _precio_sel = float(_sel_item.get("precio_ml_objetivo", _sel_item.get("precio_ml", 0)) or 0)

        st.markdown(
            f'<div style="font-family:var(--font-mono);font-size:0.72rem;color:#64748b;margin-bottom:12px;">'
            f'Precio ML objetivo: <strong style="color:#B8963E;">${_precio_sel:.2f}</strong></div>',
            unsafe_allow_html=True,
        )

        _up_key_lote = f"ev_uploader_lote_{st.session_state.get('_uploader_counter', 0)}"
        _uploaded_lote = st.file_uploader(
            "📤 Sube la foto del producto",
            type=["jpg", "jpeg", "png", "webp"],
            key=_up_key_lote,
            help="JPG, PNG o WebP · Fondo blanco o neutral recomendado para mejor resultado IA",
        )

        if _uploaded_lote:
            _bytes_lote = _uploaded_lote.read()
            st.image(_bytes_lote, caption=f"Vista previa — {_sel_nombre}", width=260)
            if st.button("🚀  Procesar imagen", key="ev_btn_procesar_lote", type="primary",
                         use_container_width=True):
                ejecutar_procesamiento_triple(_bytes_lote, _sel_nombre, _precio_sel)

# ── TAB: Entrada manual ───────────────────────────────────────────────────────
with _modo_tab_manual:
    _col_m1, _col_m2 = st.columns(2)
    with _col_m1:
        _nombre_manual = st.text_input(
            "Nombre del producto", key="ev_nombre_manual",
            placeholder="Ej: Auriculares Bluetooth Sony WH-1000XM5",
        )
    with _col_m2:
        _precio_manual = st.number_input(
            "Precio ML objetivo (USD)", min_value=0.0, step=0.5,
            key="ev_precio_manual", value=0.0,
        )

    _up_key_manual = f"ev_uploader_manual_{st.session_state.get('_uploader_counter', 0)}"
    _uploaded_manual = st.file_uploader(
        "📤 Sube la foto del producto",
        type=["jpg", "jpeg", "png", "webp"],
        key=_up_key_manual,
    )

    if _uploaded_manual:
        _bytes_manual = _uploaded_manual.read()
        st.image(_bytes_manual, caption="Vista previa", width=260)
        if st.button("🚀  Procesar imagen", key="ev_btn_procesar_manual", type="primary",
                     use_container_width=True):
            if not _nombre_manual.strip():
                st.warning("Ingresa el nombre del producto antes de procesar.")
            else:
                ejecutar_procesamiento_triple(_bytes_manual, _nombre_manual.strip(), _precio_manual)

# ══════════════════════════════════════════════════════════════════════════════
# COLA DE IMÁGENES PROCESADAS (TABS: ML · IG Post · IG Story)
# ══════════════════════════════════════════════════════════════════════════════
_cola = st.session_state.get("ev_cola", [])

if _cola:
    st.markdown('<hr style="border:none;border-top:1px solid #141e30;margin:20px 0;">', unsafe_allow_html=True)
    st.markdown(
        f'<p style="font-family:var(--font-mono);font-size:0.62rem;letter-spacing:3px;'
        f'text-transform:uppercase;color:var(--gold);margin-bottom:10px;">'
        f'◈ Archivos listos · {len(_cola)} producto(s) procesado(s)</p>',
        unsafe_allow_html=True,
    )

    for _i, _item in enumerate(reversed(_cola)):
        st.markdown(f"""
        <div style="background:var(--navy-lt);border:1px solid #141e30;border-radius:10px;
                    padding:10px 14px;margin-bottom:10px;">
            <div style="font-family:'Syne',sans-serif;font-weight:700;color:var(--text);
                        font-size:0.9rem;">📸 {_item['nombre']}</div>
            <div style="font-family:var(--font-mono);font-size:0.65rem;color:var(--muted);margin-top:3px;">
                Precio: ${_item['precio']:.2f}
                {"&nbsp; · &nbsp; <span style='color:var(--neon);'>☁️ URL Supabase vinculada</span>"
                 if _item.get("supabase_url") else ""}
            </div>
        </div>
        """, unsafe_allow_html=True)

        _tab_ml, _tab_ig, _tab_story = st.tabs(["📦 MercadoLibre", "📸 Instagram Post", "🎬 Instagram Story"])

        with _tab_ml:
            _c1, _c2 = st.columns([1, 2])
            with _c1:
                st.image(_item["bytes_ml"], use_container_width=True)
            with _c2:
                st.download_button(
                    "⬇️  Descargar ML",
                    data=_item["bytes_ml"],
                    file_name=_item["name_ml"],
                    mime="image/png",
                    key=f"dl_ml_{_i}",
                    use_container_width=True,
                )
                if _item.get("supabase_url"):
                    st.markdown(
                        f'<div style="font-family:var(--font-mono);font-size:0.65rem;'
                        f'color:var(--neon);word-break:break-all;margin-top:8px;">'
                        f'☁️ {_item["supabase_url"][:90]}{"…" if len(_item["supabase_url"]) > 90 else ""}'
                        f'</div>', unsafe_allow_html=True,
                    )

        with _tab_ig:
            _c1, _c2 = st.columns([1, 2])
            with _c1:
                st.image(_item["bytes_ig"], use_container_width=True)
            with _c2:
                st.download_button(
                    "⬇️  Descargar IG Post",
                    data=_item["bytes_ig"],
                    file_name=_item["name_ig"],
                    mime="image/png",
                    key=f"dl_ig_{_i}",
                    use_container_width=True,
                )

        with _tab_story:
            _c1, _c2 = st.columns([1, 2])
            with _c1:
                st.image(_item["bytes_story"], use_container_width=True)
            with _c2:
                st.download_button(
                    "⬇️  Descargar IG Story",
                    data=_item["bytes_story"],
                    file_name=_item["name_st"],
                    mime="image/png",
                    key=f"dl_story_{_i}",
                    use_container_width=True,
                )

# ══════════════════════════════════════════════════════════════════════════════
# BOTÓN DE CONTINUACIÓN AL PASO 3
# ══════════════════════════════════════════════════════════════════════════════
if _cola:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<hr style="border:none;border-top:1px solid #141e30;margin:0 0 20px 0;">',
                unsafe_allow_html=True)

    _n_urls = len(st.session_state.get("excel_urls_imagenes", {}))

    st.markdown(f"""
    <div style="background:rgba(0,230,118,0.05);border:1px solid rgba(0,230,118,0.2);
                border-radius:10px;padding:14px 18px;margin-bottom:16px;
                font-family:'Inter',sans-serif;font-size:0.85rem;color:#94a3b8;">
        ✅ &nbsp;<strong style="color:#00E676;">{len(_cola)} imagen(s) procesada(s)</strong>
        {"&nbsp; · &nbsp; <strong style='color:#00E676;'>" + str(_n_urls) + " URL(s)</strong> vinculadas a Supabase"
         if _n_urls else ""}
        <br><span style="font-size:0.78rem;color:#4a5568;margin-top:4px;display:block;">
        Puedes continuar al Paso 3 para generar el Excel de exportación para el CMS.
        </span>
    </div>
    """, unsafe_allow_html=True)

    _btn_col1, _btn_col2, _btn_col3 = st.columns([1, 2, 1])
    with _btn_col2:
        if st.button(
            "Continuar al Paso 3 — Exportación Excel  →",
            key="ev_btn_continuar_paso3",
            type="primary",
            use_container_width=True,
        ):
            st.session_state["pagina_activa"] = "paso3"
            st.rerun()

elif _tiene_lote:
    # Hay lote pero aún no se procesó ninguna imagen — mostrar hint
    st.markdown("""
    <div style="background:rgba(184,150,62,0.04);border:1px solid rgba(184,150,62,0.15);
                border-left:3px solid rgba(184,150,62,0.4);border-radius:10px;
                padding:1rem 1.4rem;font-family:'Inter',sans-serif;
                font-size:0.85rem;color:#94a3b8;margin-top:1rem;">
        ℹ &nbsp; Sube la foto de al menos un producto para habilitar el botón de continuación.
        <br><span style="font-size:0.78rem;color:#4a5568;margin-top:4px;display:block;">
        El Paso 2 es <strong>opcional</strong> — también puedes ir directamente al Paso 3 desde la barra de progreso.
        </span>
    </div>
    """, unsafe_allow_html=True)
