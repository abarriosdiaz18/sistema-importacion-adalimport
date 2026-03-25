import sys, os as _os, builtins as _builtins
# ── FIX sys.path ──────────────────────────────────────────────────────────────
_ROOT   = getattr(_builtins, "_ADALIMPORT_ROOT",   _os.getcwd())
_DB_DIR = getattr(_builtins, "_ADALIMPORT_DB_DIR", _os.path.join(_ROOT, "database"))
for _p in (_DB_DIR, _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)
# ─────────────────────────────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import math as _math
from config_envios import COURIERS as _COURIERS, COMISION_ML

# ── Helpers locales (no cruzan módulos) ──────────────────────────────────────
def _safe_float(val, default=0.0):
    try:
        if val is None or (isinstance(val, float) and _math.isnan(val)): return default
        return float(val)
    except: return default

def _safe_int(val, default=1):
    try:
        if val is None or (isinstance(val, float) and _math.isnan(val)): return default
        return int(float(val))
    except: return default

def _safe_str(val, default=""):
    try:
        if val is None or (isinstance(val, float) and _math.isnan(val)): return default
        s = str(val).strip()
        return default if s.lower() == 'nan' else s
    except: return default

# ── Toast (fallback silencioso si no está disponible) ────────────────────────
try:
    from _toast_system import toast as _toast
except ImportError:
    def _toast(msg, tipo="info"): pass

TIENDAS = ["Amazon", "eBay", "Walmart", "AliExpress", "Otro"]

# ══════════════════════════════════════════════════════════════════════════════
# MÓDULO: _lote_formulario  v2.0  (Rediseño A+C)
#   A — CSS elimina botones ± de number_input. Navegación Tab/Enter limpia.
#   C — Formulario nativo con inputs Streamlit (sin canvas/data_editor).
# Comunicación: SOLO via st.session_state
# ══════════════════════════════════════════════════════════════════════════════

# ── CSS: Formulario limpio — sin botones ±/× ni bordes rojos ────────────────
st.markdown("""
<style>
/* ════════════════════════════════════════════════════════════════════════════
   ADALIMPORT — _lote_formulario overrides
   Objetivo: inputs limpios, sin botones ± ni ×, sin bordes rojos de foco.
════════════════════════════════════════════════════════════════════════════ */

/* ── 1. Ocultar botones ± (step up/down) por testid Y por aria-label ──────── */
button[data-testid="stNumberInputStepDown"],
button[data-testid="stNumberInputStepUp"],
button[aria-label="increment"],
button[aria-label="decrement"],
[data-testid="stNumberInput"] button {
    display: none !important;
    width: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    border: none !important;
    overflow: hidden !important;
}

/* ── 2. Ocultar botón × (clear) del number_input ─────────────────────────── */
button[data-testid="stNumberInputClearButton"],
[data-testid="stNumberInput"] > div > button,
input[type="number"] + button,
.stNumberInput button {
    display: none !important;
}

/* ── 3. Quitar el borde naranja/rojo de foco en TODOS los inputs ──────────── */
input:focus,
input:focus-visible,
select:focus,
select:focus-visible,
textarea:focus,
[data-baseweb="input"]:focus-within,
[data-baseweb="select"]:focus-within,
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus,
[data-testid="stSelectbox"] [data-baseweb="select"]:focus-within {
    outline: none !important;
    box-shadow: 0 0 0 1px rgba(184,150,62,0.45) !important;
    border-color: rgba(184,150,62,0.45) !important;
}

/* ── 4. Estado hover de inputs ───────────────────────────────────────────── */
[data-testid="stTextInput"] input:hover,
[data-testid="stNumberInput"] input:hover {
    border-color: rgba(184,150,62,0.3) !important;
}

/* ── 5. Quitar anillo rojo/naranja nativo del browser en number ──────────── */
input[type="number"] {
    -moz-appearance: textfield !important;
}
input[type="number"]::-webkit-outer-spin-button,
input[type="number"]::-webkit-inner-spin-button {
    -webkit-appearance: none !important;
    margin: 0 !important;
}

/* ── 6. Contenedor number_input: quitar padding extra que dejaban los ± ───── */
[data-testid="stNumberInput"] > div {
    gap: 0 !important;
}
[data-testid="stNumberInput"] input {
    border-radius: 6px !important;
}

/* ── 7. Upload zone ──────────────────────────────────────────────────────── */
div[data-testid="stFileUploader"] {
    border: 1px dashed rgba(184,150,62,0.25) !important;
    border-radius: 10px !important;
    padding: 0.2rem 0.5rem !important;
    background: rgba(184,150,62,0.02) !important;
    transition: border-color 0.2s;
}
div[data-testid="stFileUploader"]:hover {
    border-color: rgba(184,150,62,0.5) !important;
}

/* ── 8. Expander header ──────────────────────────────────────────────────── */
details summary {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.75rem !important;
    letter-spacing: 1.2px !important;
    text-transform: uppercase !important;
    color: #64748b !important;
}
details[open] summary { color: #B8963E !important; }

/* ── 9. Selectbox: quitar borde rojo de foco ─────────────────────────────── */
[data-baseweb="select"] > div:focus-within,
[data-baseweb="select"] > div:focus {
    border-color: rgba(184,150,62,0.45) !important;
    box-shadow: 0 0 0 1px rgba(184,150,62,0.3) !important;
    outline: none !important;
}

/* ── 10. Label del file uploader ─────────────────────────────────────────── */
div[data-testid="stFileUploader"] label {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 1px !important;
    color: #94a3b8 !important;
    text-transform: uppercase !important;
}
</style>
""", unsafe_allow_html=True)


