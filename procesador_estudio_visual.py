# ══════════════════════════════════════════════════════════════════════════════
# ADALIMPORT · procesador_estudio_visual.py  ·  v1.0
# Módulo Python puro (importable) — Estudio Visual de imágenes
#
# Extraído de _publicaciones.py para desacoplar la lógica de procesamiento
# de imágenes del flujo principal de generación de copys.
# Nombre distinto de _estudio_visual.py (página en pages/) para evitar
# cualquier confusión o conflicto de import.
#
# USO:
#   from procesador_estudio_visual import render_estudio_visual
#   render_estudio_visual(nombre_producto, precio_producto, lista_productos, modo)
#
# Dependencias inyectadas en el caller (NO hace sus propios imports de páginas):
#   · streamlit (st) — se importa aquí directamente
#   · procesador_imagenes — se importa aquí con fallback seguro
# ══════════════════════════════════════════════════════════════════════════════

import re as _re_ev
import streamlit as st

# ── Procesador de imágenes con fallback seguro ────────────────────────────────
try:
    from procesador_imagenes import (
        modulo_disponible,
        procesar_version_catalogo,
        procesar_version_ig_post,
        procesar_version_ig_story,
        rembg_disponible,
    )
    _PROCESADOR_OK = True
except Exception:
    _PROCESADOR_OK = False
    def modulo_disponible():                            return False
    def rembg_disponible():                             return False
    def procesar_version_catalogo(_b):                  return None
    def procesar_version_ig_post(_b, _p, _n):           return None
    def procesar_version_ig_story(_b, _p, _n):          return None


# ══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN PÚBLICA
# ══════════════════════════════════════════════════════════════════════════════

