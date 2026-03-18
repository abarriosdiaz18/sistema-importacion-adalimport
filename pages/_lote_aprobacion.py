import sys, os as _os, builtins as _builtins
# ── FIX sys.path ──────────────────────────────────────────────────────────────
_ROOT   = getattr(_builtins, "_ADALIMPORT_ROOT",   _os.getcwd())
_DB_DIR = getattr(_builtins, "_ADALIMPORT_DB_DIR", _os.path.join(_ROOT, "database"))
for _p in (_DB_DIR, _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)
# ─────────────────────────────────────────────────────────────────────────────
import streamlit as st
from datetime import date as _date
from exportador_reportes import generar_pdf_reporte

try:
    from _toast_system import toast as _toast
except ImportError:
    def _toast(msg, tipo="info"): pass

try:
    from db_manager import guardar_lote_aprobado, lote_id_existe, obtener_siguiente_id_lote
    _DB_DISPONIBLE = True
except ImportError:
    _DB_DISPONIBLE = False
    def guardar_lote_aprobado(*a, **kw): return False, 'Módulo DB no encontrado'
    def lote_id_existe(*a, **kw): return False
    def obtener_siguiente_id_lote(prefijo: str) -> str: return "001"

# ══════════════════════════════════════════════════════════════════════════════
# MÓDULO: _lote_aprobacion
# Responsabilidad: flujo idle → form → done, guardado en BD, PDF, botones
#                  de navegación a Marketing y Studio Visual.
# Comunicación: SOLO via st.session_state
# ══════════════════════════════════════════════════════════════════════════════

