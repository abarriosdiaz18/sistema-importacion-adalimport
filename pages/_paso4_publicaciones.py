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
#  ADALIMPORT — pages/_paso4_publicaciones.py  ·  v1.0 (Paso 4 del Pipeline Wizard)
#  Consola de Ventas — Generador de Copys y Publicaciones
#
#  Versión: refactor de _publicaciones.py con:
#    1. Barra wizard render_wizard_nav(paso_actual=4).
#    2. Guard suave (banner informativo, no bloqueante) si no hay lote activo.
#    3. Estudio Visual ELIMINADO de esta página (vive en _paso2_estudio.py).
#    4. Deposita "copys_generados_ok" en session_state al generar el primer copy
#       (contrato del pipeline — marca Paso 4 completado).
#    5. El resto de la lógica de copys, ZIP masivo y selector de historial
#       se mantiene IDÉNTICO al original.
#
#  Módulos core: generador_publicaciones.py — NO SE MODIFICA.
#  Comunicación: EXCLUSIVAMENTE via st.session_state.
# ══════════════════════════════════════════════════════════════════════════════

# ── Componentes del wizard ────────────────────────────────────────────────────
try:
    from modules._wizard_nav      import render_wizard_nav
    from modules._estado_pipeline import marcar_copys_generados, resetear_pipeline
    _WIZARD_OK = True
except ImportError:
    _WIZARD_OK = False
    def render_wizard_nav(paso_actual: int) -> None: pass
    def marcar_copys_generados() -> None: pass
    def resetear_pipeline() -> None: pass

# ── Design System ─────────────────────────────────────────────────────────────
from styles_adalimport import aplicar_estilos
aplicar_estilos()

# ── Módulos core ──────────────────────────────────────────────────────────────
from generador_publicaciones import (
    generar_titulo, generar_descripcion, generar_copy_instagram,
    extraer_puntos_clave,
)
from config_envios import COMISION_ML
import config_envios as cfg

try:
    from db_manager import obtener_todos_los_lotes, obtener_lote_por_id, obtener_items_por_lote
    _DB_DISPONIBLE = True
except Exception:
    _DB_DISPONIBLE = False

# ══════════════════════════════════════════════════════════════════════════════
# BARRA WIZARD
# ══════════════════════════════════════════════════════════════════════════════
render_wizard_nav(paso_actual=4)

# ══════════════════════════════════════════════════════════════════════════════
# PLANTILLAS GLOBALES (idénticas al original)
# ══════════════════════════════════════════════════════════════════════════════
METODOS_PAGO  = ["Efectivo", "Pago Móvil", "Transferencia", "Binance (USDT)", "PayPal"]
METODOS_ENVIO = ["Retiro personal en San Bernardino (Caracas)", "MRW", "ZOOM"]
GARANTIA      = "3 días por defectos de fábrica"

_BLOQUE_PAGO_ML = (
    "=========================================\n"
    "💳 MÉTODOS DE PAGO:\n"
    "=========================================\n\n"
    + "\n".join(f"• {m}" for m in METODOS_PAGO)
)
_BLOQUE_ENVIO_ML = (
    "=========================================\n"
    "📍 ENTREGA Y ENVÍOS:\n"
    "=========================================\n\n"
    + "\n".join(f"• {e}" for e in METODOS_ENVIO)
    + "\n📦 El costo de envío corre por cuenta del comprador."
)

# ══════════════════════════════════════════════════════════════════════════════
# FUNCIONES INTERNAS DE COPY (idénticas al original)
# ══════════════════════════════════════════════════════════════════════════════
def _copy_mercadolibre(titulo: str, precio: float, descripcion: str = "", marca: str = "") -> tuple:
    """Genera (título_ml, descripción_ml) optimizados para MercadoLibre Venezuela."""
    puntos = extraer_puntos_clave(descripcion, max_puntos=6)
    ficha  = "\n".join(f"• {p.strip().capitalize()}." for p in puntos) if puntos else "• Producto importado de USA.\n• Original y garantizado."
    desc_ml = f"""ADALIMPORT — Importado directamente de USA 🇺🇸

=========================================
📦 DESCRIPCIÓN:
=========================================

{ficha}

=========================================
💰 PRECIO: ${precio:.2f}
=========================================

⚠️ Consultar disponibilidad antes de ofertar.
Respondemos a la brevedad posible.

{_BLOQUE_ENVIO_ML}

{_BLOQUE_PAGO_ML}

=========================================
🛡️ GARANTÍA:
=========================================

{GARANTIA}
"""
    return titulo, desc_ml


