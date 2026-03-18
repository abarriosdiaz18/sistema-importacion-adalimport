import sys, os as _os, builtins as _builtins
# ── FIX sys.path ──────────────────────────────────────────────────────────────
_ROOT   = getattr(_builtins, "_ADALIMPORT_ROOT",   _os.getcwd())
_DB_DIR = getattr(_builtins, "_ADALIMPORT_DB_DIR", _os.path.join(_ROOT, "database"))
for _p in (_DB_DIR, _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)
# ─────────────────────────────────────────────────────────────────────────────
import streamlit as st
import copy as _copy
import math as _math
from calculadora_importacion import analizar_lote, validar_lote
from config_envios import COMISION_ML

try:
    from _toast_system import toast as _toast
except ImportError:
    def _toast(msg, tipo="info"): pass

# ══════════════════════════════════════════════════════════════════════════════
# MÓDULO: _lote_resultados
# Responsabilidad: botón analizar, validación, monitor de eficiencia,
#                  KPIs, tabla desglose, decisión maestra, comparativa.
# Comunicación: SOLO via st.session_state
# ══════════════════════════════════════════════════════════════════════════════

def render_resultados():
    """Renderiza el análisis completo del lote. Requiere productos en session_state."""

    modo        = st.session_state.get("_form_modo", "aereo")
    origen_key  = st.session_state.get("_form_origen", "us")
    origen_envio = st.session_state.get("_form_origen_envio", "🇺🇸  USA")
    courier_sel  = st.session_state.get("courier_sel", None)

    # Leer comisión del sidebar (sincronizado via app.py)
    comision   = st.session_state.get("cfg_comision_ml", 11.0) / 100
    margen_gan = st.number_input(
        "Margen de ganancia objetivo (%)",
        min_value=5, max_value=100,
        value=int(st.session_state.get("cfg_margen_gan", 30)),
        step=5
    ) / 100
    capital = st.number_input(
        "Capital disponible ($)",
        min_value=0.0,
        value=float(st.session_state.get("cfg_capital", 500.0)),
        step=50.0,
        help="Tu presupuesto total para este lote (productos + flete)"
    )

    if st.button("⚡  ANALIZAR LOTE", use_container_width=True):
        productos_calc = _copy.deepcopy(st.session_state.productos)
        resumen_val    = validar_lote(productos_calc)

        # ── Errores bloqueantes ───────────────────────────────────────────────
        if resumen_val["productos_error"]:
            for pe in resumen_val["productos_error"]:
                with st.container():
                    st.markdown(f"""
                    <div style="background:#1F0D0D;border:1px solid #FF1744;border-radius:8px;
                                padding:0.8rem 1rem;margin-bottom:0.5rem">
                        <div style="color:#FF1744;font-family:Space Mono,monospace;font-size:0.8rem;
                                    font-weight:700">❌ {pe["nombre"]}</div>
                        {"".join(f'<div style="color:#aaa;font-size:0.8rem;margin-top:0.3rem">• {e}</div>' for e in pe["errores"])}
                    </div>""", unsafe_allow_html=True)

            if not resumen_val["productos_ok"]:
                _toast("Corrige los errores antes de continuar. No hay productos válidos para analizar.", "error")
                st.stop()
            else:
                _toast(f"{len(resumen_val['productos_error'])} producto(s) con errores serán omitidos del análisis.", "warning")

        # ── Advertencias (no bloquean) ────────────────────────────────────────
        if resumen_val["hay_advertencias"]:
            for p in resumen_val["productos_ok"]:
                val = p.get("_validacion", {})
                if val.get("advertencias"):
                    for adv in val["advertencias"]:
                        st.markdown(f"""
                        <div style="background:#1A1500;border:1px solid #FFD600;border-radius:8px;
                                    padding:0.6rem 1rem;margin-bottom:0.4rem;font-size:0.8rem;color:#FFD600">
                            ⚠️ <b>{p.get("nombre","")}</b>: {adv}
                        </div>""", unsafe_allow_html=True)

        # ── Calcular ──────────────────────────────────────────────────────────
        _productos_ok_pristine = _copy.deepcopy(resumen_val["productos_ok"])
        productos_validos      = _copy.deepcopy(_productos_ok_pristine)
        resultados, env_total, peso_vol, unidad, costo_total = analizar_lote(
            productos_validos, modo=modo, margen_ganancia=margen_gan,
            courier=courier_sel, origen=origen_key
        )

        # ── Monitor de Eficiencia ─────────────────────────────────────────────
        _r0              = resultados[0] if resultados else {}
        _carga_real      = _r0.get("carga_total_lote",    peso_vol)
        _carga_min       = _r0.get("carga_minimo_courier", 0)
        _min_usd_courier = _r0.get("carga_minimo_usd",     0)
        _faltante        = _r0.get("faltante_minimo",      0)
        _n_items         = sum(r["cantidad"] for r in resultados)
        _unid_mon        = "lb" if modo == "aereo" else "ft³"
        _emoji_mon       = "✈️" if modo == "aereo" else "🚢"

        st.markdown('<div class="section-title">📊 Monitor de Eficiencia del Consolidado</div>', unsafe_allow_html=True)
        _mc1, _mc2, _mc3 = st.columns(3)

        _mc1.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Total artículos · Carga acumulada</div>
            <div class="kpi-value kpi-white">
                {_n_items} ítems
                <small style="font-size:0.8rem;color:#aaa;display:block;margin-top:2px">
                    {_emoji_mon} {_carga_real:.3f} {_unid_mon} reales
                </small>
            </div>
        </div>""", unsafe_allow_html=True)

        _mc2.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Costo total del flete al courier</div>
            <div class="kpi-value kpi-yellow">
                ${env_total:.2f}
                <small style="font-size:0.75rem;color:#aaa;display:block;margin-top:2px">
                    Factor flete: ${_r0.get("tarifa_efectiva", 0):.2f}/{_unid_mon}
                </small>
            </div>
        </div>""", unsafe_allow_html=True)

        if _carga_min > 0 and _faltante > 0:
            _mc3.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Estado del consolidado</div>
                <div class="kpi-value" style="color:#FFD600;font-size:0.95rem">
                    ⚠️ Bajo el mínimo
                    <small style="font-size:0.72rem;color:#aaa;display:block;margin-top:2px">
                        Mínimo: {_carga_min} {_unid_mon} · Faltan {_faltante:.3f} {_unid_mon}
                    </small>
                </div>
            </div>""", unsafe_allow_html=True)
            _toast(
                f"Consolidado bajo el mínimo — {_carga_real:.3f} {_unid_mon} de {_carga_min} {_unid_mon}. "
                f"Faltan {_faltante:.3f} {_unid_mon} · Agrega más productos para optimizar el flete.",
                "warning"
            )
        elif env_total <= _min_usd_courier and _min_usd_courier > 0:
            _mc3.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Estado del consolidado</div>
                <div class="kpi-value" style="color:#FFD600;font-size:0.95rem">
                    ⚠️ Mínimo USD activo
                    <small style="font-size:0.72rem;color:#aaa;display:block;margin-top:2px">
                        Pagando mínimo: ${_min_usd_courier:.2f}
                    </small>
                </div>
            </div>""", unsafe_allow_html=True)
            _toast(
                f"Se aplica el mínimo en USD — el courier cobra ${_min_usd_courier:.2f} "
                f"independientemente del volumen. Agrega más productos para distribuir este costo fijo.",
                "warning"
            )
        else:
            _mc3.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Estado del consolidado</div>
                <div class="kpi-value" style="color:#00E676;font-size:0.95rem">
                    ✅ Flete optimizado
                    <small style="font-size:0.72rem;color:#aaa;display:block;margin-top:2px">
                        Supera el mínimo · Tarifa plena activa
                    </small>
                </div>
            </div>""", unsafe_allow_html=True)
            _toast(
                f"Consolidado optimizado — {_carga_real:.3f} {_unid_mon} · flete a tarifa plena, prorrateo exacto.",
                "success"
            )

        st.markdown("---")

        # ── KPIs principales ──────────────────────────────────────────────────
        costo_origen_total   = sum(r["costo_warehouse"] * r["cantidad"] for r in resultados)
        presupuesto_restante = capital - costo_total
        ganancia_total_lote  = sum(r["ganancia_objetivo"] * r["cantidad"] for r in resultados)

        k1, k2, k3, k4, k5 = st.columns(5)
        k1.markdown(f'''<div class="kpi-card">
            <div class="kpi-label">Costo en tiendas</div>
            <div class="kpi-value kpi-white">${costo_origen_total:.2f}</div>
        </div>''', unsafe_allow_html=True)
        k2.markdown(f'''<div class="kpi-card">
            <div class="kpi-label">Courier {"✈️" if modo=="aereo" else "🚢"}</div>
            <div class="kpi-value kpi-yellow">${env_total:.2f} <small style="font-size:0.8rem">({peso_vol} {unidad})</small></div>
        </div>''', unsafe_allow_html=True)
        k3.markdown(f'''<div class="kpi-card">
            <div class="kpi-label">Inversión total</div>
            <div class="kpi-value kpi-white">${costo_total:.2f}</div>
        </div>''', unsafe_allow_html=True)
        presup_color = "kpi-green" if presupuesto_restante >= 0 else "kpi-red"
        k4.markdown(f'''<div class="kpi-card">
            <div class="kpi-label">Capital restante</div>
            <div class="kpi-value {presup_color}">${presupuesto_restante:.2f}</div>
        </div>''', unsafe_allow_html=True)
        k5.markdown(f'''<div class="kpi-card">
            <div class="kpi-label">Ganancia total lote</div>
            <div class="kpi-value kpi-green">${ganancia_total_lote:.2f}</div>
        </div>''', unsafe_allow_html=True)

        # ── Banner de alertas semáforo ────────────────────────────────────────
        _alertas_nivel1 = [r for r in resultados if r.get("inapto_para_aereo")]
        _alertas_nivel2 = [r for r in resultados if r.get("inviable_aire")]
        _alertas_nivel3 = [r for r in resultados if "INVIABLE" in r.get("decision","")
                           and not r.get("inapto_para_aereo") and not r.get("inviable_aire")]

        if _alertas_nivel1 or _alertas_nivel2 or _alertas_nivel3:
            _alerta_html = """
            <div style="background:#1A0A00;border:2px solid #E65100;border-radius:10px;
                        padding:0.8rem 1.2rem;margin-bottom:1rem">
            <div style="font-family:Space Mono,monospace;color:#FF6D00;font-size:0.82rem;
                        font-weight:700;margin-bottom:0.5rem">
                🚨 Productos que requieren acción antes de comprar
            </div>"""
            if _alertas_nivel1:
                _names1 = ", ".join(a["nombre"] for a in _alertas_nivel1)
                _alerta_html += f'<div style="margin-bottom:0.3rem"><span style="color:#FF6D00;font-weight:700">🟠 USAR MARÍTIMO</span><span style="color:#888;font-size:0.78rem"> · {_names1}</span></div>'
            if _alertas_nivel2:
                _names2 = ", ".join(a["nombre"] for a in _alertas_nivel2)
                _alerta_html += f'<div style="margin-bottom:0.3rem"><span style="color:#FF1744;font-weight:700">🔴 INVIABLE (aire)</span><span style="color:#888;font-size:0.78rem"> · {_names2}</span></div>'
            if _alertas_nivel3:
                _names3 = ", ".join(a["nombre"] for a in _alertas_nivel3)
                _alerta_html += f'<div style="margin-bottom:0.3rem"><span style="color:#FF1744;font-weight:700">🔴 INVIABLE (margen)</span><span style="color:#888;font-size:0.78rem"> · {_names3}</span></div>'
            _alerta_html += "</div>"
            st.markdown(_alerta_html, unsafe_allow_html=True)

        # ── Tabla de resultados ───────────────────────────────────────────────
        st.markdown('<div class="section-title">Desglose completo de costos por producto</div>', unsafe_allow_html=True)

        _tarifa_ef   = resultados[0]["tarifa_efectiva"] if resultados else 0
        _unid_fisica = resultados[0]["unidad_fisica"]   if resultados else "lb"
        _unid_emoji  = "✈️" if _unid_fisica == "lb" else "🚢"
        _unid_lbl    = "lb" if _unid_fisica == "lb" else "ft³"

        filas = ""
        for r in resultados:
            inapto   = r.get("inapto_para_aereo", False)
            inviable = r.get("inviable_aire", False)

            if inapto or "MARÍTIMO" in r["decision"]:
                dec_html = '<span class="badge-inapto">🟠 USAR MARÍTIMO</span>'
            elif inviable or "INVIABLE" in r["decision"]:
                dec_html = '<span class="badge-bad">🔴 INVIABLE</span>'
            elif "REVISAR" in r["decision"]:
                dec_html = '<span class="badge-warn">⚠️ REVISAR</span>'
            elif "COMPRAR" in r["decision"]:
                dec_html = '<span class="badge-ok">✅ COMPRAR</span>'
            else:
                dec_html = '<span class="badge-bad">🔴 INVIABLE</span>'

            tax_display = f'{r["tax_rate"]*100:.0f}%'
            sin_dims    = r.get("_validacion", {}).get("modo") == "sin_dims" if r.get("_validacion") else False

            _decision_str = r.get("decision", "")
            if r.get("inapto_para_aereo"):
                _tr_bg = 'background:rgba(230,81,0,0.08);border-left:3px solid #E65100'
            elif r.get("inviable_aire") or ("INVIABLE" in _decision_str):
                _tr_bg = 'background:rgba(255,23,68,0.08);border-left:3px solid #FF1744'
            elif "REVISAR" in _decision_str:
                _tr_bg = 'background:rgba(255,214,0,0.04);border-left:3px solid #FFD600'
            else:
                _tr_bg = ''

            dims_badge = (
                '<br><span style="display:inline-block;margin-top:3px;padding:2px 7px;'
                'background:#2A1500;border:1px solid #FF8C00;border-radius:4px;'
                'color:#FF8C00;font-size:0.68rem;font-weight:700;letter-spacing:0.03em">'
                '⚠️ FALTA MEDIDAS — estimación de riesgo</span>'
            ) if sin_dims else ''

            nombre_cell = f'<b>{r["nombre"]}</b><br><small style="color:#555">{r["tienda"]}</small>{dims_badge}'

            if _unid_fisica == "lb":
                mag_val  = r["peso_cobrable_item"]
                mag_disp = f'{mag_val:.3f} lb'
            else:
                mag_val  = r["vol_ft3_item"]
                mag_disp = f'{mag_val:.4f} ft³'
            prop_pct    = r["prop_fisica"] * 100
            fisico_cell = (
                f'<b>{mag_disp}</b>'
                f'<br><small style="color:#555">{prop_pct:.1f}% del lote</small>'
                + ('<br><small style="color:#FF8C00;font-style:italic">solo peso real</small>' if sin_dims else '')
            )
            flete_cell = (
                f'<b style="color:#FFD600">+${r["flete_proporcional"]:.2f}</b>'
                f'<br><small style="color:#555">${_tarifa_ef:.2f}/{_unid_lbl} efectivo</small>'
            )

            filas += f"""
            <tr style="{_tr_bg}">
                <td style="text-align:center">{dec_html}</td>
                <td>{nombre_cell}</td>
                <td style="text-align:center">{r["cantidad"]}</td>
                <td>${r["precio_tienda"]:.2f}<br><small style="color:#888">+${r["sales_tax"]:.2f} tax ({tax_display})</small></td>
                <td><small style="color:#888">+${r["envio_interno"]:.2f}</small></td>
                <td>${r["costo_warehouse"]:.2f}</td>
                <td style="text-align:center">{fisico_cell}</td>
                <td style="text-align:center">{flete_cell}</td>
                <td><b>${r["costo_real"]:.2f}</b><br><small style="color:#555">+3% seg.</small></td>
                <td style="color:#888"><b>${r["precio_ml_minimo"]:.2f}</b><br><small style="color:#555">sin pérdida</small></td>
                <td style="color:#FFD600"><b>${r["precio_ml_objetivo"]:.2f}</b><br><small style="color:#555">-${r["comision_ml"]:.2f} ML</small></td>
                <td style="color:#00E676"><b>${r["ganancia_objetivo"]:.2f}</b><br><small style="color:#555">{r["margen_pct"]}%</small></td>
            </tr>"""

        st.markdown(f"""
        <table class="res-table">
            <thead><tr>
                <th style="text-align:center">DECISIÓN</th>
                <th>Producto</th><th>Cant</th>
                <th>Precio + Tax</th><th>Env. interno</th>
                <th>En warehouse</th>
                <th>{_unid_emoji} Peso/Vol.</th>
                <th>Flete</th>
                <th>Costo real</th>
                <th>💸 Precio mín. ML</th>
                <th>🎯 Precio obj. ML</th>
                <th>Ganancia ({margen_gan*100:.0f}%)</th>
            </tr></thead>
            <tbody>{filas}</tbody>
        </table>
        <br>
        <div style="font-size:0.7rem;color:#555;margin-top:0.5rem">
        {_unid_emoji} <b>Flete proporcional</b>: courier repartido por peso/volumen físico real · Tarifa efectiva del lote: <b>${_tarifa_ef:.2f}/{_unid_lbl}</b><br>
        💡 <b>Precio mínimo ML</b>: punto de equilibrio, no pierdes ni ganas.<br>
        🎯 <b>Precio objetivo ML</b>: incluye tu ganancia deseada ({margen_gan*100:.0f}%) · Comisión ML {comision*100:.0f}% ya descontada.<br>
        🔴 <b>Inviable Aire</b>: se activa cuando el peso volumétrico supera 2× el peso real (umbral 100%). Cambia a Marítimo.
        </div>
        """, unsafe_allow_html=True)

        # ── Decisión maestra de envío ─────────────────────────────────────────
        st.markdown("---")
        try:
            res_aereo, env_a, pv_a, u_a, ct_a = analizar_lote(
                _copy.deepcopy(_productos_ok_pristine),
                modo="aereo", margen_ganancia=margen_gan,
                courier=courier_sel, origen=origen_key)
            res_mar, env_m, pv_m, u_m, ct_m = analizar_lote(
                _copy.deepcopy(_productos_ok_pristine),
                modo="maritimo", margen_ganancia=margen_gan,
                courier=courier_sel, origen=origen_key)

            ventas_a_real = sum(ra["precio_ml_objetivo"] * ra["cantidad"] for ra in res_aereo)
            ventas_m_real = sum(rm["precio_ml_objetivo"] * rm["cantidad"] for rm in res_mar)
            inv_a      = round(sum(ra["costo_real"] * ra["cantidad"] for ra in res_aereo), 2)
            inv_m      = round(sum(rm["costo_real"] * rm["cantidad"] for rm in res_mar), 2)
            gan_a_real = round(ventas_a_real - inv_a, 2)
            gan_m_real = round(ventas_m_real - inv_m, 2)
            roi_a      = round((gan_a_real / inv_a * 100) if inv_a > 0 else 0, 1)
            roi_m      = round((gan_m_real / inv_m * 100) if inv_m > 0 else 0, 1)
            margen_a   = round((gan_a_real / ventas_a_real * 100) if ventas_a_real > 0 else 0, 1)
            margen_m   = round((gan_m_real / ventas_m_real * 100) if ventas_m_real > 0 else 0, 1)

            ahorro_flete   = round(abs(env_a - env_m), 2)
            _empate_flete  = ahorro_flete < 5.00
            _n_productos   = len(_productos_ok_pristine)
            _es_item_unico = _n_productos == 1

            if _empate_flete:
                mejor_via = "aereo"; _forzado_por_velocidad = True
            else:
                mejor_via = "aereo" if env_a <= env_m else "maritimo"; _forzado_por_velocidad = False

            _flete_ganador_val = env_a if mejor_via == "aereo" else env_m
            _flete_loser_val   = env_m if mejor_via == "aereo" else env_a
            _inv_ganadora      = inv_a if mejor_via == "aereo" else inv_m
            _inv_loser         = inv_m if mejor_via == "aereo" else inv_a
            _gan_winner        = gan_a_real if mejor_via == "aereo" else gan_m_real
            _gan_loser         = gan_m_real if mejor_via == "aereo" else gan_a_real
            _roi_winner        = roi_a      if mejor_via == "aereo" else roi_m
            _roi_loser         = roi_m      if mejor_via == "aereo" else roi_a
            _margen_winner     = margen_a   if mejor_via == "aereo" else margen_m
            _margen_loser      = margen_m   if mejor_via == "aereo" else margen_a

            _es_compacto = True
            if _es_item_unico and _productos_ok_pristine:
                _p0      = _productos_ok_pristine[0]
                _peso_lb = _p0.get("peso_lb", 0) or 0
                _l       = _p0.get("largo", 0) or 0
                _aw      = _p0.get("ancho", 0) or 0
                _h       = _p0.get("alto",  0) or 0
                _vol_ft3 = (_l * _aw * _h) / 1728 if (_l and _aw and _h) else 0
                _es_compacto = not (_vol_ft3 > 1.0 or _peso_lb > 10)

            _tipo_item  = "compacto"  if _es_compacto else "voluminoso"
            _via_nombre = "Aérea"     if mejor_via == "aereo" else "Marítima"
            _via_icono  = "✈️"        if mejor_via == "aereo" else "🚢"

            if _forzado_por_velocidad:
                _mensaje_cerebro = (
                    f"✈️ <b>Conveniente vía Aérea:</b> La diferencia de flete es de solo "
                    f"<b>${ahorro_flete:.2f}</b> — por debajo del umbral de $5.00. "
                    f"Con un ahorro tan pequeño, la velocidad de entrega es el factor decisivo."
                )
            elif _es_item_unico:
                _mensaje_cerebro = (
                    f"{_via_icono} <b>Conveniente vía {_via_nombre}:</b> Este ítem individual es "
                    f"<b>{_tipo_item}</b>, por lo que esta vía ofrece el flete más económico "
                    f"(<b>${_flete_ganador_val:.2f}</b>) frente a ${_flete_loser_val:.2f} por la otra vía."
                )
            else:
                _mensaje_cerebro = (
                    f"{_via_icono} <b>Conveniente vía {_via_nombre}:</b> El lote consolidado "
                    f"aprovecha mejor esta modalidad, <b>ahorrándote ${ahorro_flete:.2f}</b> "
                    f"(${_flete_ganador_val:.2f} vs ${_flete_loser_val:.2f})."
                )

            _via_label       = "✈️ AÉREO"    if mejor_via == "aereo" else "🚢 MARÍTIMO"
            _via_emoji       = "✈️"           if mejor_via == "aereo" else "🚢"
            _entrega_winner  = "7 – 10 días"  if mejor_via == "aereo" else "20 – 30 días"
            _via_loser_label = "🚢 Marítimo"  if mejor_via == "aereo" else "✈️ Aéreo"
            _entrega_loser   = "20 – 30 días" if mejor_via == "aereo" else "7 – 10 días"
            gan_color_w = "#00E676" if _gan_winner >= 0 else "#FF1744"
            gan_color_l = "#00E676" if _gan_loser  >= 0 else "#FF1744"

            _str_flete_w = f"${_flete_ganador_val:,.2f}"; _str_flete_l = f"${_flete_loser_val:,.2f}"
            _str_inv_w   = f"${_inv_ganadora:,.2f}";      _str_inv_l   = f"${_inv_loser:,.2f}"
            _str_gan_w   = f"${_gan_winner:,.2f}";         _str_gan_l   = f"${_gan_loser:,.2f}"
            _str_roi_w   = f"{_roi_winner:.1f}% / {_margen_winner:.1f}%"
            _str_roi_l   = f"{_roi_loser:.1f}% / {_margen_loser:.1f}%"
            _str_roi_sub = f"ROI {_roi_winner:.1f}% · Margen {_margen_winner:.1f}%"
            _str_cerebro_label = "Ítem único" if _es_item_unico else f"Consolidado {_n_productos} productos"

            _nota_velocidad = (
                f'<div style="font-size:0.7rem;color:#7B8CDE;margin-top:6px;'
                f'background:#0D0D1F;border-radius:6px;padding:4px 10px;display:inline-block">'
                f'&#9889; Regla $5 · diferencia ${ahorro_flete:.2f} &lt; $5 → velocidad decide</div>'
            ) if _forzado_por_velocidad else ""

            st.markdown(
                '<div style="border:2px solid #00E676;border-radius:18px;background:#0A140A;'
                'box-shadow:0 0 32px rgba(0,230,118,0.18),inset 0 0 60px rgba(0,0,0,0.6);'
                'padding:1.6rem 1.8rem 0.6rem 1.8rem;margin-bottom:0">'
                '<div style="display:flex;align-items:center;justify-content:space-between;'
                'flex-wrap:wrap;gap:0.6rem;margin-bottom:1.2rem">'
                '<div style="font-size:0.65rem;font-weight:900;letter-spacing:2.5px;'
                'text-transform:uppercase;color:#00E676;background:rgba(0,230,118,0.08);'
                'border:1px solid #00E676;border-radius:20px;padding:4px 16px;white-space:nowrap">'
                '🎯 DECISIÓN INTELIGENTE DE ENVÍO</div>'
                '<div style="font-size:0.62rem;color:#2a6a2a;letter-spacing:1px">'
                'Criterio: Flete más bajo · Empate &lt;$5 → velocidad</div></div>',
                unsafe_allow_html=True
            )
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:1rem;flex-wrap:wrap;margin-bottom:1rem">'
                f'<div style="font-size:0.62rem;font-weight:900;color:#0A140A;background:#00E676;'
                f'border-radius:20px;padding:4px 14px;letter-spacing:1.5px;text-transform:uppercase;white-space:nowrap">'
                f'🏆 VÍA RECOMENDADA</div>'
                f'<div style="font-size:1.8rem;font-weight:900;color:#00E676;'
                f'letter-spacing:0.5px;text-shadow:0 0 20px rgba(0,230,118,0.5)">{_via_label}</div>'
                f'{_nota_velocidad}</div>',
                unsafe_allow_html=True
            )

            _mk1, _mk2, _mk3 = st.columns(3)
            _mk1.markdown(
                f'<div style="background:#0D1A0D;border:2px solid #00E676;border-radius:12px;'
                f'padding:1rem;text-align:center;box-shadow:0 0 16px rgba(0,230,118,0.15)">'
                f'<div style="font-size:0.6rem;color:#00E676;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:6px;font-weight:700">🚀 Flete a Pagar (Ganador)</div>'
                f'<div style="font-size:1.9rem;font-weight:900;color:#00E676;line-height:1;text-shadow:0 0 12px rgba(0,230,118,0.4)">{_str_flete_w}</div>'
                f'<div style="font-size:0.68rem;color:#2a6a2a;margin-top:5px">{_entrega_winner}</div></div>',
                unsafe_allow_html=True
            )
            _mk2.markdown(
                f'<div style="background:#0A140A;border:1px solid #1a3a1a;border-radius:12px;padding:1rem;text-align:center">'
                f'<div style="font-size:0.6rem;color:#888;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:6px;font-weight:700">💰 Inversión Total del Lote</div>'
                f'<div style="font-size:1.9rem;font-weight:900;color:#E8E8E8;line-height:1">{_str_inv_w}</div>'
                f'<div style="font-size:0.68rem;color:#555;margin-top:5px">producto + flete + seguro</div></div>',
                unsafe_allow_html=True
            )
            _mk3.markdown(
                f'<div style="background:#0A140A;border:1px solid #1a3a1a;border-radius:12px;padding:1rem;text-align:center">'
                f'<div style="font-size:0.6rem;color:#888;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:6px;font-weight:700">📈 Ganancia Neta del Lote</div>'
                f'<div style="font-size:1.9rem;font-weight:900;color:{gan_color_w};line-height:1">{_str_gan_w}</div>'
                f'<div style="font-size:0.68rem;color:#555;margin-top:5px">{_str_roi_sub}</div></div>',
                unsafe_allow_html=True
            )
            st.markdown(
                f'<div style="background:rgba(0,230,118,0.04);border:1px solid rgba(0,230,118,0.2);'
                f'border-radius:10px;padding:0.9rem 1.2rem;line-height:1.65;margin-top:0.8rem">'
                f'<div style="font-size:0.6rem;color:#00A854;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:6px;font-weight:700">'
                f'🧠 Cerebro Logístico — {_str_cerebro_label}</div>'
                f'<div style="font-size:0.875rem;color:#C8F0D0;font-weight:500">{_mensaje_cerebro}</div></div>',
                unsafe_allow_html=True
            )
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
            _cl, _cr = st.columns(2)
            _cl.markdown(
                f'<div style="border:2px solid #00E676;border-radius:12px;background:#0A140A;padding:1rem 1.1rem;height:100%;box-shadow:0 0 18px rgba(0,230,118,0.12)">'
                f'<div style="font-size:0.65rem;color:#00E676;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:0.7rem;font-weight:700">{_via_emoji} {_via_label} · Desglose</div>'
                f'<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #1a3a1a;font-size:0.78rem"><span style="color:#4a8a4a">Flete courier</span><span style="font-weight:700;color:#00E676">{_str_flete_w}</span></div>'
                f'<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #1a3a1a;font-size:0.78rem"><span style="color:#4a8a4a">Inversión total</span><span style="font-weight:700;color:#E8E8E8">{_str_inv_w}</span></div>'
                f'<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #1a3a1a;font-size:0.78rem"><span style="color:#4a8a4a">Ganancia neta</span><span style="font-weight:700;color:{gan_color_w}">{_str_gan_w}</span></div>'
                f'<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #1a3a1a;font-size:0.78rem"><span style="color:#4a8a4a">ROI / Margen</span><span style="font-weight:700;color:#7B8CDE">{_str_roi_w}</span></div>'
                f'<div style="display:flex;justify-content:space-between;padding:5px 0;font-size:0.78rem"><span style="color:#4a8a4a">Entrega estimada</span><span style="font-weight:700;color:#00E676">{_entrega_winner}</span></div></div>',
                unsafe_allow_html=True
            )
            _cr.markdown(
                f'<div style="border:1px solid #1E2A1E;border-radius:12px;background:#070D07;padding:1rem 1.1rem;opacity:0.65;height:100%">'
                f'<div style="font-size:0.65rem;color:#3a6a3a;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:0.7rem;font-weight:700">{_via_loser_label} · Comparativa</div>'
                f'<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #111a11;font-size:0.78rem"><span style="color:#2a4a2a">Flete courier</span><span style="font-weight:700;color:#3a6a3a">{_str_flete_l}</span></div>'
                f'<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #111a11;font-size:0.78rem"><span style="color:#2a4a2a">Inversión total</span><span style="font-weight:700;color:#444">{_str_inv_l}</span></div>'
                f'<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #111a11;font-size:0.78rem"><span style="color:#2a4a2a">Ganancia neta</span><span style="font-weight:700;color:{gan_color_l};opacity:0.5">{_str_gan_l}</span></div>'
                f'<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #111a11;font-size:0.78rem"><span style="color:#2a4a2a">ROI / Margen</span><span style="font-weight:700;color:#2a4a2a">{_str_roi_l}</span></div>'
                f'<div style="display:flex;justify-content:space-between;padding:5px 0;font-size:0.78rem"><span style="color:#2a4a2a">Entrega estimada</span><span style="font-weight:700;color:#2a4a2a">{_entrega_loser}</span></div></div>',
                unsafe_allow_html=True
            )

        except Exception as _e_comp:
            _toast(f"No se pudo generar la comparativa: {_e_comp}", "warning")

        st.markdown("---")

        # ── Persistir resultados en session_state para aprobación ────────────
        st.session_state.resultados_lote   = resultados
        st.session_state._lote_env_total   = env_total
        st.session_state._lote_costo_total = costo_total
        st.session_state._lote_ganancia    = ganancia_total_lote
        st.session_state._lote_modo        = modo
        st.session_state._lote_origen      = st.session_state.get("_form_origen_envio", origen_envio)
        st.session_state._lote_aprobado    = False
        st.session_state["_modo_activo_prev"] = modo
