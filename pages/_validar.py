import streamlit as st
import requests
import os as _os_val
from config_envios import COMISION_ML
import config_envios as cfg
from styles_adalimport import aplicar_estilos
aplicar_estilos()

# ── Hero Header ───────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg,rgba(13,20,36,0.9) 0%,rgba(5,9,15,0.95) 100%);
            border:1px solid rgba(184,150,62,0.2);border-top:2px solid var(--gold);
            border-radius:14px;padding:20px 24px;margin-bottom:24px;
            display:flex;align-items:center;gap:16px;">
  <span style="font-size:2rem;line-height:1;filter:drop-shadow(0 0 10px rgba(0,230,118,0.4));">🔍</span>
  <div style="flex:1">
    <div style="font-family:'DM Mono',monospace;font-size:0.58rem;letter-spacing:3px;
                text-transform:uppercase;color:var(--gold);margin-bottom:4px;">
      Validar · Competencia MercadoLibre
    </div>
    <div style="font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:800;
                color:var(--text);line-height:1.1;margin-bottom:4px;">
      Análisis de <span style="color:var(--neon);">Competitividad</span>
    </div>
    <div style="font-family:'Inter',sans-serif;font-size:0.82rem;color:var(--muted);">
      Compara tu precio ML calculado contra la competencia real en el mercado
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown('''
<div style="background:#0D1A0D;border:1px solid #1a3a1a;border-radius:8px;padding:0.8rem 1.2rem;margin-bottom:1.2rem;font-size:0.82rem;color:#aaa;line-height:1.6">
📋 <b style="color:#00E676">Flujo recomendado:</b>
Abre ML Venezuela → busca tu producto → anota los precios que ves →
ingrésalos aquí → ADALIMPORT calcula si tu precio es competitivo.
</div>
''', unsafe_allow_html=True)

# ── Historial en sesión ───────────────────────────────────────────────
if "historial_precios" not in st.session_state:
    st.session_state.historial_precios = []

# ── Formulario de entrada ─────────────────────────────────────────────
st.markdown('<div class="section-title">Nuevo análisis de competencia</div>', unsafe_allow_html=True)

col_f1, col_f2 = st.columns([1, 1])
with col_f1:
    v_nombre   = st.text_input("Nombre del producto", placeholder="Ej: Pilas AA Energizer 4pk", key="v_nombre")
    v_mi_precio = st.number_input("Mi precio ML calculado ($)", min_value=0.01, value=20.0,
                                   help="El precio que calculaste en el Tab LOTE", key="v_mi_precio")
    v_mi_costo  = st.number_input("Mi costo total ($)", min_value=0.01, value=15.0,
                                   help="Costo producto + envío por unidad", key="v_mi_costo")

with col_f2:
    st.markdown("<small style='color:#888'>Precios observados en ML Venezuela (deja en 0 los que no uses)</small>", unsafe_allow_html=True)
    v_p1 = st.number_input("Competencia #1 ($)", min_value=0.0, value=0.0, key="v_p1")
    v_p2 = st.number_input("Competencia #2 ($)", min_value=0.0, value=0.0, key="v_p2")
    v_p3 = st.number_input("Competencia #3 ($)", min_value=0.0, value=0.0, key="v_p3")
    v_p4 = st.number_input("Competencia #4 ($)", min_value=0.0, value=0.0, key="v_p4")
    v_p5 = st.number_input("Competencia #5 ($)", min_value=0.0, value=0.0, key="v_p5")

