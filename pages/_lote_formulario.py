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

TIENDAS = ["— Selecciona una tienda —", "Amazon", "eBay", "Walmart", "AliExpress", "Otro"]

# ══════════════════════════════════════════════════════════════════════════════
# MÓDULO: _lote_formulario
# Responsabilidad: selección de modo/origen, carga de catálogo Excel,
#                  previsualización, formulario manual, tabla del lote actual.
# Comunicación: SOLO via st.session_state
# ══════════════════════════════════════════════════════════════════════════════

def render_formulario():
    """Renderiza el bloque completo de entrada de datos del lote."""

    # ── Toast dispatcher — al inicio del ciclo de render ─────────────────────
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

    # ══════════════════════════════════════════════════════════════════════
    # PASO 1 — CARGAR ARCHIVO
    # ══════════════════════════════════════════════════════════════════════
    with st.expander(
        "📂  Paso 1 — Cargar archivo de catálogo",
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
            "📤  Sube tu productos_catalogo.xlsx",
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

    # ══════════════════════════════════════════════════════════════════════
    # PASO 2 — PREVISUALIZAR Y SELECCIONAR
    # ══════════════════════════════════════════════════════════════════════
    if st.session_state._cat_preview is not None:
        cat_prev = st.session_state._cat_preview

        activos = cat_prev[
            (cat_prev["activo"].astype(str).str.upper() == "TRUE") &
            (cat_prev["producto"].notna()) &
            (cat_prev["producto"].astype(str).str.strip() != "") &
            (cat_prev["producto"].astype(str).str.lower() != "nan")
        ]

        with st.expander("👁  Paso 2 — Revisar catálogo cargado", expanded=True):
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

    # ══════════════════════════════════════════════════════════════════════
    # PASO 3 — AGREGAR MANUALMENTE
    # ══════════════════════════════════════════════════════════════════════
    with st.expander("➕  Agregar producto manualmente"):
        if "_form_key" not in st.session_state:
            st.session_state._form_key = 0
        fk = st.session_state._form_key

        r1c1, r1c2, r1c3 = st.columns(3)
        n_nombre = r1c1.text_input("Producto", placeholder="Ej: Audífonos Sony WH-1000XM5", key=f"n_nombre_{fk}")
        n_tienda = r1c2.selectbox("Tienda", TIENDAS, key=f"n_tienda_{fk}")
        n_costo  = r1c3.number_input("Precio ($)", min_value=0.0, value=None, placeholder="29.99", key=f"n_costo_{fk}")

        r2c1, r2c2, r2c3, r2c4, r2c5, r2c6 = st.columns([1, 1.2, 1, 1, 1, 1.1])
        n_cant  = r2c1.number_input("Cant.", min_value=1, value=1, step=1, key=f"n_cant_{fk}")
        n_peso  = r2c2.number_input("Peso (lb)", min_value=0.0, value=None, placeholder="1.50", key=f"n_peso_{fk}")

        n_unidad_dims = r2c6.selectbox(
            "Unidad dims", ["— Selecciona —", "in (pulgadas)", "ft (pies)"],
            key=f"n_udims_{fk}", help="Selecciona la unidad."
        )
        _dims_en_ft = "ft" in n_unidad_dims
        _ph = "ft" if _dims_en_ft else "in"
        n_largo = r2c3.number_input(f"Largo ({_ph})", min_value=0.0, value=None, placeholder=_ph, key=f"n_largo_{fk}")
        n_ancho = r2c4.number_input(f"Ancho ({_ph})", min_value=0.0, value=None, placeholder=_ph, key=f"n_ancho_{fk}")
        n_alto  = r2c5.number_input(f"Alto ({_ph})",  min_value=0.0, value=None, placeholder=_ph, key=f"n_alto_{fk}")

        r3c1, r3c2, r3c3 = st.columns(3)
        n_tax_man  = r3c1.number_input("Tax %", min_value=0.0, value=None, placeholder="0.00", key=f"n_tax_{fk}")
        n_env_int  = r3c2.number_input("Env. interno ($)", min_value=0.0, value=None, placeholder="0.00", key=f"n_envint_{fk}")
        n_tax_incl = r3c3.checkbox("Tax incluido en precio", key=f"n_taxincl_{fk}")

        errores_form = []
        if not n_nombre or not str(n_nombre).strip():       errores_form.append("nombre")
        if n_tienda == "— Selecciona una tienda —":         errores_form.append("tienda")
        if not n_costo or float(n_costo or 0) <= 0:         errores_form.append("costo")
        if not n_peso  or float(n_peso  or 0) <= 0:         errores_form.append("peso")
        tiene_dims = (
            (n_largo is not None and float(n_largo) > 0) or
            (n_ancho is not None and float(n_ancho) > 0) or
            (n_alto  is not None and float(n_alto)  > 0)
        )
        if tiene_dims and n_unidad_dims == "— Selecciona —":
            errores_form.append("unidad de medida")

        if st.button("➕ Agregar al lote", key=f"btn_agregar_{fk}", use_container_width=True):
            if errores_form:
                faltantes = {
                    "nombre": "Nombre", "tienda": "Tienda", "costo": "Precio",
                    "peso": "Peso", "unidad de medida": "Unidad Dims"
                }
                st.session_state._toast_pending = (
                    f"Faltan campos obligatorios: {', '.join(faltantes[e] for e in errores_form)}",
                    "error"
                )
                st.rerun()
            else:
                def _to_in(val):
                    if val is None: return None
                    return round(float(val) * 12, 2) if _dims_en_ft else float(val)

                st.session_state.productos.append({
                    "nombre":        str(n_nombre).strip(),
                    "costo":         float(n_costo),
                    "tienda":        n_tienda,
                    "descripcion":   "",
                    "peso_real":     float(n_peso),
                    "largo":         _to_in(n_largo),
                    "ancho":         _to_in(n_ancho),
                    "alto":          _to_in(n_alto),
                    "cantidad":      int(n_cant),
                    "tax_manual":    (float(n_tax_man) / 100) if n_tax_man and float(n_tax_man) > 0 else None,
                    "envio_interno": float(n_env_int)  if n_env_int  and float(n_env_int)  > 0 else None,
                    "tax_incluido":  n_tax_incl,
                })
                st.session_state._form_key += 1
                st.rerun()

    # ── Limpiar lote con confirmación ─────────────────────────────────────────
    _col_limpiar, _ = st.columns([1, 3])
    with _col_limpiar:
        if not st.session_state.confirm_limpiar:
            if st.button("🗑 Limpiar lote", use_container_width=True):
                st.session_state.confirm_limpiar = True
                st.rerun()
        else:
            st.markdown("<small style='color:#FF1744'>¿Seguro?</small>", unsafe_allow_html=True)
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

    # ── Tabla del lote actual ──────────────────────────────────────────────────
    if st.session_state.productos:
        df_lote = pd.DataFrame([
            {
                "nombre":    p.get("nombre",""),
                "tienda":    p.get("tienda",""),
                "cantidad":  p.get("cantidad",""),
                "costo":     p.get("costo",""),
                "peso_real": p.get("peso_real",""),
                "largo":     p.get("largo") if p.get("largo") else None,
                "ancho":     p.get("ancho") if p.get("ancho") else None,
                "alto":      p.get("alto")  if p.get("alto")  else None,
            }
            for p in st.session_state.productos
        ])
        st.dataframe(df_lote, width="stretch", hide_index=True, column_config={
            "nombre":   st.column_config.TextColumn("Producto"),
            "tienda":   st.column_config.TextColumn("Tienda"),
            "cantidad": st.column_config.NumberColumn("Cant.", format="%d"),
            "costo":    st.column_config.NumberColumn("Precio tienda $", format="$%.2f"),
            "peso_real":st.column_config.NumberColumn("Peso lb", format="%.2f"),
            "largo":    st.column_config.NumberColumn('L"', format="%d"),
            "ancho":    st.column_config.NumberColumn('A"', format="%d"),
            "alto":     st.column_config.NumberColumn('H"', format="%d"),
        })

        nombres   = [p["nombre"] for p in st.session_state.productos]
        to_remove = st.selectbox("Eliminar producto:", ["— seleccionar —"] + nombres, key="remove_sel")
        if to_remove != "— seleccionar —":
            if st.button(f"Eliminar «{to_remove}»"):
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
                    <div style="font-family:Space Mono,monospace;color:#FF6D00;font-size:0.9rem;
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
                        💡 Agrega LARGO × ANCHO × ALTO (in) en tu catálogo para un cálculo exacto.
                    </div>
                </div>""", unsafe_allow_html=True)

    # ── Devolver modo y origen al orquestador via session_state ──────────────
    st.session_state["_form_modo"]   = modo
    st.session_state["_form_origen"] = origen_key
    st.session_state["_form_origen_envio"] = origen_envio