def _copy_instagram(titulo: str, precio: float, descripcion: str = "") -> str:
    """Genera copy corto para Instagram."""
    puntos  = extraer_puntos_clave(descripcion, max_puntos=3)
    bullets = "\n".join(f"✅ {p.capitalize()}" for p in puntos) if puntos else \
              "✅ Original importado\n✅ Disponible en Caracas\n✅ Envíos a todo el país"
    return f"""🔥 {titulo} 🔥

{bullets}

💰 Precio: ${precio:.2f}

📍 Caracas · Envíos nacionales
📩 Escríbenos para apartar el tuyo

#ADALIMPORT #Venezuela #Caracas #ImportadoUSA"""


def _copy_whatsapp(titulo: str, precio: float, descripcion: str = "") -> str:
    """Genera copy para WhatsApp / catálogo."""
    puntos  = extraer_puntos_clave(descripcion, max_puntos=4)
    bullets = "\n".join(f"• {p.strip().capitalize()}." for p in puntos) if puntos else \
              "• Original importado de USA.\n• Disponible en Caracas."
    return f"""*{titulo}*

{bullets}

💵 Precio: *${precio:.2f}*
📍 Caracas · Envíos nacionales (MRW / ZOOM)
💳 {" · ".join(METODOS_PAGO[:3])}
🛡️ {GARANTIA}

Escríbenos para apartar ✉️"""


# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div style="background:linear-gradient(135deg,rgba(13,20,36,0.9) 0%,rgba(5,9,15,0.95) 100%);
            border:1px solid rgba(184,150,62,0.2);border-top:2px solid var(--gold);
            border-radius:14px;padding:20px 24px;margin-bottom:20px;
            display:flex;align-items:center;gap:16px;">
  <span style="font-size:2rem;line-height:1;
               filter:drop-shadow(0 0 10px rgba(184,150,62,0.4));">✍️</span>
  <div style="flex:1">
    <div style="font-family:'DM Mono',monospace;font-size:0.58rem;letter-spacing:3px;
                text-transform:uppercase;color:var(--gold);margin-bottom:4px;">
      Pipeline · Paso 4 de 4
    </div>
    <div style="font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:800;
                color:var(--text);line-height:1.1;margin-bottom:4px;">
      Publicaciones <span style="color:var(--gold);">y Copys</span>
    </div>
    <div style="font-family:'Inter',sans-serif;font-size:0.82rem;color:var(--muted);">
      Genera títulos y descripciones optimizadas para MercadoLibre, Instagram y WhatsApp.
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# GUARD SUAVE — Banner si no hay lote activo (no bloqueante)
# A diferencia de los pasos 2 y 3, aquí se permite acceso sin lote
# porque el usuario puede generar copys manualmente.
# ══════════════════════════════════════════════════════════════════════════════
_lote_mkt          = st.session_state.get("lote_activo_marketing")
_tiene_lote        = bool(_lote_mkt and _lote_mkt.get("resultados"))
_tiene_lote_sesion = bool(st.session_state.get("resultados_lote"))

if "pub_modo_manual" not in st.session_state:
    st.session_state["pub_modo_manual"] = False

# Banner de llegada desde Paso 3
_acaba_de_llegar = st.session_state.pop("_llegada_pub", False)
if _acaba_de_llegar:
    _lote_id_arr = (
        st.session_state.get("lote_id")
        or st.session_state.get("_lote_id_reg", "")
    )
    st.markdown(f"""
    <div style="background:rgba(13,26,13,0.9);border:1px solid var(--neon);
                border-radius:8px;padding:0.8rem 1.2rem;margin-bottom:1rem;
                font-family:var(--font-body);font-size:0.85rem;color:var(--neon);">
        ✅ <strong>Lote <span style="font-family:var(--font-mono);">{_lote_id_arr}</span>
        listo</strong> — Selecciona un producto del panel lateral para generar su publicación.
    </div>""", unsafe_allow_html=True)

# Banner informativo si no hay lote (guard suave — no bloquea)
if not _tiene_lote and not _tiene_lote_sesion and not st.session_state["pub_modo_manual"]:
    st.markdown("""
    <div style="background:rgba(184,150,62,0.06);border:1px solid rgba(184,150,62,0.25);
                border-left:3px solid var(--gold);border-radius:10px;
                padding:1.1rem 1.4rem;margin-bottom:1.2rem;
                font-family:'Inter',sans-serif;">
        <div style="font-family:'DM Mono',monospace;font-size:0.58rem;letter-spacing:3px;
                    text-transform:uppercase;color:var(--gold);margin-bottom:6px;">
            ℹ Sin lote activo
        </div>
        <div style="font-size:0.88rem;color:#e2e8f0;margin-bottom:10px;">
            Completa el <strong style="color:var(--gold);">Paso 1</strong> para cargar
            automáticamente los productos del lote aquí.
            También puedes generar copys manualmente sin un lote.
        </div>
    </div>
    """, unsafe_allow_html=True)

    _gc1, _gc2, _gc3 = st.columns([1, 1, 2])
    with _gc1:
        if st.button("← Volver al Paso 1", key="pub_btn_volver_paso1", use_container_width=True):
            st.session_state["pagina_activa"] = "paso1"
            st.rerun()
    with _gc2:
        if st.button("Modo manual →", key="pub_btn_modo_manual", use_container_width=True):
            st.session_state["pub_modo_manual"] = True
            st.rerun()
    if not st.session_state["pub_modo_manual"]:
        st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR DE HISTORIAL (idéntico al original)