if st.button("📊  ANALIZAR COMPETITIVIDAD", use_container_width=True):
    precios_comp = [p for p in [v_p1, v_p2, v_p3, v_p4, v_p5] if p > 0]
    if not precios_comp:
        st.warning("Ingresa al menos un precio de la competencia.")
    elif not v_nombre:
        st.warning("Ingresa el nombre del producto.")
    else:
        promedio  = sum(precios_comp) / len(precios_comp)
        minimo    = min(precios_comp)
        maximo    = max(precios_comp)
        ganancia  = v_mi_precio - v_mi_costo
        margen    = (ganancia / v_mi_precio * 100) if v_mi_precio > 0 else 0
        diff_pct  = ((v_mi_precio - promedio) / promedio * 100)

        # Precio sugerido óptimo: 5% bajo el promedio
        precio_optimo = round(promedio * 0.95, 2)
        ganancia_optima = precio_optimo - v_mi_costo

        # Determinar veredicto
        if v_mi_precio < minimo * 0.95:
            veredicto = ("⚠️ PRECIO MUY BAJO", "#FF1744",
                         "Estás regalando el producto. Revisa si tu costo real está bien calculado.")
        elif v_mi_precio <= promedio:
            veredicto = ("✅ COMPETITIVO", "#00E676",
                         f"Estás {abs(diff_pct):.1f}% bajo el promedio. Buena posición para vender rápido.")
        elif v_mi_precio <= maximo:
            veredicto = ("🔶 PRECIO ALTO", "#FFD600",
                         f"Estás {diff_pct:.1f}% sobre el promedio. Justifica con garantía o envío incluido.")
        else:
            veredicto = ("❌ FUERA DE MERCADO", "#FF1744",
                         f"Superas el precio máximo en {diff_pct:.1f}%. Muy difícil vender a este precio.")

        # ── KPIs principales ─────────────────────────────────────────
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.markdown(f'''<div class="kpi-card"><div class="kpi-label">Mi precio</div>
            <div class="kpi-value kpi-yellow">${v_mi_precio:.2f}</div></div>''', unsafe_allow_html=True)
        k2.markdown(f'''<div class="kpi-card"><div class="kpi-label">Promedio ML</div>
            <div class="kpi-value kpi-white">${promedio:.2f}</div></div>''', unsafe_allow_html=True)
        k3.markdown(f'''<div class="kpi-card"><div class="kpi-label">Mínimo ML</div>
            <div class="kpi-value kpi-red">${minimo:.2f}</div></div>''', unsafe_allow_html=True)
        k4.markdown(f'''<div class="kpi-card"><div class="kpi-label">Máximo ML</div>
            <div class="kpi-value kpi-green">${maximo:.2f}</div></div>''', unsafe_allow_html=True)
        k5.markdown(f'''<div class="kpi-card"><div class="kpi-label">Mi ganancia</div>
            <div class="kpi-value {"kpi-green" if ganancia > 0 else "kpi-red"}">${ganancia:.2f}</div></div>''', unsafe_allow_html=True)

        # ── Veredicto ────────────────────────────────────────────────
        st.markdown(f'''
        <div class="precio-validado" style="border-color:{veredicto[1]};background:linear-gradient(135deg,#111,#0D0D0D);margin-top:1rem">
            <div class="label">Veredicto</div>
            <div class="valor" style="color:{veredicto[1]};font-size:1.3rem">{veredicto[0]}</div>
            <div class="fuente" style="margin-top:0.4rem;font-size:0.85rem;color:#aaa">{veredicto[2]}</div>
        </div>
        ''', unsafe_allow_html=True)

        # ── Precio sugerido óptimo ───────────────────────────────────
        st.markdown('<div class="section-title">Recomendación de precio</div>', unsafe_allow_html=True)

        col_rec1, col_rec2 = st.columns(2)
        with col_rec1:
            ganancia_color = "#00E676" if ganancia_optima > 0 else "#FF1744"
            st.markdown(f'''
            <div class="kpi-card" style="border-color:#FFD600">
                <div class="kpi-label">Precio óptimo sugerido (5% bajo promedio)</div>
                <div class="kpi-value kpi-yellow" style="font-size:2rem">${precio_optimo:.2f}</div>
                <div style="font-size:0.75rem;color:#888;margin-top:0.4rem">
                    Ganancia estimada: <span style="color:{ganancia_color}">${ganancia_optima:.2f}</span>
                    &nbsp;·&nbsp; Margen: <span style="color:{ganancia_color}">{((ganancia_optima/precio_optimo)*100) if precio_optimo > 0 else 0:.1f}%</span>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        with col_rec2:
            # Tabla de precios de competencia visualizada
            filas_comp = ""
            for i, p in enumerate(precios_comp, 1):
                bar_w = int((p / maximo) * 100)
                color = "#00E676" if p == minimo else ("#FF1744" if p == maximo else "#888")
                filas_comp += f'''<tr>
                    <td style="color:#888;font-size:0.75rem">#{i}</td>
                    <td style="font-family:Space Mono,monospace;color:{color}">${p:.2f}</td>
                    <td style="width:100px">
                        <div style="background:#2A2A2A;border-radius:3px;height:6px;width:100px">
                            <div style="background:{color};height:6px;border-radius:3px;width:{bar_w}px"></div>
                        </div>
                    </td>
                </tr>'''
            st.markdown(f'''
            <div style="background:#161616;border:1px solid #2A2A2A;border-radius:8px;padding:1rem">
                <div style="font-size:0.65rem;color:#888;text-transform:uppercase;letter-spacing:2px;margin-bottom:0.8rem">
                    Precios competencia ({len(precios_comp)} observados)
                </div>
                <table style="width:100%;border-collapse:collapse">{filas_comp}</table>
                <div style="margin-top:0.8rem;font-size:0.7rem;color:#555">
                    Tu precio vs promedio: <span style="color:{"#00E676" if diff_pct <= 0 else "#FFD600"}">{diff_pct:+.1f}%</span>
                </div>
            </div>
            ''', unsafe_allow_html=True)

        # ── Guardar en historial ─────────────────────────────────────
        entrada_historial = {
            "producto": v_nombre,
            "mi_precio": v_mi_precio,
            "promedio": round(promedio, 2),
            "minimo": minimo,
            "maximo": maximo,
            "ganancia": round(ganancia, 2),
            "margen": round(margen, 1),
            "veredicto": veredicto[0],
            "precio_optimo": precio_optimo,
        }
        # Evitar duplicados por nombre
        st.session_state.historial_precios = [
            h for h in st.session_state.historial_precios if h["producto"] != v_nombre
        ]
        st.session_state.historial_precios.insert(0, entrada_historial)

# ── Historial de análisis ─────────────────────────────────────────────
if st.session_state.historial_precios:
    st.markdown('<div class="section-title">Historial de análisis esta sesión</div>', unsafe_allow_html=True)
    filas_h = ""
    for h in st.session_state.historial_precios:
        if "COMPETITIVO" in h["veredicto"]:
            vcolor = "#00E676"
        elif "BAJO" in h["veredicto"] or "FUERA" in h["veredicto"]:
            vcolor = "#FF1744"
        else:
            vcolor = "#FFD600"
        filas_h += f'''<tr>
            <td><b>{h["producto"]}</b></td>
            <td style="font-family:Space Mono,monospace">${h["mi_precio"]:.2f}</td>
            <td>${h["promedio"]:.2f}</td>
            <td>${h["minimo"]:.2f}</td>
            <td>${h["maximo"]:.2f}</td>
            <td style="color:#00E676">${h["ganancia"]:.2f}</td>
            <td style="color:#888">{h["margen"]}%</td>
            <td style="color:#FFD600">${h["precio_optimo"]:.2f}</td>
            <td style="color:{vcolor};font-size:0.75rem;font-family:Space Mono,monospace">{h["veredicto"]}</td>
        </tr>'''
    st.markdown(f'''
    <table class="res-table">
        <thead><tr>
            <th>Producto</th><th>Mi precio</th><th>Promedio</th>
            <th>Mín</th><th>Máx</th><th>Ganancia</th><th>Margen</th>
            <th>Precio óptimo</th><th>Veredicto</th>
        </tr></thead>
        <tbody>{filas_h}</tbody>
    </table>
    ''', unsafe_allow_html=True)

    if st.button("🗑  Limpiar historial"):
        st.session_state.historial_precios = []
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — GENERADOR DE PUBLICACIONES
# ══════════════════════════════════════════════════════════════════════════════