def render_aprobacion(_resetear_home_fn):
    """
    Renderiza el flujo completo de aprobación del lote.
    Requiere resultados_lote en session_state (post-análisis).

    Args:
        _resetear_home_fn: referencia a la función _resetear_home() del router.
    """
    if "resultados_lote" not in st.session_state or not st.session_state.resultados_lote:
        return

    st.markdown("---")
    estado_apr = st.session_state.get("_estado_apr", "idle")

    # ══════════════════════════════════════════════════════════════════════
    # ESTADO idle — Solo botón de aprobación
    # ══════════════════════════════════════════════════════════════════════
    if estado_apr == "idle":
        if st.button("✅  APROBAR LOTE", use_container_width=True):
            st.session_state._estado_apr = "form"
            st.rerun()

    # ══════════════════════════════════════════════════════════════════════
    # ESTADO form — Formulario de aprobación
    # ══════════════════════════════════════════════════════════════════════
    elif estado_apr == "form":
        res     = st.session_state.resultados_lote
        env_t   = st.session_state.get("_lote_env_total", 0)
        costo_t = st.session_state.get("_lote_costo_total", 0)
        gan_t   = st.session_state.get("_lote_ganancia", 0)
        modo_t  = st.session_state.get("_lote_modo", "aereo")

        st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&display=swap');
        .lote-id-badge {
            font-family: 'DM Mono', monospace !important;
            background: #021a09; border: 1.5px solid #00E676; border-radius: 6px;
            padding: 0.18rem 0.6rem; color: #00E676; font-size: 0.88rem;
            font-weight: 500; letter-spacing: 0.04em; display: inline-block;
        }
        .lote-id-hint { font-family: 'DM Mono', monospace; font-size: 0.7rem; color: #3a7a5a; margin-top: 3px; }
        </style>""", unsafe_allow_html=True)

        st.markdown("""
        <div style="background:#0D1A0D;border:2px solid #00E676;border-radius:12px;
                    padding:1.2rem 1.5rem;margin-top:0.5rem">
        <div style="font-family:'Space Mono',monospace;color:#00E676;font-size:1rem;
                    font-weight:700;margin-bottom:0.3rem">✅ APROBAR LOTE</div>
        <div style="font-size:0.78rem;color:#555;margin-bottom:1rem">
        El ID se genera automáticamente según el modo de envío. Puedes editarlo; se bloqueará si ya existe.
        </div>""", unsafe_allow_html=True)

        m1, m2, m3 = st.columns(3)
        m1.markdown(f'''<div class="kpi-card">
            <div class="kpi-label">Inversión total</div>
            <div class="kpi-value kpi-white">${costo_t:.2f}</div>
        </div>''', unsafe_allow_html=True)
        m2.markdown(f'''<div class="kpi-card">
            <div class="kpi-label">Courier</div>
            <div class="kpi-value kpi-yellow">${env_t:.2f}</div>
        </div>''', unsafe_allow_html=True)
        m3.markdown(f'''<div class="kpi-card">
            <div class="kpi-label">Ganancia estimada</div>
            <div class="kpi-value kpi-green">${gan_t:.2f}</div>
        </div>''', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        _prefijo_actual = "AER" if modo_t == "aereo" else "MAR"
        _color_prefijo  = "#00E676" if modo_t == "aereo" else "#7B8CDE"
        _emoji_modo     = "✈️" if modo_t == "aereo" else "🚢"

        _cache_key = f"_id_sugerido_cache_{_prefijo_actual}"
        if _cache_key not in st.session_state:
            _correlativo = obtener_siguiente_id_lote(_prefijo_actual) if _DB_DISPONIBLE else "001"
            st.session_state[_cache_key] = f"{_prefijo_actual}-{_correlativo}"
        id_sugerido = st.session_state[_cache_key]

        st.markdown(
            f'<div style="margin-bottom:0.4rem;font-size:0.75rem;color:#555;">'
            f'{_emoji_modo} Siguiente ID sugerido para <b style="color:{_color_prefijo}">'
            f'{_prefijo_actual}</b>: &nbsp;'
            f'<span class="lote-id-badge">{id_sugerido}</span></div>',
            unsafe_allow_html=True
        )

        fa1, fa2, fa3 = st.columns(3)
        with fa1:
            lote_id = st.text_input(
                "ID del lote", value=id_sugerido,
                help="AER-XXX = Aéreo · MAR-XXX = Marítimo · Editable, no se permiten duplicados.",
                key="_apr_id"
            )
            _id_editado   = (lote_id or "").strip()
            _id_duplicado = _DB_DISPONIBLE and bool(_id_editado) and lote_id_existe(_id_editado)

            if _id_duplicado:
                _toast(f"ID '{_id_editado}' ya existe en la base de datos. Cambia el ID para continuar.", "error")
            elif _id_editado and _id_editado != id_sugerido:
                st.markdown('<div class="lote-id-hint">✎ ID personalizado — único y disponible</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="lote-id-hint">⚡ ID generado automáticamente</div>', unsafe_allow_html=True)

        with fa2:
            fecha_compra = st.date_input("Fecha de compra", value=_date.today(), key="_apr_fecha")
        with fa3:
            notas_lote = st.text_input("Notas (opcional)", placeholder="Ej: Primer pedido del año", key="_apr_notas")

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        col_ok, col_cancel = st.columns([2, 1])
        with col_ok:
            _btn_disabled = _id_duplicado or not _id_editado
            if st.button(
                "💾  REGISTRAR Y APROBAR LOTE",
                use_container_width=True,
                disabled=_btn_disabled,
                help="Cambia el ID del lote — este ya existe en la base de datos." if _btn_disabled else None,
            ):
                # ── Snapshot para reportes ────────────────────────────────────
                st.session_state._reporte_resultados = list(res)
                st.session_state._reporte_modo       = modo_t
                st.session_state._reporte_lote_id    = lote_id
                st.session_state._reporte_costo      = costo_t
                st.session_state._reporte_ganancia   = gan_t
                st.session_state._reporte_env        = env_t

                # ── Doble-check ID duplicado ──────────────────────────────────
                if _DB_DISPONIBLE and lote_id_existe(lote_id):
                    _toast(f"ID '{lote_id}' ya existe en la base de datos. Modifica el ID antes de guardar.", "error")
                    st.stop()

                # ── ROI ───────────────────────────────────────────────────────
                _roi_apr = round((gan_t / costo_t * 100) if costo_t and costo_t > 0 else 0.0, 2)

                # ── Guardar en SQLite ─────────────────────────────────────────
                _db_ok = False; _db_msg = ""
                try:
                    _db_ok, _db_msg = guardar_lote_aprobado(
                        lote_id_text=lote_id, fecha=fecha_compra,
                        courier=st.session_state.get("courier_sel", ""),
                        modo=modo_t, origen=st.session_state.get("_lote_origen", ""),
                        costo_flete=env_t, inversion_total=costo_t,
                        ganancia_total=gan_t, roi=_roi_apr,
                        notas=notas_lote, resultados=res,
                    )
                except Exception as _db_exc:
                    _db_ok = False; _db_msg = f"{type(_db_exc).__name__}: {_db_exc}"

                # ── Feedback visual ───────────────────────────────────────────
                if _db_ok:
                    st.markdown("""
                    <div style="background:linear-gradient(135deg,#021a09,#042e10);border:2px solid #00E676;
                                border-radius:12px;padding:1rem 1.4rem;margin:0.6rem 0 0.3rem;
                                display:flex;align-items:center;gap:0.9rem;">
                        <span style="font-size:1.8rem;line-height:1">✅</span>
                        <div>
                            <div style="font-family:'Space Mono',monospace;color:#00E676;
                                        font-size:0.9rem;font-weight:800;letter-spacing:0.5px;">
                                Lote guardado en Base de Datos Permanente</div>
                            <div style="color:#3a8a5a;font-size:0.72rem;margin-top:2px;">
                                SQLite · <code style="color:#2a7a4a">database/adalimport.db</code>
                                &nbsp;·&nbsp; Transacción confirmada (commit ✓)
                            </div>
                        </div>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background:#1A0A00;border:2px solid #FF6D00;border-radius:10px;
                                padding:0.9rem 1.2rem;margin:0.5rem 0;">
                        <div style="color:#FF6D00;font-family:Space Mono,monospace;font-size:0.82rem;font-weight:700;">
                            ⚠️ No se pudo guardar en la base de datos
                        </div>
                        <div style="color:#aaa;font-size:0.75rem;margin-top:0.4rem;">
                            El lote sigue aprobado y puedes descargar el reporte.<br>
                            Error: <code style="color:#FF9A50">{_db_msg}</code>
                        </div>
                    </div>""", unsafe_allow_html=True)

                # ── Avanzar a "done" ──────────────────────────────────────────
                st.session_state._estado_apr  = "done"
                st.session_state._lote_id_reg = lote_id
                st.session_state._lote_aprobado = True

                for _ck in ("_id_sugerido_cache_AER", "_id_sugerido_cache_MAR"):
                    st.session_state.pop(_ck, None)

                # ── Persistencia Marketing ────────────────────────────────────
                st.session_state["lote_activo_marketing"] = {
                    "lote_id": lote_id, "modo": modo_t, "resultados": res,
                    "costo_total": costo_t, "ganancia_total": gan_t, "env_total": env_t,
                }

                # ── DataFrame para Estudio Visual ─────────────────────────────
                try:
                    import pandas as _pd_excel
                    _catalogo_df = st.session_state.get("catalogo_df")

                    def _get_category(nombre_prod):
                        if _catalogo_df is None: return ""
                        for _col in ("category", "categoria", "categoría"):
                            if _col in _catalogo_df.columns:
                                _match = _catalogo_df[
                                    _catalogo_df["producto"].astype(str).str.strip() == nombre_prod.strip()
                                ]
                                if not _match.empty:
                                    return str(_match.iloc[0][_col]).strip()
                        return ""

                    _desc_lookup = {
                        p.get("nombre", ""): p.get("descripcion", "")
                        for p in st.session_state.get("productos", [])
                    }
                    _filas_excel = []
                    for _r_ex in res:
                        _nombre_ex = _r_ex.get("nombre", "")
                        _filas_excel.append({
                            "lote_id": lote_id, "nombre": _nombre_ex,
                            "marca": _r_ex.get("marca", ""), "tienda": _r_ex.get("tienda", ""),
                            "cantidad": _r_ex.get("cantidad", 1),
                            "costo_tienda": _r_ex.get("precio_tienda", 0.0),
                            "costo_warehouse": _r_ex.get("costo_warehouse", 0.0),
                            "flete_proporcional": _r_ex.get("flete_proporcional", 0.0),
                            "costo_real": _r_ex.get("costo_real", 0.0),
                            "precio_ml_minimo": _r_ex.get("precio_ml_minimo", 0.0),
                            "precio_ml_objetivo": _r_ex.get("precio_ml_objetivo", 0.0),
                            "ganancia_objetivo": _r_ex.get("ganancia_objetivo", 0.0),
                            "margen_pct": _r_ex.get("margen_pct", 0.0),
                            "decision": _r_ex.get("decision", ""),
                            "modo_envio": modo_t,
                            "descripcion": _desc_lookup.get(_nombre_ex, ""),
                            "category": _get_category(_nombre_ex),
                            "image": "",
                        })
                    st.session_state["excel_lote_en_Estudio_Visual"] = _pd_excel.DataFrame(_filas_excel)
                except Exception as _e_df:
                    print(f"[ADALIMPORT][_lote_aprobacion] Aviso: no se pudo crear el DataFrame Web: {_e_df}")

                st.rerun()

        with col_cancel:
            if st.button("↩️  Cancelar", use_container_width=True):
                st.session_state._estado_apr = "idle"
                for _ck in ("_id_sugerido_cache_AER", "_id_sugerido_cache_MAR"):
                    st.session_state.pop(_ck, None)
                st.rerun()

    # ══════════════════════════════════════════════════════════════════════
    # ESTADO done — Pantalla de éxito post-aprobación
    # ══════════════════════════════════════════════════════════════════════
    elif estado_apr == "done":
        _res_rep  = st.session_state.get("_reporte_resultados")
        _modo_rep = st.session_state.get("_reporte_modo", "aereo")
        _id_rep   = st.session_state.get("_reporte_lote_id", "")
        _costo_r  = float(st.session_state.get("_reporte_costo",   0) or 0)
        _gan_r    = float(st.session_state.get("_reporte_ganancia", 0) or 0)
        _env_r    = float(st.session_state.get("_reporte_env",      0) or 0)

        if not _res_rep:
            _toast("No se encontraron datos del lote. Regresa al análisis y vuelve a aprobar.", "warning")
            if st.button("↩️  Volver al análisis"):
                st.session_state._estado_apr = "idle"
                st.rerun()
            return

        lote_id_reg = _id_rep
        via_txt = "AÉREO ✈️" if _modo_rep == "aereo" else "MARÍTIMO 🚢"

        # ── Banner de éxito ───────────────────────────────────────────────────
        st.markdown(f"""
        <div style="background:#0D1A0D;border:2px solid #00E676;border-radius:12px;
                    padding:1.5rem;text-align:center;margin-top:0.5rem">
            <div style="font-size:2rem;margin-bottom:0.5rem">🎉</div>
            <div style="font-family:Space Mono,monospace;color:#00E676;font-size:1.1rem;
                        font-weight:700">¡Lote {lote_id_reg} aprobado!</div>
            <div style="color:#888;font-size:0.82rem;margin-top:0.5rem">
                Guardado en Base de Datos Permanente · Vía seleccionada:
                <span style="color:#C9A84C;font-weight:700">{via_txt}</span>
            </div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── KPIs resumen ──────────────────────────────────────────────────────
        _rk1, _rk2, _rk3 = st.columns(3)
        _rk1.markdown(f'''<div class="kpi-card">
            <div class="kpi-label">Inversión Total</div>
            <div class="kpi-value kpi-white">${_costo_r:.2f}</div>
        </div>''', unsafe_allow_html=True)
        _rk2.markdown(f'''<div class="kpi-card">
            <div class="kpi-label">Flete Courier</div>
            <div class="kpi-value kpi-yellow">${_env_r:.2f}</div>
        </div>''', unsafe_allow_html=True)
        _rk3.markdown(f'''<div class="kpi-card">
            <div class="kpi-label">Ganancia Estimada</div>
            <div class="kpi-value {'kpi-green' if _gan_r >= 0 else 'kpi-red'}">${_gan_r:.2f}</div>
        </div>''', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Pre-generar PDF ───────────────────────────────────────────────────
        _html_bytes = None; _pdf_error = None
        try:
            _html_bytes = generar_pdf_reporte(
                resultados=_res_rep, modo=_modo_rep, lote_id=_id_rep,
                costo_total=_costo_r, ganancia_total=_gan_r, env_total=_env_r,
            )
        except Exception as _e_pdf:
            _pdf_error = str(_e_pdf)

        # ── CSS botones corporativos ──────────────────────────────────────────
        st.markdown("""
        <style>
        .btn-marketing-wrapper > div > button,
        .btn-marketing-wrapper .stButton > button,
        .btn-marketing-wrapper [data-testid="stBaseButton-secondary"] {
            background: linear-gradient(135deg,#002d12 0%,#004a1e 50%,#002d12 100%) !important;
            border: 2px solid #00E676 !important; color: #00E676 !important;
            font-weight: 800 !important; font-size: 1rem !important;
            font-family: 'Space Mono', monospace !important; letter-spacing: 2.5px !important;
            padding: 0.95rem 1rem !important; border-radius: 12px !important;
            box-shadow: 0 0 28px rgba(0,230,118,0.22), 0 0 60px rgba(0,230,118,0.07) !important;
            text-transform: uppercase !important; transition: all 0.25s ease !important;
        }
        .btn-marketing-wrapper > div > button:hover,
        .btn-marketing-wrapper .stButton > button:hover,
        .btn-marketing-wrapper [data-testid="stBaseButton-secondary"]:hover {
            background: linear-gradient(135deg,#004a1e 0%,#007a32 50%,#004a1e 100%) !important;
            box-shadow: 0 0 44px rgba(0,230,118,0.55), 0 0 88px rgba(0,230,118,0.20) !important;
            border-color: #00ff88 !important; color: #ffffff !important;
            transform: translateY(-2px) scale(1.01) !important;
        }
        .btn-studio-wrapper > div > button,
        .btn-studio-wrapper .stButton > button,
        .btn-studio-wrapper [data-testid="stBaseButton-secondary"],
        .btn-studio-wrapper [data-testid="stBaseButton-primary"] {
            background: linear-gradient(135deg,#1a1000 0%,#2e1e00 50%,#1a1000 100%) !important;
            border: 2px solid #B8963E !important; color: #cda434 !important;
            font-weight: 800 !important; font-size: 0.92rem !important;
            font-family: 'Space Mono', monospace !important; letter-spacing: 2px !important;
            padding: 0.95rem 1rem !important; border-radius: 12px !important;
            box-shadow: 0 0 22px rgba(184,150,62,0.20), 0 0 50px rgba(184,150,62,0.07) !important;
            text-transform: uppercase !important; transition: all 0.25s ease !important;
        }
        .btn-studio-wrapper > div > button:hover,
        .btn-studio-wrapper .stButton > button:hover,
        .btn-studio-wrapper [data-testid="stBaseButton-secondary"]:hover,
        .btn-studio-wrapper [data-testid="stBaseButton-primary"]:hover {
            background: linear-gradient(135deg,#2e1e00 0%,#5a3a00 50%,#2e1e00 100%) !important;
            box-shadow: 0 0 42px rgba(205,164,52,0.55), 0 0 85px rgba(205,164,52,0.18) !important;
            border-color: #e0b85a !important; color: #ffffff !important;
            transform: translateY(-2px) scale(1.01) !important;
        }
        </style>""", unsafe_allow_html=True)

        # ── Botones Marketing + Studio ────────────────────────────────────────
        _espacio1, _col_btn1, _col_btn2, _espacio2 = st.columns([1, 2, 2, 1])

        with _col_btn1:
            st.markdown('<div class="btn-marketing-wrapper">', unsafe_allow_html=True)
            if st.button(
                "🚀   GENERAR PUBLICACIONES", key="btn_ir_marketing",
                use_container_width=True, type="secondary",
                help="Ir al Generador de Publicaciones con el lote ya cargado",
            ):
                if not st.session_state.get("lote_activo_marketing"):
                    st.session_state["lote_activo_marketing"] = {
                        "lote_id": _id_rep, "modo": _modo_rep, "resultados": _res_rep,
                        "costo_total": _costo_r, "ganancia_total": _gan_r, "env_total": _env_r,
                    }
                st.session_state["_llegada_pub"]  = True
                st.session_state["pagina_activa"] = "publicaciones"
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        with _col_btn2:
            st.markdown('<div class="btn-studio-wrapper">', unsafe_allow_html=True)
            if st.button(
                "📸   IR AL STUDIO VISUAL", key="btn_ir_studio",
                use_container_width=True, type="secondary",
                help="Ir al Estudio Visual para trabajar las fotos de este lote",
            ):
                st.session_state["lote_activo_marketing"] = {
                    "lote_id": _id_rep, "modo": _modo_rep, "resultados": _res_rep,
                    "costo_total": _costo_r, "ganancia_total": _gan_r, "env_total": _env_r,
                }
                st.session_state["pagina_activa"] = "estudio_visual"
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        # ── PDF ───────────────────────────────────────────────────────────────
        st.markdown("<br><br>", unsafe_allow_html=True)
        _pdf_c1, _pdf_c2, _pdf_c3 = st.columns([1, 2, 1])
        with _pdf_c2:
            st.markdown("""
            <div style="background:linear-gradient(160deg,#140808,#0e0404);border:1px solid #3a1212;
                        border-radius:10px;padding:0.9rem 0.8rem 0.5rem;margin-bottom:0.4rem;text-align:center;">
                <span style="display:inline-flex;align-items:center;justify-content:center;
                             width:44px;height:44px;background:linear-gradient(135deg,#a93226,#e74c3c);
                             border-radius:10px;font-size:1.3rem;box-shadow:0 3px 12px rgba(231,76,60,0.3);">📄</span>
                <div style="color:#FF6B6B;font-weight:700;font-size:0.82rem;margin-top:0.5rem;">Resumen PDF del Lote</div>
                <div style="color:#4a3333;font-size:0.65rem;margin-top:0.1rem;">Imprimible · .html → PDF</div>
            </div>""", unsafe_allow_html=True)
            if _html_bytes:
                st.download_button(
                    label="⬇ Descargar Resumen PDF", data=_html_bytes,
                    file_name=f"ADALIMPORT_{_id_rep}_resumen.html", mime="text/html",
                    use_container_width=True, key="dl_pdf_centro",
                    help="Abre en navegador → Ctrl+P → Guardar como PDF",
                )
            else:
                _toast(f"Error al generar PDF: {_pdf_error}", "error")

        # ── Nuevo Lote ────────────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        _sp1, _reset_btn, _sp2 = st.columns([1, 2, 1])
        with _reset_btn:
            if st.button(
                "➕  Cargar Nuevo Lote", key="btn_nuevo_lote_resumen",
                use_container_width=True, type="secondary",
                help="Limpia TODOS los datos (incluyendo marketing) y vuelve al inicio",
            ):
                _resetear_home_fn()
                st.session_state["pagina_activa"] = "lote"
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