# ══════════════════════════════════════════════════════════════════════════════
if _DB_DISPONIBLE:
    with st.sidebar:
        st.markdown(
            '<div style="font-family:var(--font-mono);font-size:0.60rem;letter-spacing:2.5px;'
            'text-transform:uppercase;color:var(--gold);margin-bottom:8px;">◈ Historial de Lotes</div>',
            unsafe_allow_html=True,
        )
        try:
            _lotes_hist    = obtener_todos_los_lotes() or []
            _PLACEHOLDER_HIST = "— Selecciona un lote —"
            _opts_map = {f"{l.get('lote_id_text','?')} · {l.get('fecha','?')} · {l.get('modo','?')}": l.get("lote_id_text","") for l in _lotes_hist}
            _opciones_hist = [_PLACEHOLDER_HIST] + list(_opts_map.keys())

            _sel_hist  = st.selectbox("Lote archivado:", _opciones_hist, key="pub_sel_historial")
            _btn_cargar_hist = st.button("Cargar lote", key="pub_btn_cargar_hist",
                                          use_container_width=True,
                                          disabled=(_sel_hist == _PLACEHOLDER_HIST))

            if _btn_cargar_hist and _sel_hist != _PLACEHOLDER_HIST:
                _lote_id_rec = _opts_map.get(_sel_hist, "")
                if _lote_id_rec:
                    try:
                        _header_rec = obtener_lote_por_id(_lote_id_rec)
                        _items_rec  = obtener_items_por_lote(_lote_id_rec)
                        if _items_rec:
                            _resultados_mapped = [
                                {
                                    "nombre":             _it.get("nombre", ""),
                                    "cantidad":           _it.get("cantidad", 1),
                                    "tienda":             _it.get("tienda", ""),
                                    "precio_tienda":      _it.get("costo_unitario", 0),
                                    "envio_courier":      _it.get("flete_individual", 0),
                                    "costo_real":         _it.get("costo_real", 0),
                                    "precio_ml":          _it.get("precio_venta", 0),
                                    "precio_ml_objetivo": _it.get("precio_venta", 0),
                                    "ganancia_objetivo":  _it.get("ganancia_neta", 0),
                                    "margen_pct":         _it.get("margen_pct", 0),
                                }
                                for _it in _items_rec
                            ]
                            st.session_state["resultados_lote"]       = _resultados_mapped
                            st.session_state["lote_activo_marketing"] = {
                                "lote_id":          _lote_id_rec,
                                "modo":             "aereo" if str(_header_rec.get("modo","")) == "Aéreo" else "maritimo",
                                "courier":          _header_rec.get("courier", ""),
                                "resultados":       _resultados_mapped,
                                "origen_historial": True,
                            }
                            st.session_state["_llegada_pub"]    = True
                            st.session_state["_lote_id_reg"]    = _lote_id_rec
                            st.session_state["lote_id"]         = _lote_id_rec
                            st.session_state["pub_modo_manual"] = False
                            st.success(f"✅ **{_lote_id_rec}** cargado — {len(_resultados_mapped)} producto(s).")
                            st.rerun()
                        else:
                            st.warning(f"El lote **{_lote_id_rec}** no tiene ítems registrados.")
                    except Exception as _exc_hist:
                        st.error(f"Error al recuperar el lote: {_exc_hist}")

            if st.button("🗑️ Limpiar", key="pub_btn_limpiar", use_container_width=True):
                for _kl in ["lote_activo_marketing", "resultados_lote", "_zip_listo",
                            "_zip_n_archivos", "_lote_id_reg", "_desc_temporales",
                            "_pub_copy_ml", "_pub_copy_ig", "_pub_copy_wa"]:
                    st.session_state.pop(_kl, None)
                st.session_state["pub_modo_manual"] = False
                st.rerun()

        except Exception as _e_sidebar:
            st.caption(f"Historial no disponible: {_e_sidebar}")

# ══════════════════════════════════════════════════════════════════════════════
# DATOS DEL LOTE PARA PUBLICACIONES
# ══════════════════════════════════════════════════════════════════════════════
_resultados_lote = st.session_state.get("resultados_lote", [])
_cat             = st.session_state.get("catalogo_df", None)