def render_formulario():
    """Renderiza el bloque completo de entrada de datos del lote. v2.0"""

    # ── Toast dispatcher ─────────────────────────────────────────────────────
    if "_toast_pending" in st.session_state:
        _msg, _tipo = st.session_state.pop("_toast_pending")
        _toast(_msg, _tipo)

    # ── Detección de cambio de modo ───────────────────────────────────────────
    _modo_anterior = st.session_state.get("_modo_activo_prev", None)

    modo_envio = st.radio(
        "Modo de envío:",
        ["✈️  Aéreo", "🚢  Marítimo"],
        horizontal=True, key="modo_envio_radio"
    )
    modo = "aereo" if "Aéreo" in modo_envio else "maritimo"

    if _modo_anterior is not None and _modo_anterior != modo:
        for _k in ("resultados_lote", "_lote_env_total", "_lote_costo_total",
                   "_lote_ganancia", "_lote_modo", "_estado_apr"):
            st.session_state.pop(_k, None)
        st.session_state.pop("_id_sugerido_cache_AER", None)
        st.session_state.pop("_id_sugerido_cache_MAR", None)
    st.session_state["_modo_activo_prev"] = modo

    # ── Origen del envío ──────────────────────────────────────────────────────
    courier_sel = st.session_state.get("courier_sel", None)
    _origenes_disponibles = (
        _COURIERS[courier_sel].get("origenes", ["us", "cn"])
        if courier_sel and courier_sel in _COURIERS else ["us", "cn"]
    )
    _opciones_origen = []
    if "us" in _origenes_disponibles: _opciones_origen.append("🇺🇸  USA")
    if "cn" in _origenes_disponibles: _opciones_origen.append("🇨🇳  China")

    origen_envio = st.radio(
        "Origen:", _opciones_origen, horizontal=True, key="origen_envio_radio"
    )
    origen_key = "us" if "USA" in origen_envio else "cn"

    # ── Banner de tarifas ─────────────────────────────────────────────────────
    _cfg_modo        = _COURIERS[courier_sel][modo][origen_key]
    _consolidado     = _COURIERS[courier_sel].get("consolidado_dias")
    _consolidado_txt = (
        f'&nbsp;·&nbsp; <span style="color:#555">📦 Consolida {_consolidado} días</span>'
        if _consolidado else ''
    )

    if modo == "aereo":
        _tarifa_str = f'${_cfg_modo["tarifa_lb"]:.2f}/lb'
        _minimo_str = (
            f'mín {_cfg_modo["minimo_lb"]} lb · ${_cfg_modo["minimo_usd"]:.2f}'
            if _cfg_modo["minimo_lb"] else f'mín ${_cfg_modo["minimo_usd"]:.2f}'
        )
        st.markdown(f"""
        <div style="background:#0D120D;border:1px solid #2a4a2a;border-radius:8px;
                    padding:0.6rem 1rem;font-size:0.8rem;color:#aaa;margin-bottom:0.8rem">
        ✈️ <b style="color:#00E676">Aéreo</b> · {"🇺🇸 USA" if "USA" in origen_envio else "🇨🇳 China"} → 🇻🇪 Venezuela &nbsp;·&nbsp;
        <b style="color:#888">{courier_sel}</b> &nbsp;·&nbsp;
        Tarifa: <b style="color:#FFD600">{_tarifa_str}</b> &nbsp;·&nbsp; <b style="color:#FFD600">{_minimo_str}</b>{_consolidado_txt}
        </div>""", unsafe_allow_html=True)
    else:
        _tarifa_str = f'${_cfg_modo["tarifa_ft3"]:.2f}/ft³'
        _minimo_str = f'mín {_cfg_modo["minimo_ft3"]:.2f} ft³ · ${_cfg_modo["minimo_usd"]:.2f}'
        st.markdown(f"""
        <div style="background:#0D1020;border:1px solid #2a2a4a;border-radius:8px;
                    padding:0.6rem 1rem;font-size:0.8rem;color:#aaa;margin-bottom:0.8rem">
        🚢 <b style="color:#7B8CDE">Marítimo</b> · {"🇺🇸 USA" if "USA" in origen_envio else "🇨🇳 China"} → 🇻🇪 Venezuela &nbsp;·&nbsp;
        <b style="color:#888">{courier_sel}</b> &nbsp;·&nbsp;
        Tarifa: <b style="color:#FFD600">{_tarifa_str}</b> &nbsp;·&nbsp; <b style="color:#FFD600">{_minimo_str}</b> &nbsp;·&nbsp;
        <span style="color:#555">~30-45 días · cálculo por volumen</span>{_consolidado_txt}
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-title">Productos del lote</div>', unsafe_allow_html=True)

    # ── Inicializar estado ────────────────────────────────────────────────────
    if "productos"        not in st.session_state: st.session_state.productos       = []
    if "confirm_limpiar"  not in st.session_state: st.session_state.confirm_limpiar = False
    if "_cat_preview"     not in st.session_state: st.session_state._cat_preview    = None

    # ══════════════════════════════════════════════════════════════════════════
    # BLOQUE 1 — CARGAR ARCHIVO EXCEL
    # ══════════════════════════════════════════════════════════════════════════
    with st.expander(
        "📂  Cargar catálogo Excel",
        expanded=st.session_state._cat_preview is None and not st.session_state.productos
    ):
        try:
            import io as _io
            import openpyxl as _opxl
            _wb_tpl = _opxl.Workbook()
            _ws_tpl = _wb_tpl.active
            _ws_tpl.title = "catalogo"
            _ws_tpl.append(["PRODUCTO","MARCA","TIENDA","COSTO","PESO","LARGO","ANCHO","ALTO",
                             "CANTIDAD","DESCRIPCION","LINK","ACTIVO"])
            _ws_tpl.append(["Ej: Pilas AAA Energizer 4pk","Energizer","Amazon",
                             12.99,0.25,5,2,3,10,"Pilas recargables 1500mAh","https://amazon.com/...","TRUE"])
            _buf_tpl = _io.BytesIO()
            _wb_tpl.save(_buf_tpl)
            _buf_tpl.seek(0)
            st.download_button(
                label="📥  Descargar Plantilla Excel",
                data=_buf_tpl,
                file_name="productos_catalogo_plantilla.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                help="Descarga la plantilla con el formato correcto para ADALIMPORT"
            )
        except Exception:
            pass

        st.markdown("<div style='margin:0.6rem 0'></div>", unsafe_allow_html=True)

        _up_key  = f"cat_uploader_{st.session_state.get('_uploader_counter', 0)}"
        uploaded = st.file_uploader(
            "Sube tu productos_catalogo.xlsx",
            type=["xlsx", "xlsm"],
            help="Sube el archivo con la hoja 'catalogo' en el formato de la plantilla",
            key=_up_key
        )

        if uploaded:
            try:
                df_up = pd.read_excel(uploaded, sheet_name="catalogo")
                df_up.columns = (df_up.columns.str.strip().str.lower()
                                 .str.replace(r"[^a-záéíóúñ_]","_",regex=True)
                                 .str.replace(r"_+","_",regex=True).str.strip("_"))
                rename_map = {}
                for col in df_up.columns:
                    if col.startswith("product"): rename_map[col]="producto"
                    elif col.startswith("marc"):  rename_map[col]="marca"
                    elif col.startswith("descr"): rename_map[col]="descripcion"
                    elif col.startswith("peso"):  rename_map[col]="peso_lb"
                    elif col.startswith("larg"):  rename_map[col]="largo_in"
                    elif col.startswith("anch"):  rename_map[col]="ancho_in"
                    elif col.startswith("alt"):   rename_map[col]="alto_in"
                    elif col.startswith("cant"):  rename_map[col]="cantidad"
                    elif col.startswith("tiend"): rename_map[col]="tienda"
                    elif col.startswith("cost"):  rename_map[col]="costo"
                    elif col.startswith("link") or col.startswith("url"): rename_map[col]="link"
                    elif col.startswith("activ"): rename_map[col]="activo"
                df_up = df_up.rename(columns=rename_map)
                st.session_state.catalogo_df  = df_up
                st.session_state._cat_preview = df_up
                _toast("Catálogo cargado correctamente.", "success")
            except Exception as e:
                err_msg = str(e)
                _es_formato = any(k in err_msg.lower() for k in ("catalogo","worksheet","sheet"))
                if _es_formato:
                    st.markdown("""
                    <div style="background:#1A0000;border:1px solid #FF1744;border-radius:8px;
                                padding:1rem 1.2rem;font-size:0.82rem;color:#ccc;margin-top:0.5rem">
                    <b style="color:#FF1744">Formato incorrecto</b><br><br>
                    El archivo debe tener una hoja llamada <b>catalogo</b> con las columnas de la plantilla.<br>
                    Descarga la plantilla arriba para ver el formato requerido.
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background:#1A0000;border:1px solid #FF1744;border-radius:8px;
                                padding:0.8rem 1.2rem;font-size:0.82rem;color:#ccc;margin-top:0.5rem">
                    <b style="color:#FF1744">Error al leer el archivo</b> — {err_msg}
                    </div>""", unsafe_allow_html=True)

    # ── Preview del catálogo cargado ──────────────────────────────────────────
    if st.session_state._cat_preview is not None:
        cat_prev = st.session_state._cat_preview

        activos = cat_prev[
            (cat_prev["activo"].astype(str).str.upper() == "TRUE") &
            (cat_prev["producto"].notna()) &
            (cat_prev["producto"].astype(str).str.strip() != "") &
            (cat_prev["producto"].astype(str).str.lower() != "nan")
        ]

        with st.expander("👁  Revisar catálogo cargado", expanded=True):
            if activos.empty:
                _toast("No hay productos con ACTIVO=TRUE en el catálogo.", "warning")
            else:
                total_cat  = len(cat_prev[cat_prev["producto"].notna() & (cat_prev["producto"].astype(str).str.lower() != "nan")])
                total_act  = len(activos)
                total_cost = sum(_safe_float(r.get("costo")) * _safe_int(r.get("cantidad"),1) for _, r in activos.iterrows())

                r1, r2, r3 = st.columns(3)
                r1.markdown(f'''<div class="kpi-card">
                    <div class="kpi-label">Productos en catálogo</div>
                    <div class="kpi-value kpi-white">{total_cat}</div>
                </div>''', unsafe_allow_html=True)
                r2.markdown(f'''<div class="kpi-card">
                    <div class="kpi-label">Activos para este lote</div>
                    <div class="kpi-value kpi-green">{total_act}</div>
                </div>''', unsafe_allow_html=True)
                r3.markdown(f'''<div class="kpi-card">
                    <div class="kpi-label">Costo estimado productos</div>
                    <div class="kpi-value kpi-yellow">${total_cost:.2f}</div>
                </div>''', unsafe_allow_html=True)

                filas_prev = ""
                for _, row in activos.iterrows():
                    filas_prev += f"""<tr>
                        <td><b>{_safe_str(row.get("producto"))}</b></td>
                        <td style="color:#888">{_safe_str(row.get("marca"))}</td>
                        <td style="color:#888">{_safe_str(row.get("tienda","Amazon"))}</td>
                        <td style="color:#FFD600;text-align:center">{_safe_int(row.get("cantidad"),1)}</td>
                        <td style="color:#FFD600;text-align:center">${_safe_float(row.get("costo")):.2f}</td>
                        <td style="color:#888;text-align:center">{_safe_float(row.get("peso_lb")):.2f} lb</td>
                    </tr>"""
                st.markdown(f"""
                <table class="res-table">
                    <thead><tr>
                        <th>Producto</th><th>Marca</th><th>Tienda</th>
                        <th>Cantidad</th><th>Costo</th><th>Peso</th>
                    </tr></thead>
                    <tbody>{filas_prev}</tbody>
                </table>""", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                if st.button("⚡  CARGAR ESTE LOTE AL ANALIZADOR", use_container_width=True, type="primary"):
                    nuevos = 0
                    nombres_actuales = [p["nombre"] for p in st.session_state.productos]
                    for _, row in activos.iterrows():
                        nombre = _safe_str(row.get("producto",""))
                        if nombre and nombre not in nombres_actuales:
                            st.session_state.productos.append({
                                "nombre":      nombre,
                                "costo":       _safe_float(row.get("costo"), 0.0),
                                "tienda":      _safe_str(row.get("tienda"), "Amazon"),
                                "descripcion": _safe_str(row.get("descripcion", "")),
                                "peso_real":   _safe_float(row.get("peso_lb"), 0.0),
                                "largo":       _safe_int(row.get("largo_in", row.get("largo")), 0) or None,
                                "ancho":       _safe_int(row.get("ancho_in", row.get("ancho")), 0) or None,
                                "alto":        _safe_int(row.get("alto_in",  row.get("alto")),  0) or None,
                                "cantidad":    _safe_int(row.get("cantidad"), 1),
                                "tax_manual": None, "envio_interno": None, "tax_incluido": False,
                            })
                            nuevos += 1
                    st.session_state._cat_preview = None
                    _toast(f"{nuevos} productos cargados al lote.", "success")
                    st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # BLOQUE 2 — FORMULARIO NATIVO (inputs Streamlit — sin data_editor/canvas)
    # Elimina el bug de doble-Tab y el borde rojo del Glide Data Grid.
    # ══════════════════════════════════════════════════════════════════════════

    # ── Separador ────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="display:flex;align-items:center;gap:1rem;margin:1.2rem 0 1rem 0">
        <div style="flex:1;height:1px;background:linear-gradient(90deg,transparent,#1c2a42)"></div>
        <span style="font-family:'DM Mono',monospace;font-size:0.65rem;letter-spacing:2px;
                     color:#4a5568;text-transform:uppercase;white-space:nowrap">
            ✦ Agregar producto manualmente
        </span>
        <div style="flex:1;height:1px;background:linear-gradient(90deg,#1c2a42,transparent)"></div>
    </div>""", unsafe_allow_html=True)

    # ── Form key — reset limpio tras cada "Agregar" ───────────────────────────
    if "_form_key" not in st.session_state:
        st.session_state._form_key = 0
    _fk = st.session_state._form_key

    # ── Fila 1: Producto · Tienda · Precio · Cantidad ─────────────────────────
    _fc1, _fc2, _fc3, _fc4 = st.columns([3, 1.4, 1.2, 0.8])
    _f_nombre = _fc1.text_input(
        "Producto", placeholder="Ej: Audífonos Sony WH-1000XM5",
        key=f"fi_nombre_{_fk}", label_visibility="collapsed"
    )
    _f_tienda = _fc2.selectbox(
        "Tienda", TIENDAS, key=f"fi_tienda_{_fk}", label_visibility="collapsed"
    )
    _f_precio = _fc3.number_input(
        "Precio ($)", min_value=0.0, value=None, placeholder="$ Precio",
        key=f"fi_precio_{_fk}", label_visibility="collapsed"
    )
    _f_cant = _fc4.number_input(
        "Cant.", min_value=1, value=1, step=1,
        key=f"fi_cant_{_fk}", label_visibility="collapsed"
    )

    # ── Labels fila 1 ────────────────────────────────────────────────────────
    st.markdown("""
    <div style="display:grid;grid-template-columns:3fr 1.4fr 1.2fr 0.8fr;
                gap:0.5rem;margin:-0.45rem 0 0.6rem 0">
        <span style="font-family:'DM Mono',monospace;font-size:0.58rem;color:#4a5568;
                     letter-spacing:1px;padding-left:2px">PRODUCTO *</span>
        <span style="font-family:'DM Mono',monospace;font-size:0.58rem;color:#4a5568;
                     letter-spacing:1px;padding-left:2px">TIENDA *</span>
        <span style="font-family:'DM Mono',monospace;font-size:0.58rem;color:#4a5568;
                     letter-spacing:1px;padding-left:2px">PRECIO USD *</span>
        <span style="font-family:'DM Mono',monospace;font-size:0.58rem;color:#4a5568;
                     letter-spacing:1px;padding-left:2px">CANT.</span>
    </div>""", unsafe_allow_html=True)

    # ── Fila 2: Peso · L · A · H ─────────────────────────────────────────────
    _fd1, _fd2, _fd3, _fd4 = st.columns([1.5, 1, 1, 1])
    _f_peso  = _fd1.number_input(
        "Peso lb", min_value=0.0, value=None, placeholder="Peso (lb)",
        key=f"fi_peso_{_fk}", label_visibility="collapsed"
    )
    _f_largo = _fd2.number_input(
        "Largo in", min_value=0.0, value=None, placeholder='L" (in)',
        key=f"fi_largo_{_fk}", label_visibility="collapsed"
    )
    _f_ancho = _fd3.number_input(
        "Ancho in", min_value=0.0, value=None, placeholder='A" (in)',
        key=f"fi_ancho_{_fk}", label_visibility="collapsed"
    )
    _f_alto  = _fd4.number_input(
        "Alto in", min_value=0.0, value=None, placeholder='H" (in)',
        key=f"fi_alto_{_fk}", label_visibility="collapsed"
    )

    # ── Labels fila 2 ────────────────────────────────────────────────────────
    st.markdown("""
    <div style="display:grid;grid-template-columns:1.5fr 1fr 1fr 1fr;
                gap:0.5rem;margin:-0.45rem 0 0.9rem 0">
        <span style="font-family:'DM Mono',monospace;font-size:0.58rem;color:#4a5568;
                     letter-spacing:1px;padding-left:2px">PESO LB *</span>
        <span style="font-family:'DM Mono',monospace;font-size:0.58rem;color:#4a5568;
                     letter-spacing:1px;padding-left:2px">LARGO"</span>
        <span style="font-family:'DM Mono',monospace;font-size:0.58rem;color:#4a5568;
                     letter-spacing:1px;padding-left:2px">ANCHO"</span>
        <span style="font-family:'DM Mono',monospace;font-size:0.58rem;color:#4a5568;
                     letter-spacing:1px;padding-left:2px">ALTO"</span>
    </div>""", unsafe_allow_html=True)

    # ── Validación ────────────────────────────────────────────────────────────
    _nombre_ok = bool(_f_nombre and str(_f_nombre).strip())
    _precio_ok = bool(_f_precio is not None and float(_f_precio or 0) > 0)
    _peso_ok   = bool(_f_peso   is not None and float(_f_peso   or 0) > 0)
    _form_ok   = _nombre_ok and _precio_ok and _peso_ok

    # ── Botones ───────────────────────────────────────────────────────────────
    _col_btn, _col_clear = st.columns([3, 1])
    with _col_btn:
        if st.button(
            "＋  AGREGAR AL LOTE",
            key=f"btn_agregar_{_fk}",
            use_container_width=True,
            type="primary",
            disabled=not _form_ok
        ):
            _nombre = str(_f_nombre).strip()
            if _nombre in {p["nombre"] for p in st.session_state.productos}:
                st.session_state["_toast_pending"] = (f"«{_nombre}» ya está en el lote.", "warning")
            else:
                st.session_state.productos.append({
                    "nombre":        _nombre,
                    "costo":         float(_f_precio or 0),
                    "tienda":        str(_f_tienda or "Amazon"),
                    "descripcion":   "",
                    "peso_real":     float(_f_peso  or 0),
                    "largo":         int(_f_largo or 0) or None,
                    "ancho":         int(_f_ancho or 0) or None,
                    "alto":          int(_f_alto  or 0) or None,
                    "cantidad":      int(_f_cant  or 1),
                    "tax_manual":    None,
                    "envio_interno": None,
                    "tax_incluido":  False,
                })
                st.session_state._form_key += 1
                st.session_state["_toast_pending"] = (f"«{_nombre}» agregado al lote.", "success")
            st.rerun()

    with _col_clear:
        if st.button("↺  Limpiar", key=f"btn_clear_{_fk}", use_container_width=True):
            st.session_state._form_key += 1
            st.rerun()

    # ── Separador ─────────────────────────────────────────────────────────────
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # ── Limpiar lote completo con confirmación ────────────────────────────────
    _col_limpiar, _ = st.columns([1, 3])
    with _col_limpiar:
        if not st.session_state.confirm_limpiar:
            if st.button("🗑  Limpiar lote", use_container_width=True):
                st.session_state.confirm_limpiar = True
                st.rerun()
        else:
            st.markdown("<small style='color:#FF1744'>¿Seguro? Esto borra el lote completo.</small>", unsafe_allow_html=True)
            c_yes, c_no = st.columns(2)
            with c_yes:
                if st.button("✅ Sí", use_container_width=True):
                    st.session_state.productos        = []
                    st.session_state.confirm_limpiar  = False
                    st.session_state._cat_preview     = None
                    st.session_state._estado_apr      = "idle"
                    if "resultados_lote" in st.session_state:
                        del st.session_state["resultados_lote"]
                    st.rerun()
            with c_no:
                if st.button("❌ No", use_container_width=True):
                    st.session_state.confirm_limpiar = False
                    st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # TABLA DEL LOTE ACTUAL (productos ya confirmados)
    # ══════════════════════════════════════════════════════════════════════════
    if st.session_state.productos:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:1rem;margin:1.4rem 0 0.8rem 0">
            <div style="flex:1;height:1px;background:linear-gradient(90deg,transparent,#1c2a42)"></div>
            <span style="font-family:'DM Mono',monospace;font-size:0.65rem;letter-spacing:2px;
                         color:#B8963E;text-transform:uppercase;white-space:nowrap">
                ✦ Lote actual — {n} producto{s}
            </span>
            <div style="flex:1;height:1px;background:linear-gradient(90deg,#1c2a42,transparent)"></div>
        </div>
        """.replace("{n}", str(len(st.session_state.productos)))
           .replace("{s}", "s" if len(st.session_state.productos) != 1 else ""),
        unsafe_allow_html=True)

        df_lote = pd.DataFrame([
            {
                "Producto":  p.get("nombre",""),
                "Tienda":    p.get("tienda",""),
                "Cant.":     p.get("cantidad",""),
                "$ Precio":  p.get("costo",""),
                "Peso lb":   p.get("peso_real",""),
                'L "':       p.get("largo") if p.get("largo") else "—",
                'A "':       p.get("ancho") if p.get("ancho") else "—",
                'H "':       p.get("alto")  if p.get("alto")  else "—",
            }
            for p in st.session_state.productos
        ])
        st.dataframe(df_lote, use_container_width=True, hide_index=True, column_config={
            "Producto":  st.column_config.TextColumn("Producto", width="large"),
            "Tienda":    st.column_config.TextColumn("Tienda", width="small"),
            "Cant.":     st.column_config.NumberColumn("Cant.", format="%d", width="small"),
            "$ Precio":  st.column_config.NumberColumn("$ Precio", format="$%.2f", width="small"),
            "Peso lb":   st.column_config.NumberColumn("Peso lb", format="%.2f lb", width="small"),
            'L "':       st.column_config.TextColumn('L"', width="small"),
            'A "':       st.column_config.TextColumn('A"', width="small"),
            'H "':       st.column_config.TextColumn('H"', width="small"),
        })

        # ── Eliminar producto individual ──────────────────────────────────────
        nombres   = [p["nombre"] for p in st.session_state.productos]
        to_remove = st.selectbox("Eliminar producto:", ["— seleccionar —"] + nombres, key="remove_sel")
        if to_remove != "— seleccionar —":
            if st.button(f"Eliminar «{to_remove}»", key="btn_remove_prod"):
                st.session_state.productos = [p for p in st.session_state.productos if p["nombre"] != to_remove]
                st.rerun()

        st.markdown("---")

        # ── Advertencia marítimo sin dimensiones ──────────────────────────────
        def _dim_valida(val):
            try: return float(str(val).strip()) > 0.0
            except (TypeError, ValueError): return False

        modo_actual = st.session_state.get("_modo_activo_prev", "aereo")
        if modo_actual == "maritimo":
            prods_sin_dims = [
                p["nombre"] for p in st.session_state.productos
                if not (
                    _dim_valida(p.get("largo")) and
                    _dim_valida(p.get("ancho")) and
                    _dim_valida(p.get("alto"))
                )
            ]
            if prods_sin_dims:
                st.markdown(f"""
                <div style="background:#1A1000;border:2px solid #FF6D00;border-radius:10px;
                            padding:1rem 1.2rem;margin-bottom:1rem">
                    <div style="font-family:'DM Mono',monospace;color:#FF6D00;font-size:0.9rem;
                                font-weight:700;margin-bottom:0.5rem">
                        🚢 ADVERTENCIA — Modo Marítimo requiere dimensiones reales
                    </div>
                    <div style="color:#ccc;font-size:0.82rem;margin-bottom:0.8rem">
                        El envío marítimo se cobra por <b>volumen (ft³)</b>, no por peso.<br>
                        Sin dimensiones reales el cálculo será incorrecto.
                    </div>
                    <div style="color:#FF6D00;font-size:0.8rem;font-weight:700">
                        {len(prods_sin_dims)} producto(s) sin dimensiones:
                    </div>
                    <div style="color:#888;font-size:0.78rem;margin-top:0.3rem">
                        {"<br>".join(f"• {n}" for n in prods_sin_dims)}
                    </div>
                    <div style="color:#aaa;font-size:0.78rem;margin-top:0.8rem;
                                border-top:1px solid #333;padding-top:0.6rem">
                        💡 Agrega LARGO × ANCHO × ALTO en las celdas H" · A" · L" de la tabla.
                    </div>
                </div>""", unsafe_allow_html=True)

    # ── Devolver modo y origen al orquestador via session_state ──────────────
    st.session_state["_form_modo"]        = modo
    st.session_state["_form_origen"]      = origen_key
    st.session_state["_form_origen_envio"] = origen_envio