def render_estudio_visual(
    nombre_producto: str,
    precio_producto: float,
    lista_productos,          # list[dict] con claves "nombre"/"precio", o None
    modo: str = "individual", # "individual" | "lote"
) -> None:
    """
    Renderiza el Estudio Visual completo dentro de un st.expander:
      · Sube 1 foto → genera 3 formatos (ML · IG Post · IG Story · WhatsApp)

    Modos:
      individual — usa nombre_producto y precio_producto directamente.
                   No muestra selector de productos.
      lote       — muestra un selectbox para elegir producto de lista_productos.
                   nombre y precio se toman del ítem seleccionado.

    Toda comunicación con el resto de la app es via st.session_state.
    Esta función NO modifica session_state salvo lectura de _pub_nombre/_pub_precio.
    """

    with st.expander("🎨  Estudio Visual · ML · Instagram Post · IG Story", expanded=False):

        # ── Encabezado ─────────────────────────────────────────────────────────
        st.markdown(
            '<p style="font-family:var(--font-mono);font-size:0.60rem;letter-spacing:3px;'
            'text-transform:uppercase;color:var(--gold);margin:0 0 2px 0;">'
            '◈ Procesamiento de Imagen · Módulo Atómico v3.0</p>'
            '<p style="font-family:\'Syne\',sans-serif;font-size:1.05rem;font-weight:700;'
            'color:var(--text);margin:0 0 4px 0;">'
            'Genera los 3 formatos de imagen desde una sola foto</p>'
            '<p style="font-family:var(--font-body);font-size:0.80rem;color:var(--muted);margin:0 0 12px 0;">'
            '📦 <strong style="color:var(--text);">ML</strong> — Fondo blanco puro, sin texto &nbsp;·&nbsp; '
            '📸 <strong style="color:var(--text);">IG Post</strong> — Branding + nombre, sin precio &nbsp;·&nbsp; '
            '🎬 <strong style="color:var(--text);">IG Story</strong> — Branding completo + precio &nbsp;·&nbsp; '
            '💬 <strong style="color:var(--text);">WhatsApp</strong> — usa la imagen del IG Post'
            '</p>',
            unsafe_allow_html=True,
        )

        # ── Estado de dependencias ─────────────────────────────────────────────
        _pil_ok   = modulo_disponible()
        _rembg_ok = rembg_disponible()

        if not _pil_ok:
            st.warning(
                "⚠️ **Pillow no está instalado.** Añade `Pillow` a tu `requirements.txt` y reinicia la app.",
                icon="📦",
            )
            return

        if _rembg_ok:
            st.markdown(
                '<div style="background:rgba(0,230,118,0.06);border:1px solid rgba(0,230,118,0.22);'
                'border-radius:8px;padding:8px 14px;margin-bottom:14px;font-family:var(--font-body);'
                'font-size:0.80rem;color:rgba(0,230,118,0.85);">'
                '✅ <strong>Remoción de fondo activa</strong> — rembg (U²-Net IA) eliminará el fondo en los 3 formatos.'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="background:rgba(184,150,62,0.06);border:1px solid rgba(184,150,62,0.25);'
                'border-radius:8px;padding:8px 14px;margin-bottom:14px;font-family:var(--font-body);'
                'font-size:0.80rem;color:rgba(184,150,62,0.85);">'
                '⚠️ <strong>rembg no instalado</strong> — Sin remoción de fondo. '
                'Actívalo con: <code>pip install rembg onnxruntime</code>'
                '</div>',
                unsafe_allow_html=True,
            )

        # ── Paso 1: Contexto del producto ──────────────────────────────────────
        # Sufijo único por modo para evitar colisiones de key entre instancias
        _key_sfx = modo

        if modo == "lote" and lista_productos:
            st.markdown(
                '<span style="font-family:var(--font-mono);font-size:0.62rem;'
                'color:var(--muted);letter-spacing:2px;text-transform:uppercase;">'
                'Paso 1 — Selecciona el producto del lote</span>',
                unsafe_allow_html=True,
            )
            _nombres_ev = [p["nombre"] for p in lista_productos]
            _sel_ev = st.selectbox(
                "Producto",
                options=_nombres_ev,
                key=f"ev_sel_prod_{_key_sfx}",
                label_visibility="collapsed",
            )
            _prod_ev   = next((p for p in lista_productos if p["nombre"] == _sel_ev), None)
            _ev_nombre = _prod_ev["nombre"] if _prod_ev else ""
            _ev_precio = float(_prod_ev["precio"]) if _prod_ev else 0.0
        else:
            # Modo individual / manual: datos vienen del formulario de producto
            _ev_nombre = nombre_producto or st.session_state.get("_pub_nombre", "")
            _ev_precio = precio_producto  or float(st.session_state.get("_pub_precio", 0.0))
            if _ev_nombre:
                st.markdown(
                    '<span style="font-family:var(--font-mono);font-size:0.62rem;'
                    'color:var(--muted);letter-spacing:2px;text-transform:uppercase;">'
                    'Paso 1 — Producto activo</span>',
                    unsafe_allow_html=True,
                )
            else:
                st.info("Ingresa el nombre del producto en el formulario de arriba para activar el Estudio Visual.")
                return

        # Chip de producto activo con precio
        st.markdown(
            f'<div style="display:flex;gap:16px;align-items:center;'
            f'background:rgba(184,150,62,0.05);border:1px solid rgba(184,150,62,0.18);'
            f'border-radius:8px;padding:8px 14px;margin:8px 0 16px 0;">'
            f'<span style="font-family:var(--font-body);font-weight:600;font-size:0.88rem;'
            f'color:var(--text);flex:1;">{_ev_nombre or "—"}</span>'
            f'<span style="font-family:var(--font-mono);font-size:0.78rem;color:var(--gold);white-space:nowrap;">'
            f'💲 ${_ev_precio:.2f} &nbsp;<span style="color:var(--muted);font-size:0.65rem;">'
            f'(aparecerá en IG Story)</span></span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── Paso 2: Upload ─────────────────────────────────────────────────────
        st.markdown(
            '<span style="font-family:var(--font-mono);font-size:0.62rem;'
            'color:var(--muted);letter-spacing:2px;text-transform:uppercase;">'
            'Paso 2 — Sube la foto cruda del producto</span>',
            unsafe_allow_html=True,
        )
        _archivo_ev = st.file_uploader(
            "Foto",
            type=["jpg", "jpeg", "png", "webp"],
            key=f"ev_uploader_{_key_sfx}",
            help="JPG · PNG · WEBP — Una foto genera los 3 formatos automáticamente.",
            label_visibility="collapsed",
        )

        # ── Paso 3: Procesamiento ─────────────────────────────────────────────
        if _archivo_ev is None:
            st.markdown(
                '<div style="border:1px dashed rgba(184,150,62,0.22);border-radius:10px;'
                'padding:28px 20px;text-align:center;margin-top:8px;">'
                '<span style="font-size:2rem;display:block;margin-bottom:8px;">🖼️</span>'
                '<span style="font-family:var(--font-mono);font-size:0.66rem;color:var(--muted);'
                'letter-spacing:2px;text-transform:uppercase;">Esperando imagen</span><br>'
                '<span style="font-family:var(--font-body);font-size:0.78rem;'
                'color:rgba(200,200,200,0.35);margin-top:6px;display:block;">'
                'Se generarán: 📦 ML &nbsp;·&nbsp; 📸 IG Post &nbsp;·&nbsp; 🎬 IG Story &nbsp;·&nbsp; 💬 WhatsApp'
                '</span></div>',
                unsafe_allow_html=True,
            )
            return

        st.markdown(
            '<hr style="border:none;border-top:1px solid rgba(184,150,62,0.12);margin:14px 0">'
            '<span style="font-family:var(--font-mono);font-size:0.62rem;'
            'color:var(--muted);letter-spacing:2px;text-transform:uppercase;">'
            'Paso 3 — Resultados</span>',
            unsafe_allow_html=True,
        )

        _bytes_raw   = _archivo_ev.read()
        _nombre_arch = _re_ev.sub(r'[^a-zA-Z0-9_\-]', '_', _ev_nombre)[:40] or "producto"

        with st.spinner("Procesando imagen con IA — remoción de fondo en curso…"):
            _bml   = procesar_version_catalogo(_bytes_raw)
            _big   = procesar_version_ig_post(_bytes_raw, _ev_precio, _ev_nombre)
            _bstry = procesar_version_ig_story(_bytes_raw, _ev_precio, _ev_nombre)

        if not any([_bml, _big, _bstry]):
            st.error("❌ Error al procesar la imagen. Verifica que el archivo no esté corrupto.")
            return

        # Foto original — pequeña, a la izquierda
        _co, _ce = st.columns([1, 3])
        with _co:
            st.markdown(
                '<span style="font-family:var(--font-mono);font-size:0.56rem;color:var(--muted);'
                'letter-spacing:2px;text-transform:uppercase;display:block;margin-bottom:4px;">'
                '📷 Original</span>',
                unsafe_allow_html=True,
            )
            st.image(_bytes_raw, use_container_width=True)

        st.markdown(
            '<hr style="border:none;border-top:1px solid rgba(184,150,62,0.10);margin:14px 0">',
            unsafe_allow_html=True,
        )

        # ── Tabs de resultados ─────────────────────────────────────────────────
        _tab_ml, _tab_ig, _tab_story, _tab_wa = st.tabs([
            "📦 MercadoLibre",
            "📸 Instagram Post",
            "🎬 Instagram Story",
            "💬 WhatsApp",
        ])

        # ── TAB: MercadoLibre ──────────────────────────────────────────────────
        with _tab_ml:
            if _bml:
                _c1, _c2, _c3 = st.columns([1, 2, 1])
                with _c2:
                    st.image(_bml, use_container_width=True)
                st.download_button(
                    label="⬇️  Descargar · Catálogo ML (PNG 1080×1080)",
                    data=_bml,
                    file_name=f"ADALIMPORT_{_nombre_arch}_ML.png",
                    mime="image/png",
                    use_container_width=True,
                    key=f"ev_dl_ml_{_key_sfx}",
                )
                st.markdown(
                    '<div style="background:rgba(0,230,118,0.04);border:1px solid rgba(0,230,118,0.15);'
                    'border-radius:8px;padding:9px 13px;margin-top:8px;">'
                    '<span style="font-family:var(--font-mono);font-size:0.58rem;color:var(--neon);">◈ Especificaciones</span><br>'
                    '<span style="font-family:var(--font-body);font-size:0.76rem;color:var(--muted);">'
                    '1080×1080 px &nbsp;·&nbsp; Relación 1:1 &nbsp;·&nbsp; '
                    'Fondo <strong style="color:var(--text);">blanco puro</strong> &nbsp;·&nbsp; '
                    'Sin logo · Sin precio · Sin texto'
                    '</span></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.error("Error generando la versión ML.")

        # ── TAB: Instagram Post ────────────────────────────────────────────────
        with _tab_ig:
            if _big:
                _c1, _c2, _c3 = st.columns([1, 2, 1])
                with _c2:
                    st.image(_big, use_container_width=True)
                st.download_button(
                    label="⬇️  Descargar · IG Post (PNG 1080×1080)",
                    data=_big,
                    file_name=f"ADALIMPORT_{_nombre_arch}_IG_Post.png",
                    mime="image/png",
                    use_container_width=True,
                    key=f"ev_dl_ig_{_key_sfx}",
                )
                st.markdown(
                    '<div style="background:rgba(225,48,108,0.04);border:1px solid rgba(225,48,108,0.18);'
                    'border-radius:8px;padding:9px 13px;margin-top:8px;">'
                    '<span style="font-family:var(--font-mono);font-size:0.58rem;color:#e1306c;">◈ Especificaciones</span><br>'
                    '<span style="font-family:var(--font-body);font-size:0.76rem;color:var(--muted);">'
                    '1080×1080 px &nbsp;·&nbsp; Relación 1:1 &nbsp;·&nbsp; '
                    'Fondo <strong style="color:var(--text);">Dark Navy</strong> &nbsp;·&nbsp; '
                    'Logo ADALIMPORT en Oro &nbsp;·&nbsp; Nombre del producto &nbsp;·&nbsp; Sin precio'
                    '</span></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.error("Error generando la versión IG Post.")

        # ── TAB: Instagram Story ───────────────────────────────────────────────
        with _tab_story:
            if _bstry:
                _c1, _c2, _c3 = st.columns([1.5, 1, 1.5])
                with _c2:
                    st.image(_bstry, use_container_width=True)
                st.download_button(
                    label="⬇️  Descargar · IG Story (PNG 1080×1920)",
                    data=_bstry,
                    file_name=f"ADALIMPORT_{_nombre_arch}_IG_Story.png",
                    mime="image/png",
                    use_container_width=True,
                    key=f"ev_dl_story_{_key_sfx}",
                )
                st.markdown(
                    f'<div style="background:rgba(184,150,62,0.04);border:1px solid rgba(184,150,62,0.18);'
                    f'border-radius:8px;padding:9px 13px;margin-top:8px;">'
                    f'<span style="font-family:var(--font-mono);font-size:0.58rem;color:var(--gold);">◈ Especificaciones</span><br>'
                    f'<span style="font-family:var(--font-body);font-size:0.76rem;color:var(--muted);">'
                    f'1080×1920 px &nbsp;·&nbsp; Relación 9:16 &nbsp;·&nbsp; '
                    f'Fondo <strong style="color:var(--text);">Dark Navy</strong> &nbsp;·&nbsp; '
                    f'Logo + Nombre + Precio <strong style="color:var(--gold);">${_ev_precio:.2f}</strong> en badge Verde Neón'
                    f'</span></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.error("Error generando la versión IG Story.")

        # ── TAB: WhatsApp ──────────────────────────────────────────────────────
        with _tab_wa:
            if _big:
                st.markdown(
                    '<div style="background:rgba(0,230,118,0.04);border:1px solid rgba(0,230,118,0.18);'
                    'border-left:3px solid rgba(0,230,118,0.5);border-radius:0 8px 8px 0;'
                    'padding:10px 14px;margin-bottom:14px;">'
                    '<span style="font-family:var(--font-mono);font-size:0.60rem;color:var(--neon);">'
                    '💬 WhatsApp usa la imagen del IG Post</span><br>'
                    '<span style="font-family:var(--font-body);font-size:0.78rem;color:var(--muted);">'
                    'El formato 1080×1080 con branding es el estándar para catálogos y estados de '
                    '<strong style="color:var(--text);">WhatsApp Business</strong>. '
                    'Descárgala desde la pestaña IG Post.'
                    '</span></div>',
                    unsafe_allow_html=True,
                )
                _c1, _c2, _c3 = st.columns([1, 2, 1])
                with _c2:
                    st.image(_big, use_container_width=True)
                st.download_button(
                    label="⬇️  Descargar · WhatsApp (PNG 1080×1080)",
                    data=_big,
                    file_name=f"ADALIMPORT_{_nombre_arch}_WhatsApp.png",
                    mime="image/png",
                    use_container_width=True,
                    key=f"ev_dl_wa_{_key_sfx}",
                )
            else:
                st.error("Error generando la imagen para WhatsApp.")