def _resolver_desc_marca(nombre_prod: str):
    """Extrae marca y descripción del catálogo para un nombre dado."""
    if _cat is None:
        return "", ""
    import pandas as pd
    _col_nom = next((c for c in _cat.columns if "product" in c or c == "nombre"), None)
    _col_des = next((c for c in _cat.columns if "descr" in c), None)
    _col_mar = next((c for c in _cat.columns if "marc" in c), None)
    if not _col_nom:
        return "", ""
    _row = _cat[_cat[_col_nom].astype(str).str.lower() == nombre_prod.lower()]
    if _row.empty:
        return "", ""
    _marca = str(_row.iloc[0][_col_mar]).strip() if _col_mar and _col_mar in _row else ""
    _desc  = str(_row.iloc[0][_col_des]).strip() if _col_des and _col_des in _row else ""
    return _marca if _marca.lower() != "nan" else "", _desc if _desc.lower() != "nan" else ""

# ══════════════════════════════════════════════════════════════════════════════
# BANNER DE LOTE ACTIVO + TRIGGER MASIVO
# ══════════════════════════════════════════════════════════════════════════════
if _tiene_lote or _tiene_lote_sesion:
    _n_lote = len(_resultados_lote)
    _lote_id_disp = (
        (_lote_mkt or {}).get("lote_id")
        or st.session_state.get("lote_id")
        or st.session_state.get("_lote_id_reg", "—")
    )

    _col_banner, _col_masivo_b = st.columns([3, 1])
    with _col_banner:
        st.markdown(
            f'<div style="background:rgba(0,230,118,0.06);border:1px solid rgba(0,230,118,0.20);'
            f'border-radius:8px;padding:10px 14px;">'
            f'<span style="font-family:var(--font-mono);font-size:0.62rem;color:var(--neon);">'
            f'● Lote activo: <strong>{_lote_id_disp}</strong> · {_n_lote} producto(s)</span></div>',
            unsafe_allow_html=True,
        )
    with _col_masivo_b:
        _btn_masivo = st.button(
            "📦 Pack Masivo (ZIP)",
            use_container_width=True,
            key="btn_masivo_top",
            help=f"Genera un .txt con los 3 copys por cada uno de los {_n_lote} productos",
        )
    if _btn_masivo:
        st.session_state["_trigger_masivo"] = True
        st.rerun()

    st.markdown('<hr style="border:none;border-top:1px solid rgba(184,150,62,0.10);margin:4px 0 20px 0;">',
                unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ESTADO INTERNO
# ══════════════════════════════════════════════════════════════════════════════
for _key, _default in [
    ("_pub_nombre", ""), ("_pub_marca", ""), ("_pub_precio", 0.00),
    ("_pub_desc", ""), ("_pub_sel_ant", "— nuevo producto —"),
]:
    if _key not in st.session_state:
        st.session_state[_key] = _default

# ══════════════════════════════════════════════════════════════════════════════
# LAYOUT: PANEL LATERAL DE SELECCIÓN + CONSOLA DE COPY
# ══════════════════════════════════════════════════════════════════════════════
_col_lista, _col_consola = st.columns([1, 2], gap="medium")

# ── Panel lateral: selector de productos del lote ─────────────────────────────
with _col_lista:
    st.markdown(
        '<div style="font-family:var(--font-mono);font-size:0.60rem;letter-spacing:2.5px;'
        'text-transform:uppercase;color:var(--gold);margin-bottom:10px;">◈ Productos del lote</div>',
        unsafe_allow_html=True,
    )

    _opciones_prod = ["— nuevo producto —"] + [r.get("nombre","") for r in _resultados_lote]

    _sel_prod = st.selectbox(
        "Selecciona producto:", _opciones_prod,
        key="pub_sel_producto",
        label_visibility="collapsed",
    )

    # Auto-carga de datos del producto seleccionado
    if _sel_prod != "— nuevo producto —" and _sel_prod != st.session_state["_pub_sel_ant"]:
        st.session_state["_pub_sel_ant"] = _sel_prod
        _item_sel = next((r for r in _resultados_lote if r.get("nombre") == _sel_prod), {})
        _marca_r, _desc_r = _resolver_desc_marca(_sel_prod)
        st.session_state["_pub_nombre"] = _sel_prod
        st.session_state["_pub_marca"]  = _marca_r
        st.session_state["_pub_precio"] = float(_item_sel.get("precio_ml_objetivo",
                                                  _item_sel.get("precio_ml", 0)) or 0)
        st.session_state["_pub_desc"]   = _desc_r
        st.rerun()

    # Mini-tabla del lote
    if _resultados_lote:
        st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
        for _r in _resultados_lote:
            _precio_r  = float(_r.get("precio_ml_objetivo", _r.get("precio_ml", 0)) or 0)
            _decision  = _r.get("decision", "")
            _color_dec = "#00E676" if "COMPRAR" in _decision else ("#f87171" if "INVIABLE" in _decision or "NO" in _decision else "#B8963E")
            _es_sel    = _r.get("nombre") == _sel_prod
            _bg        = "rgba(184,150,62,0.10)" if _es_sel else "transparent"
            _brd       = "1px solid rgba(184,150,62,0.35)" if _es_sel else "1px solid transparent"

            st.markdown(f"""
            <div style="background:{_bg};border:{_brd};border-radius:7px;
                        padding:7px 10px;margin-bottom:4px;cursor:pointer;">
                <div style="font-family:'Inter',sans-serif;font-size:0.80rem;
                            color:var(--text);font-weight:{'700' if _es_sel else '400'};">
                    {_r.get('nombre','')[:38]}
                </div>
                <div style="display:flex;justify-content:space-between;margin-top:2px;">
                    <span style="font-family:var(--font-mono);font-size:0.65rem;color:var(--muted);">
                        ${_precio_r:.2f}
                    </span>
                    <span style="font-family:var(--font-mono);font-size:0.58rem;color:{_color_dec};">
                        {_decision.split()[0] if _decision else '—'}
                    </span>
                </div>
            </div>""", unsafe_allow_html=True)

# ── Consola de generación de copy ─────────────────────────────────────────────
with _col_consola:
    st.markdown(
        '<div style="font-family:var(--font-mono);font-size:0.60rem;letter-spacing:2.5px;'
        'text-transform:uppercase;color:var(--gold);margin-bottom:10px;">◈ Generador de Publicación</div>',
        unsafe_allow_html=True,
    )

    _c_nom, _c_mar = st.columns([2, 1])
    with _c_nom:
        _pub_nombre = st.text_input("Nombre del producto", value=st.session_state["_pub_nombre"],
                                     key="pub_inp_nombre")
    with _c_mar:
        _pub_marca  = st.text_input("Marca", value=st.session_state["_pub_marca"],
                                     key="pub_inp_marca")

    _pub_precio = st.number_input(
        "Precio ML objetivo (USD)", min_value=0.0, step=0.5,
        value=float(st.session_state["_pub_precio"]),
        key="pub_inp_precio",
    )

    _pub_desc = st.text_area(
        "Descripción del producto (pega desde la tienda origen)",
        value=st.session_state["_pub_desc"],
        height=120, key="pub_inp_desc",
        placeholder="Pega aquí la descripción original del producto para que la IA extraiga los puntos clave...",
    )

    # ── Botón de generación ────────────────────────────────────────────────────
    _btn_generar = st.button(
        "✨  Generar Publicación",
        key="pub_btn_generar",
        type="primary",
        use_container_width=True,
    )

    if _btn_generar:
        if not _pub_nombre.strip():
            st.warning("Ingresa el nombre del producto.")
        else:
            _titulo_gen     = generar_titulo(_pub_nombre, _pub_marca, _pub_desc)
            _titulo_ml, _desc_ml = _copy_mercadolibre(_titulo_gen, _pub_precio, _pub_desc, _pub_marca)
            _copy_ig        = _copy_instagram(_titulo_gen, _pub_precio, _pub_desc)
            _copy_wa        = _copy_whatsapp(_titulo_gen, _pub_precio, _pub_desc)

            st.session_state["_pub_copy_ml"] = (_titulo_ml, _desc_ml)
            st.session_state["_pub_copy_ig"] = _copy_ig
            st.session_state["_pub_copy_wa"] = _copy_wa

            # Marcar Paso 4 completado (contrato del pipeline)
            marcar_copys_generados()
            st.rerun()

    # ── Mostrar copys generados ────────────────────────────────────────────────
    if st.session_state.get("_pub_copy_ml"):
        _titulo_ml, _desc_ml = st.session_state["_pub_copy_ml"]
        _copy_ig = st.session_state.get("_pub_copy_ig", "")
        _copy_wa = st.session_state.get("_pub_copy_wa", "")

        _tab_ml, _tab_ig, _tab_wa = st.tabs(["📦 MercadoLibre", "📸 Instagram", "💬 WhatsApp"])

        with _tab_ml:
            st.markdown(f"""
            <div style="background:var(--navy-lt);border:1px solid rgba(184,150,62,0.2);
                        border-radius:8px;padding:10px 14px;margin-bottom:8px;">
                <div style="font-family:'DM Mono',monospace;font-size:0.58rem;color:var(--gold);
                            text-transform:uppercase;letter-spacing:2px;margin-bottom:4px;">Título ML</div>
                <div style="font-family:'Inter',sans-serif;font-size:0.88rem;color:var(--text);
                            font-weight:600;">{_titulo_ml}</div>
                <div style="font-family:'DM Mono',monospace;font-size:0.65rem;color:var(--muted);margin-top:4px;">
                    {len(_titulo_ml)} / 60 caracteres
                    {'✅' if len(_titulo_ml) <= 60 else '⚠️ Excede el límite'}
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.text_area("Descripción ML", value=_desc_ml, height=260, key="pub_ta_ml")
            st.download_button("⬇️ Descargar .txt ML", data=f"{_titulo_ml}\n\n{_desc_ml}".encode("utf-8"),
                               file_name=f"ML_{_pub_nombre[:30]}.txt", mime="text/plain",
                               key="dl_txt_ml", use_container_width=True)

        with _tab_ig:
            st.text_area("Copy Instagram", value=_copy_ig, height=260, key="pub_ta_ig")
            st.download_button("⬇️ Descargar .txt Instagram", data=_copy_ig.encode("utf-8"),
                               file_name=f"IG_{_pub_nombre[:30]}.txt", mime="text/plain",
                               key="dl_txt_ig", use_container_width=True)

        with _tab_wa:
            st.text_area("Copy WhatsApp", value=_copy_wa, height=260, key="pub_ta_wa")
            st.download_button("⬇️ Descargar .txt WhatsApp", data=_copy_wa.encode("utf-8"),
                               file_name=f"WA_{_pub_nombre[:30]}.txt", mime="text/plain",
                               key="dl_txt_wa", use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# GENERACIÓN MASIVA ZIP (idéntica al original)
# ══════════════════════════════════════════════════════════════════════════════
_hay_lote_para_masivo = bool(_resultados_lote) and not st.session_state.get("_reseteando", False)

if _hay_lote_para_masivo:
    st.markdown("---")
    st.markdown("""
    <div style="background:rgba(184,150,62,0.06);border:1px solid rgba(184,150,62,0.2);
                border-radius:10px;padding:14px 18px;margin-bottom:12px;
                display:flex;align-items:center;gap:14px;">
        <span style="font-size:1.6rem;">📦</span>
        <div>
            <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:1rem;
                        color:var(--text);">Generación Masiva del Lote</div>
            <div style="font-family:'Inter',sans-serif;font-size:0.78rem;color:var(--muted);margin-top:2px;">
                Un .txt por producto con los 3 copys (ML · Instagram · WhatsApp) listos para copiar y pegar.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Preparar productos con datos de descripción
    _desc_temporales = st.session_state.get("_desc_temporales", {})
    _productos_pub   = []
    _hay_sin_desc    = False

    for _idx_p, _r in enumerate(_resultados_lote):
        _nombre_p = _r.get("nombre", "")
        _precio_p = float(_r.get("precio_ml_objetivo", _r.get("precio_ml", 0)) or 0)
        _marca_p, _desc_p = _resolver_desc_marca(_nombre_p)
        # Recuperar descripción temporal si fue ingresada
        _desc_tmp_key = f"idx{_idx_p}_{_nombre_p}"
        if _desc_temporales.get(_desc_tmp_key):
            _desc_p = _desc_temporales[_desc_tmp_key]
        _productos_pub.append({
            "nombre": _nombre_p, "precio": _precio_p,
            "marca": _marca_p,   "desc": _desc_p,
        })
        if not _desc_p:
            _hay_sin_desc = True

    if _hay_sin_desc:
        with st.expander("⚠️ Productos sin descripción — ingresa manualmente (opcional)", expanded=False):
            for _idx_p, _p in enumerate(_productos_pub):
                if not _p["desc"]:
                    _key_ta   = f"lote_desc_tmp_idx{_idx_p}"
                    _desc_tmp = st.text_area(
                        f"Descripción para «{_p['nombre']}»",
                        value=_desc_temporales.get(f"idx{_idx_p}_{_p['nombre']}", ""),
                        placeholder="Pega aquí la descripción del producto...",
                        height=80, key=_key_ta,
                    )
                    if _desc_tmp:
                        _desc_temporales[f"idx{_idx_p}_{_p['nombre']}"] = _desc_tmp
                        _p["desc"] = _desc_tmp
            st.session_state["_desc_temporales"] = _desc_temporales

    st.markdown('<hr style="border:none;border-top:1px solid rgba(184,150,62,0.1);margin:0.2rem 0 1rem 0">',
                unsafe_allow_html=True)

    _trigger_masivo = st.session_state.pop("_trigger_masivo", False)

    _btn_generar_zip = st.button(
        "📦  Generar Pack de Publicaciones Masivas (ZIP)",
        use_container_width=True,
        key="btn_generar_zip",
    )

    if _btn_generar_zip or _trigger_masivo:
        import zipfile, io, re as _re_zip

        _zip_buffer         = io.BytesIO()
        _archivos_generados = []

        with zipfile.ZipFile(_zip_buffer, "w", zipfile.ZIP_DEFLATED) as _zf:
            for _p in _productos_pub:
                _tb          = generar_titulo(_p["nombre"], _p["marca"], _p["desc"])
                _tm, _dm     = _copy_mercadolibre(_tb, _p["precio"], _p["desc"], _p["marca"])
                _ci          = _copy_instagram(_tb, _p["precio"], _p["desc"])
                _cw          = _copy_whatsapp(_tb, _p["precio"], _p["desc"])

                _sep = "═" * 55
                _contenido = f"""{_sep}
{_p["nombre"].upper()}
{_sep}

━━━ MERCADOLIBRE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TÍTULO: {_tm}

- - - - - - - - - - - - - - - - - - - - - - - - - - -

{_dm}

━━━ INSTAGRAM ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{_ci}

━━━ WHATSAPP ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{_cw}

{_sep}
Generado por ADALIMPORT · Precio ML: ${_p["precio"]:.2f}
{_sep}
"""
                _nombre_arch = _re_zip.sub(r'[^a-zA-Z0-9_\- ]', '', _p["nombre"]).strip()
                _nombre_arch = _nombre_arch.replace(" ", "_")[:50]
                _zf.writestr(f"{_nombre_arch}.txt", _contenido.encode("utf-8"))
                _archivos_generados.append(_nombre_arch)

        _zip_buffer.seek(0)
        st.session_state["_zip_listo"]      = _zip_buffer.getvalue()
        st.session_state["_zip_n_archivos"] = len(_archivos_generados)
        # Marcar Paso 4 completado también con generación masiva
        marcar_copys_generados()
        st.rerun()

    # ── Franja de éxito ZIP ───────────────────────────────────────────────────
    if st.session_state.get("_zip_listo") is not None:
        _n_zip = st.session_state["_zip_n_archivos"]
        _col_msg, _col_dl, _col_home = st.columns([3.2, 1.2, 1.2])

        with _col_msg:
            st.markdown(
                f'<div style="background:rgba(0,230,118,0.08);border:1px solid rgba(0,230,118,0.32);'
                f'border-radius:10px;padding:12px 16px;display:flex;align-items:center;gap:10px;">'
                f'<span style="font-size:1.4rem;">✅</span>'
                f'<div><div style="font-family:\'DM Mono\',monospace;font-size:0.72rem;'
                f'color:#00E676;font-weight:700;">{_n_zip} publicación(es) generada(s)</div>'
                f'<div style="font-family:\'Inter\',sans-serif;font-size:0.75rem;color:#3a8a5a;">'
                f'ZIP listo · {_n_zip} archivos .txt</div></div></div>',
                unsafe_allow_html=True,
            )
        with _col_dl:
            st.download_button(
                "⬇️ ZIP",
                data=st.session_state["_zip_listo"],
                file_name=f"ADALIMPORT_publicaciones_{_lote_id_disp if (_tiene_lote or _tiene_lote_sesion) else 'lote'}.zip",
                mime="application/zip",
                use_container_width=True,
                type="primary",
                key="dl_zip_masivo",
            )
        with _col_home:
            if st.button("🏠 Nuevo lote", use_container_width=True, key="pub_btn_nuevo_lote"):
                for _kl in ["_zip_listo", "_zip_n_archivos", "lote_activo_marketing",
                             "resultados_lote", "_pub_copy_ml", "_pub_copy_ig", "_pub_copy_wa"]:
                    st.session_state.pop(_kl, None)
                st.session_state["pub_modo_manual"] = False
                st.session_state["pagina_activa"]   = "paso1"
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# CIERRE DE CICLO — Bloque final del Pipeline
# ──────────────────────────────────────────────────────────────────────────────
# Aparece siempre al final del Paso 4, una vez que el paso está completado
# (al menos un copy generado). Ofrece dos opciones:
#   A) Nuevo lote completo  → limpia TODO y vuelve al Paso 1 desde cero
#   B) Solo resetear wizard → limpia el progreso del pipeline pero mantiene
#      los datos del catálogo y configuración
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.get("copys_generados_ok"):

    st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(5,9,15,0.98) 0%, rgba(13,20,36,0.95) 100%);
        border: 1px solid rgba(184,150,62,0.25);
        border-top: 2px solid #B8963E;
        border-radius: 14px;
        padding: 24px 28px;
        margin-top: 8px;
    ">
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:6px;">
            <span style="font-size:1.6rem; filter:drop-shadow(0 0 8px rgba(184,150,62,0.5));">🏁</span>
            <div>
                <div style="font-family:'DM Mono',monospace; font-size:0.58rem; letter-spacing:3px;
                            text-transform:uppercase; color:#B8963E; margin-bottom:3px;">
                    Pipeline completado
                </div>
                <div style="font-family:'Syne',sans-serif; font-size:1.15rem; font-weight:800;
                            color:#e2e8f0; line-height:1.1;">
                    ¿Qué hacemos ahora?
                </div>
            </div>
        </div>
        <div style="font-family:'Inter',sans-serif; font-size:0.80rem; color:#64748b;
                    margin-top:6px; padding-left:44px;">
            Los 4 pasos del lote están completos. Elige cómo continuar.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    _cc1, _cc2 = st.columns(2)

    with _cc1:
        # Opción A — Nuevo lote completo (limpieza total)
        st.markdown("""
        <div style="background:rgba(0,230,118,0.05); border:1px solid rgba(0,230,118,0.2);
                    border-radius:10px; padding:14px 16px; margin-bottom:10px; min-height:80px;">
            <div style="font-family:'DM Mono',monospace; font-size:0.62rem; letter-spacing:2px;
                        text-transform:uppercase; color:#00E676; margin-bottom:5px;">
                ★  Comenzar desde cero
            </div>
            <div style="font-family:'Inter',sans-serif; font-size:0.78rem; color:#64748b;">
                Limpia <strong style="color:#94a3b8;">todos</strong> los datos del lote,
                imágenes, copys y catálogo. El sistema queda listo para un lote completamente nuevo.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(
            "➕  Nuevo Lote Completo",
            key="cierre_btn_nuevo_lote",
            use_container_width=True,
            type="primary",
        ):
            # Limpieza completa via el router — igual que "Cargar Nuevo Lote"
            # Limpiamos manualmente todas las claves conocidas del pipeline
            _claves_limpiar = [
                "lote_id", "_lote_id_reg", "_lote_aprobado", "_estado_apr",
                "resultados_lote", "_lote_modo", "_lote_costo_total",
                "_lote_ganancia", "_lote_env_total", "_lote_origen",
                "lote_activo_marketing", "productos", "catalogo_df",
                "excel_urls_imagenes", "excel_bytes_cms", "copys_generados_ok",
                "ev_paso2_completado", "_zip_listo", "_zip_n_archivos",
                "_pub_copy_ml", "_pub_copy_ig", "_pub_copy_wa",
                "_reporte_resultados", "_reporte_modo", "_reporte_lote_id",
                "_reporte_costo", "_reporte_ganancia", "_reporte_env",
                "_wizard_nav_css_v20", "pub_modo_manual", "_llegada_pub",
                "excel_lote_en_Estudio_Visual", "confirm_limpiar", "_cat_preview",
            ]
            for _k in _claves_limpiar:
                st.session_state.pop(_k, None)
            # Incrementar contador del uploader para forzar reset de file_uploader
            st.session_state["_uploader_counter"] = (
                st.session_state.get("_uploader_counter", 0) + 1
            )
            st.session_state["productos"]       = []
            st.session_state["courier_sel"]     = None
            st.session_state["pagina_activa"]   = "paso1"
            st.rerun()

    with _cc2:
        # Opción B — Solo resetear el wizard (mantiene catálogo y config)
        st.markdown("""
        <div style="background:rgba(184,150,62,0.05); border:1px solid rgba(184,150,62,0.18);
                    border-radius:10px; padding:14px 16px; margin-bottom:10px; min-height:80px;">
            <div style="font-family:'DM Mono',monospace; font-size:0.62rem; letter-spacing:2px;
                        text-transform:uppercase; color:#B8963E; margin-bottom:5px;">
                Nuevo lote · mismo catálogo
            </div>
            <div style="font-family:'Inter',sans-serif; font-size:0.78rem; color:#64748b;">
                Reinicia el pipeline (pasos 1-4) pero conserva el catálogo CSV y la
                configuración de courier. Útil para procesar otro lote del mismo proveedor.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(
            "🔄  Nuevo Lote · Mismo Catálogo",
            key="cierre_btn_resetear_wizard",
            use_container_width=True,
            type="secondary",
        ):
            # Limpieza parcial — solo datos del lote, no el catálogo
            _claves_lote = [
                "lote_id", "_lote_id_reg", "_lote_aprobado", "_estado_apr",
                "resultados_lote", "_lote_modo", "_lote_costo_total",
                "_lote_ganancia", "_lote_env_total", "_lote_origen",
                "lote_activo_marketing", "productos",
                "excel_urls_imagenes", "excel_bytes_cms", "copys_generados_ok",
                "ev_paso2_completado", "_zip_listo", "_zip_n_archivos",
                "_pub_copy_ml", "_pub_copy_ig", "_pub_copy_wa",
                "_reporte_resultados", "_reporte_modo", "_reporte_lote_id",
                "_reporte_costo", "_reporte_ganancia", "_reporte_env",
                "_wizard_nav_css_v20", "pub_modo_manual", "_llegada_pub",
                "excel_lote_en_Estudio_Visual", "_estado_apr",
            ]
            for _k in _claves_lote:
                st.session_state.pop(_k, None)
            st.session_state["productos"]     = []
            st.session_state["pagina_activa"] = "paso1"
            st.rerun()

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
