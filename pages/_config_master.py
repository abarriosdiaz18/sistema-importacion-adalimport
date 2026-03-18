# ═══════════════════════════════════════════════════════════════════════════════
#  ADALIMPORT — pages/_config_master.py  v2.0
#  Panel de Configuración Maestra (⚙️ Admin)
#
#  Responsabilidades:
#   · Resumen At-a-Glance de configuración activa (PRIMERO, antes de cualquier form)
#   · Edición dinámica de reglas de negocio sin tocar el código fuente
#   · Actúa como capa de sobreescritura sobre config_envios.py vía session_state
#   · Los cambios se propagan globalmente en tiempo real y se PERSISTEN en SQLite
#
#  Reglas de Oro respetadas:
#   · ATOMICIDAD  → No importa nada de _lote.py / _validar.py / _publicaciones.py
#   · PERSISTENCIA → Guarda en DB_MANAGER al presionar APLICAR
#   · DISEÑO      → Navy / Oro (#B8963E) / Verde Neón (#00E676), tipografía Syne+Inter+DM Mono
# ═══════════════════════════════════════════════════════════════════════════════

import streamlit as st
import config_envios as cfg

try:
    from db_manager import guardar_configuracion
    _DB_DISPONIBLE = True
except ImportError:
    _DB_DISPONIBLE = False

# ══════════════════════════════════════════════════════════════════════════════
#  INICIALIZAR session_state con defaults de config_envios.py
#  Si app.py ya cargó la base de datos en session_state, se respetan esos valores.
# ══════════════════════════════════════════════════════════════════════════════
def _init_config_state():
    """Puebla st.session_state con los valores actuales de cfg si aún no existen."""
    courier_activo = st.session_state.get("courier_sel") or cfg.COURIER_ACTIVO
    courier_data   = cfg.COURIERS.get(courier_activo, {})
    origen_activo  = st.session_state.get("_cfg_origen_logistica", "us")

    # ── Finanzas ──────────────────────────────────────────────────────────────
    if "cfg_comision_ml" not in st.session_state:
        st.session_state["cfg_comision_ml"]    = round(cfg.COMISION_ML * 100, 2)
    if "cfg_margen_gan" not in st.session_state:
        st.session_state["cfg_margen_gan"]     = round(cfg.MARGEN_GANANCIA * 100, 2)
    if "cfg_margen_seg" not in st.session_state:
        st.session_state["cfg_margen_seg"]     = round(cfg.MARGEN_SEGURIDAD * 100, 2)

    # ── Presupuesto ───────────────────────────────────────────────────────────
    if "cfg_capital" not in st.session_state:
        st.session_state["cfg_capital"]        = 150.0   # Default histórico

    # ── Logística: tarifas del courier activo ─────────────────────────────────
    _aereo    = courier_data.get("aereo",    {}).get(origen_activo, {})
    _maritimo = courier_data.get("maritimo", {}).get(origen_activo, {})
    if "cfg_tarifa_lb" not in st.session_state:
        st.session_state["cfg_tarifa_lb"]      = _aereo.get("tarifa_lb",   cfg.TARIFA_AEREA_LIBRA)
    if "cfg_minimo_aereo" not in st.session_state:
        st.session_state["cfg_minimo_aereo"]   = _aereo.get("minimo_usd",  cfg.MINIMO_AEREO)
    if "cfg_tarifa_ft3" not in st.session_state:
        st.session_state["cfg_tarifa_ft3"]     = _maritimo.get("tarifa_ft3", cfg.TARIFA_MARITIMA_FT3)
    if "cfg_minimo_maritimo" not in st.session_state:
        st.session_state["cfg_minimo_maritimo"]= _maritimo.get("minimo_usd", cfg.MINIMO_MARITIMO)

    # ── Sales Tax ─────────────────────────────────────────────────────────────
    if "cfg_tax_amazon"  not in st.session_state:
        st.session_state["cfg_tax_amazon"]     = round(cfg.SALES_TAX_TIENDAS.get("Amazon", 0.07) * 100, 2)
    if "cfg_tax_ebay"    not in st.session_state:
        st.session_state["cfg_tax_ebay"]       = round(cfg.SALES_TAX_TIENDAS.get("eBay",   0.07) * 100, 2)
    if "cfg_tax_walmart" not in st.session_state:
        st.session_state["cfg_tax_walmart"]    = round(cfg.SALES_TAX_TIENDAS.get("Walmart",0.07) * 100, 2)
    if "cfg_env_ebay"    not in st.session_state:
        st.session_state["cfg_env_ebay"]       = cfg.ENVIO_INTERNO_TIENDAS.get("eBay", 5.0)

    # ── Flag de modificación pendiente ────────────────────────────────────────
    if "cfg_cambios_pendientes" not in st.session_state:
        st.session_state["cfg_cambios_pendientes"] = False

_init_config_state()


# ══════════════════════════════════════════════════════════════════════════════
#  FUNCIÓN MAESTRA: Inyectar cambios en cfg.*, session_state y SQLite
# ══════════════════════════════════════════════════════════════════════════════
def _aplicar_cambios_config():
    """
    Sobreescribe temporalmente los atributos de config_envios (cfg.*) con los
    valores editados, los actualiza en session_state y LOS GUARDA EN LA BASE DE DATOS.
    """
    courier_activo = st.session_state.get("courier_sel") or cfg.COURIER_ACTIVO
    origen         = st.session_state.get("_cfg_origen_logistica", "us")

    # ── 1. Finanzas → cfg.* ───────────────────────────────────────────────────
    cfg.COMISION_ML      = st.session_state["cfg_comision_ml"]    / 100.0
    cfg.MARGEN_GANANCIA  = st.session_state["cfg_margen_gan"]     / 100.0
    cfg.MARGEN_SEGURIDAD = st.session_state["cfg_margen_seg"]     / 100.0

    # ── 2. Logística → cfg.COURIERS (mutación en memoria) ─────────────────────
    if courier_activo in cfg.COURIERS:
        _courier = cfg.COURIERS[courier_activo]
        if origen in _courier.get("aereo", {}):
            _courier["aereo"][origen]["tarifa_lb"]     = st.session_state["cfg_tarifa_lb"]
            _courier["aereo"][origen]["minimo_usd"]    = st.session_state["cfg_minimo_aereo"]
        if origen in _courier.get("maritimo", {}):
            _courier["maritimo"][origen]["tarifa_ft3"] = st.session_state["cfg_tarifa_ft3"]
            _courier["maritimo"][origen]["minimo_usd"] = st.session_state["cfg_minimo_maritimo"]

    # ── 3. Sales Tax ──────────────────────────────────────────────────────────
    cfg.SALES_TAX_TIENDAS["Amazon"]   = st.session_state["cfg_tax_amazon"]  / 100.0
    cfg.SALES_TAX_TIENDAS["eBay"]     = st.session_state["cfg_tax_ebay"]    / 100.0
    cfg.SALES_TAX_TIENDAS["Walmart"]  = st.session_state["cfg_tax_walmart"] / 100.0
    cfg.ENVIO_INTERNO_TIENDAS["eBay"] = st.session_state["cfg_env_ebay"]

    # ── 4. Capital + Courier ──────────────────────────────────────────────────
    cfg.COURIER_ACTIVO = courier_activo

    # ── 5. PERSISTENCIA EN SQLITE ─────────────────────────────────────────────
    if _DB_DISPONIBLE:
        config_a_guardar = {
            "cfg_comision_ml":     st.session_state["cfg_comision_ml"],
            "cfg_margen_gan":      st.session_state["cfg_margen_gan"],
            "cfg_margen_seg":      st.session_state["cfg_margen_seg"],
            "cfg_capital":         st.session_state["cfg_capital"],
            "cfg_tarifa_lb":       st.session_state["cfg_tarifa_lb"],
            "cfg_minimo_aereo":    st.session_state["cfg_minimo_aereo"],
            "cfg_tarifa_ft3":      st.session_state["cfg_tarifa_ft3"],
            "cfg_minimo_maritimo": st.session_state["cfg_minimo_maritimo"],
            "cfg_tax_amazon":      st.session_state["cfg_tax_amazon"],
            "cfg_tax_ebay":        st.session_state["cfg_tax_ebay"],
            "cfg_tax_walmart":     st.session_state["cfg_tax_walmart"],
            "cfg_env_ebay":        st.session_state["cfg_env_ebay"],
            "_cfg_origen_logistica": origen
        }
        guardar_configuracion(config_a_guardar)

    # ── 6. Limpiar flag y notificar ───────────────────────────────────────────
    st.session_state["cfg_cambios_pendientes"] = False
    st.session_state["_cfg_flash_ok"]          = True


def _resetear_config():
    """Borra todas las claves cfg_* para que _init_config_state() recargue los defaults."""
    _claves_cfg = [
        "cfg_comision_ml","cfg_margen_gan","cfg_margen_seg","cfg_capital",
        "cfg_tarifa_lb","cfg_minimo_aereo","cfg_tarifa_ft3","cfg_minimo_maritimo",
        "cfg_tax_amazon","cfg_tax_ebay","cfg_tax_walmart","cfg_env_ebay",
        "cfg_cambios_pendientes","_cfg_flash_ok",
    ]
    for _k in _claves_cfg:
        st.session_state.pop(_k, None)
    
    # También podemos enviar un dict vacío a la BD para limpiar la persistencia
    if _DB_DISPONIBLE:
        guardar_configuracion({})


# ══════════════════════════════════════════════════════════════════════════════
#  VARIABLES DE RENDER (shorthand)
# ══════════════════════════════════════════════════════════════════════════════
_courier_activo = st.session_state.get("courier_sel") or cfg.COURIER_ACTIVO
_cambios        = st.session_state.get("cfg_cambios_pendientes", False)
_flash_ok       = st.session_state.pop("_cfg_flash_ok", False)

_ss_ml   = st.session_state["cfg_comision_ml"]
_ss_gan  = st.session_state["cfg_margen_gan"]
_ss_cap  = st.session_state["cfg_capital"]
_ss_lb   = st.session_state["cfg_tarifa_lb"]
_ss_mina = st.session_state["cfg_minimo_aereo"]
_ss_ft3  = st.session_state["cfg_tarifa_ft3"]
_ss_minm = st.session_state["cfg_minimo_maritimo"]

# Tarifa representativa para el KPI (5 lb aéreo / 1 ft³ marítimo)
_tarifa_aereo_rep   = max(_ss_lb  * 5,  _ss_mina)
_tarifa_mar_rep     = max(_ss_ft3 * 1,  _ss_minm)


# ══════════════════════════════════════════════════════════════════════════════
#  HERO HEADER
# ══════════════════════════════════════════════════════════════════════════════

# ── Resolver backend de BD activo ─────────────────────────────────────────────
import os as _os_cfg
_use_supabase_cfg = False
try:
    _use_supabase_cfg = str(st.secrets.get("general", {}).get("USE_SUPABASE", "false")).lower() == "true"
except Exception:
    _use_supabase_cfg = _os_cfg.getenv("USE_SUPABASE", "false").lower() == "true"

if _use_supabase_cfg:
    _bd_badge_icon  = "🟢"
    _bd_badge_label = "Supabase · PostgreSQL"
    _bd_badge_color = "#00E676"
    _bd_badge_bg    = "rgba(0,230,118,0.08)"
    _bd_badge_bord  = "rgba(0,230,118,0.25)"
else:
    _bd_badge_icon  = "🟡"
    _bd_badge_label = "SQLite · Local"
    _bd_badge_color = "#B8963E"
    _bd_badge_bg    = "rgba(184,150,62,0.08)"
    _bd_badge_bord  = "rgba(184,150,62,0.25)"

st.markdown(f"""
<div class="cfg-hero">
  <span class="cfg-hero-icon">⚙️</span>
  <div style="flex:1">
    <p class="cfg-hero-title">CONFIGURACIÓN MAESTRA</p>
    <p class="cfg-hero-sub">
      Courier activo: <span style="color:#B8963E;font-weight:700">{_courier_activo}</span>
      &nbsp;·&nbsp; Reglas de negocio editables y guardadas permanentemente
    </p>
  </div>
  <div style="background:{_bd_badge_bg};border:1px solid {_bd_badge_bord};
              border-radius:8px;padding:6px 14px;text-align:center;
              white-space:nowrap;flex-shrink:0;">
    <span style="font-family:'DM Mono',monospace;font-size:0.55rem;
                 letter-spacing:2px;text-transform:uppercase;
                 color:{_bd_badge_color};display:block;margin-bottom:2px;">
      ◈ Base de datos
    </span>
    <span style="font-family:'DM Mono',monospace;font-size:0.75rem;
                 font-weight:600;color:{_bd_badge_color};">
      {_bd_badge_icon} {_bd_badge_label}
    </span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Notificaciones de estado ──────────────────────────────────────────────────
if _flash_ok:
    st.markdown("""
    <div class="cfg-alert-change">
      ✅ &nbsp;<b>Configuración guardada en Base de Datos.</b> Los cálculos se actualizaron permanentemente.
    </div>
    """, unsafe_allow_html=True)

if _cambios:
    st.markdown("""
    <div class="cfg-alert-change" style="border-color:#B8963E;color:#B8963E;background:#120d00;">
      ⚠️ &nbsp;<b>Hay cambios sin aplicar.</b> Presiona <b>APLICAR CONFIGURACIÓN</b> para guardarlos.
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  ★  AT-A-GLANCE BANNER — Estado Actual (SIEMPRE PRIMERO)
#     4 KPIs que reflejan la configuración vigente antes de cualquier formulario
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<p class="cfg-section-title">📊 Configuración Activa — Vista Rápida</p>
""", unsafe_allow_html=True)

# Determinar color del capital según nivel
_cap_hex = "#B8963E"
if _ss_cap >= 5000:
    _cap_hex = "#60a5fa"
elif _ss_cap >= 1000:
    _cap_hex = "#00E676"
elif _ss_cap >= 500:
    _cap_hex = "#e2e8f0"

# Estilos inline para las celdas KPI — no dependen del CSS global
_CELL_BASE = (
    "background:rgba(15,24,41,0.85);"
    "border:1px solid #141e30;"
    "border-radius:10px;"
    "padding:1rem 0.6rem;"
    "text-align:center;"
    "position:relative;"
    "overflow:hidden;"
)
_LABEL_STYLE = (
    "font-family:'DM Mono',monospace;"
    "font-size:0.58rem;"
    "letter-spacing:2.5px;"
    "text-transform:uppercase;"
    "color:#4a5568;"
    "display:block;"
    "margin-bottom:6px;"
)
_SUB_STYLE = (
    "font-family:'DM Mono',monospace;"
    "font-size:0.62rem;"
    "color:#4a5568;"
    "display:block;"
    "margin-top:4px;"
)

def _kpi_cell(top_color, icon, label, value, value_color, sub):
    """Genera HTML de una celda KPI autocontenida con estilos inline."""
    return f"""
<div style="{_CELL_BASE}border-top:2px solid {top_color};">
  <div style="font-size:1.3rem;line-height:1;margin-bottom:5px">{icon}</div>
  <span style="{_LABEL_STYLE}">{label}</span>
  <div style="font-family:'DM Mono',monospace;font-size:1.55rem;font-weight:500;
              line-height:1;color:{value_color}">{value}</div>
  <span style="{_SUB_STYLE}">{sub}</span>
</div>"""

# Contenedor externo del banner
st.markdown("""
<div style="background:linear-gradient(135deg,#080e1a 0%,#05090f 100%);
            border:1px solid #141e30;border-top:3px solid #B8963E;
            border-radius:14px;padding:1.2rem 1.6rem;margin-bottom:1.6rem;">
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;">
""", unsafe_allow_html=True)

_kpi1, _kpi2, _kpi3, _kpi4 = st.columns(4)

with _kpi1:
    st.markdown(_kpi_cell(
        top_color="#B8963E",
        icon="🏷️",
        label="Comisión ML",
        value=f"{_ss_ml:.1f}%",
        value_color="#B8963E",
        sub="sobre precio de venta"
    ), unsafe_allow_html=True)

with _kpi2:
    st.markdown(_kpi_cell(
        top_color="#00E676",
        icon="📈",
        label="Margen Deseado",
        value=f"{_ss_gan:.1f}%",
        value_color="#00E676",
        sub="ganancia neta objetivo"
    ), unsafe_allow_html=True)

with _kpi3:
    st.markdown(_kpi_cell(
        top_color="#60a5fa",
        icon="🚚",
        label=f"Courier · {_courier_activo}",
        value=f"✈️ ${_tarifa_aereo_rep:.2f}",
        value_color="#60a5fa",
        sub=f"🚢 ${_tarifa_mar_rep:.2f} · mín 5lb / 1ft³"
    ), unsafe_allow_html=True)

with _kpi4:
    st.markdown(_kpi_cell(
        top_color="#94a3b8",
        icon="💵",
        label="Capital Disponible",
        value=f"${_ss_cap:,.0f}",
        value_color=_cap_hex,
        sub="USD base operativo"
    ), unsafe_allow_html=True)

# Cerrar el div del banner (decorativo — los columns ya cerraron el grid real)
st.markdown("</div></div>", unsafe_allow_html=True)

st.markdown('<div class="cfg-sep"></div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  BLOQUE 1 — FINANZAS Y COMISIONES
# ══════════════════════════════════════════════════════════════════════════════
with st.expander("💰  FINANZAS · Comisiones y Márgenes", expanded=True):
    st.markdown('<p class="cfg-section-title">Parámetros Financieros</p>', unsafe_allow_html=True)

    _f1, _f2, _f3 = st.columns(3)

    with _f1:
        st.markdown('<div class="cfg-card cfg-card-accent-gold">', unsafe_allow_html=True)
        _new_ml = st.slider(
            "Comisión MercadoLibre (%)",
            min_value=5.0, max_value=25.0,
            value=float(st.session_state["cfg_comision_ml"]),
            step=0.5,
            help="Porcentaje que cobra ML Venezuela sobre el precio de venta.",
            key="_slider_comision_ml"
        )
        st.markdown(f"""
        <div class="cfg-metric-row">
          <span class="cfg-metric-chip">Actual: <b>{st.session_state['cfg_comision_ml']:.1f}%</b></span>
          <span class="cfg-metric-chip">Config base: <b>11.0%</b></span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        if _new_ml != st.session_state["cfg_comision_ml"]:
            st.session_state["cfg_comision_ml"]        = _new_ml
            st.session_state["cfg_cambios_pendientes"] = True

    with _f2:
        st.markdown('<div class="cfg-card cfg-card-accent-green">', unsafe_allow_html=True)
        _new_gan = st.slider(
            "Margen de Ganancia Deseada (%)",
            min_value=5.0, max_value=70.0,
            value=float(st.session_state["cfg_margen_gan"]),
            step=1.0,
            help="% sobre el precio de venta ML. Ej: 35% = de cada $100 vendidos, $35 es ganancia neta.",
            key="_slider_margen_gan"
        )
        _precio_ej = 10 / (1 - (_new_ml/100) - (_new_gan/100)) if (1 - _new_ml/100 - _new_gan/100) > 0 else 0
        st.markdown(f"""
        <div class="cfg-metric-row">
          <span class="cfg-metric-chip">Actual: <b>{st.session_state['cfg_margen_gan']:.1f}%</b></span>
          <span class="cfg-metric-chip">Costo $10 → PVP <b>${_precio_ej:.2f}</b></span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        if _new_gan != st.session_state["cfg_margen_gan"]:
            st.session_state["cfg_margen_gan"]         = _new_gan
            st.session_state["cfg_cambios_pendientes"] = True

    with _f3:
        st.markdown('<div class="cfg-card cfg-card-accent-blue">', unsafe_allow_html=True)
        _new_seg = st.slider(
            "Margen de Seguridad / Imprevistos (%)",
            min_value=0.0, max_value=10.0,
            value=float(st.session_state["cfg_margen_seg"]),
            step=0.5,
            help="% adicional sobre costo total para cubrir imprevistos (daños, demoras, etc.).",
            key="_slider_margen_seg"
        )
        st.markdown(f"""
        <div class="cfg-metric-row">
          <span class="cfg-metric-chip">Actual: <b>{st.session_state['cfg_margen_seg']:.1f}%</b></span>
          <span class="cfg-metric-chip">Costo $100 → +<b>${_new_seg:.2f}</b> colchón</span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        if _new_seg != st.session_state["cfg_margen_seg"]:
            st.session_state["cfg_margen_seg"]         = _new_seg
            st.session_state["cfg_cambios_pendientes"] = True


# ══════════════════════════════════════════════════════════════════════════════
#  BLOQUE 2 — PRESUPUESTO / CAPITAL
# ══════════════════════════════════════════════════════════════════════════════
with st.expander("💵  PRESUPUESTO · Límite de Capital", expanded=True):
    st.markdown('<p class="cfg-section-title">Control de Capital Disponible</p>', unsafe_allow_html=True)

    _b1, _b2 = st.columns([2, 1])
    with _b1:
        st.markdown('<div class="cfg-card cfg-card-accent-gold">', unsafe_allow_html=True)
        _new_cap = st.number_input(
            "Límite de Capital (USD)",
            min_value=50.0, max_value=100_000.0,
            value=float(st.session_state["cfg_capital"]),
            step=50.0,
            format="%.2f",
            help="Capital máximo disponible para un lote. Referencia para los cálculos.",
            key="_input_capital"
        )
        _new_cap_sl = st.slider(
            "Ajuste rápido →",
            min_value=50.0, max_value=10_000.0,
            value=float(st.session_state["cfg_capital"]),
            step=50.0,
            label_visibility="visible",
            key="_slider_capital"
        )
        _cap_final = _new_cap if _new_cap != st.session_state["cfg_capital"] else _new_cap_sl
        st.markdown('</div>', unsafe_allow_html=True)
        if _cap_final != st.session_state["cfg_capital"]:
            st.session_state["cfg_capital"]            = _cap_final
            st.session_state["cfg_cambios_pendientes"] = True

    with _b2:
        _cap_display = st.session_state["cfg_capital"]
        _tiers = [
            (500,  "🟢 Capital operativo normal"),
            (1000, "🟡 Capital medio — cuidar margen"),
            (5000, "🟠 Capital alto — diversificar lote"),
        ]
        _tier_txt = "🔵 Capital pequeño — priorizar margen"
        for _t, _lbl in _tiers:
            if _cap_display >= _t:
                _tier_txt = _lbl
        st.markdown(f"""
        <div class="cfg-card" style="text-align:center;padding:1.6rem 1rem;">
          <div style="font-family:'DM Mono',monospace;font-size:2rem;
                      font-weight:700;color:#B8963E;line-height:1">
            ${_cap_display:,.0f}
          </div>
          <div style="font-size:0.7rem;color:#64748b;margin-top:6px;
                      font-family:'DM Mono',monospace;letter-spacing:1px">
            USD DISPONIBLE
          </div>
          <div style="font-size:0.72rem;color:#e2e8f0;margin-top:10px;font-family:'Inter',sans-serif">
            {_tier_txt}
          </div>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  BLOQUE 3 — LOGÍSTICA / TARIFAS COURIER
# ══════════════════════════════════════════════════════════════════════════════
with st.expander("🚚  LOGÍSTICA · Tarifas del Courier", expanded=True):
    st.markdown('<p class="cfg-section-title">Tarifas Operativas</p>', unsafe_allow_html=True)

    _courier_data  = cfg.COURIERS.get(_courier_activo, {})
    _origenes_disp = _courier_data.get("origenes", ["us"])
    _origen_labels = {"us": "🇺🇸 USA", "cn": "🇨🇳 China"}
    _origen_opts   = [_origen_labels.get(o, o.upper()) for o in _origenes_disp]
    _origen_actual = st.session_state.get("_cfg_origen_logistica", "us")
    _origen_idx    = _origenes_disp.index(_origen_actual) if _origen_actual in _origenes_disp else 0

    _sel_orig = st.radio(
        "Origen de envío a editar:",
        options=_origen_opts,
        index=_origen_idx,
        horizontal=True,
        key="_radio_origen_log"
    )
    _origen_sel = _origenes_disp[_origen_opts.index(_sel_orig)]
    if _origen_sel != st.session_state.get("_cfg_origen_logistica"):
        _aereo_n    = _courier_data.get("aereo",    {}).get(_origen_sel, {})
        _maritimo_n = _courier_data.get("maritimo", {}).get(_origen_sel, {})
        st.session_state["_cfg_origen_logistica"] = _origen_sel
        st.session_state["cfg_tarifa_lb"]         = _aereo_n.get("tarifa_lb",    cfg.TARIFA_AEREA_LIBRA)
        st.session_state["cfg_minimo_aereo"]       = _aereo_n.get("minimo_usd",   cfg.MINIMO_AEREO)
        st.session_state["cfg_tarifa_ft3"]         = _maritimo_n.get("tarifa_ft3", cfg.TARIFA_MARITIMA_FT3)
        st.session_state["cfg_minimo_maritimo"]    = _maritimo_n.get("minimo_usd",  cfg.MINIMO_MARITIMO)
        st.rerun()

    st.markdown('<div class="cfg-sep"></div>', unsafe_allow_html=True)

    _l1, _l2 = st.columns(2)

    with _l1:
        st.markdown('<div class="cfg-card cfg-card-accent-green">', unsafe_allow_html=True)
        st.markdown("**✈️ Tarifa Aérea**")
        _new_lb = st.number_input(
            "Tarifa por Libra (USD/lb)",
            min_value=0.5, max_value=50.0,
            value=float(st.session_state["cfg_tarifa_lb"]),
            step=0.25, format="%.2f",
            key="_input_tarifa_lb"
        )
        _new_min_a = st.number_input(
            "Mínimo Aéreo (USD)",
            min_value=0.0, max_value=500.0,
            value=float(st.session_state["cfg_minimo_aereo"]),
            step=1.0, format="%.2f",
            key="_input_minimo_aereo"
        )
        st.markdown(f"""
        <div class="cfg-metric-row" style="margin-top:0.6rem">
          <span class="cfg-metric-chip">5 lb → <b>${max(_new_lb*5, _new_min_a):.2f}</b></span>
          <span class="cfg-metric-chip">10 lb → <b>${max(_new_lb*10, _new_min_a):.2f}</b></span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        if _new_lb != st.session_state["cfg_tarifa_lb"] or _new_min_a != st.session_state["cfg_minimo_aereo"]:
            st.session_state["cfg_tarifa_lb"]          = _new_lb
            st.session_state["cfg_minimo_aereo"]       = _new_min_a
            st.session_state["cfg_cambios_pendientes"] = True

    with _l2:
        st.markdown('<div class="cfg-card cfg-card-accent-blue">', unsafe_allow_html=True)
        st.markdown("**🚢 Tarifa Marítima**")
        _new_ft3 = st.number_input(
            "Tarifa por Pie Cúbico (USD/ft³)",
            min_value=0.5, max_value=200.0,
            value=float(st.session_state["cfg_tarifa_ft3"]),
            step=0.5, format="%.2f",
            key="_input_tarifa_ft3"
        )
        _new_min_m = st.number_input(
            "Mínimo Marítimo (USD)",
            min_value=0.0, max_value=500.0,
            value=float(st.session_state["cfg_minimo_maritimo"]),
            step=1.0, format="%.2f",
            key="_input_minimo_maritimo"
        )
        st.markdown(f"""
        <div class="cfg-metric-row" style="margin-top:0.6rem">
          <span class="cfg-metric-chip">1 ft³ → <b>${max(_new_ft3*1, _new_min_m):.2f}</b></span>
          <span class="cfg-metric-chip">5 ft³ → <b>${max(_new_ft3*5, _new_min_m):.2f}</b></span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        if _new_ft3 != st.session_state["cfg_tarifa_ft3"] or _new_min_m != st.session_state["cfg_minimo_maritimo"]:
            st.session_state["cfg_tarifa_ft3"]         = _new_ft3
            st.session_state["cfg_minimo_maritimo"]    = _new_min_m
            st.session_state["cfg_cambios_pendientes"] = True


# ══════════════════════════════════════════════════════════════════════════════
#  BLOQUE 4 — SALES TAX Y ENVÍO INTERNO
# ══════════════════════════════════════════════════════════════════════════════
with st.expander("🧾  IMPUESTOS · Sales Tax y Envío Interno USA", expanded=False):
    st.markdown('<p class="cfg-section-title">Cargos en Origen (USA)</p>', unsafe_allow_html=True)

    _t1, _t2, _t3, _t4 = st.columns(4)

    with _t1:
        _new_tax_az = st.number_input(
            "Amazon Tax (%)", min_value=0.0, max_value=15.0,
            value=float(st.session_state["cfg_tax_amazon"]),
            step=0.5, format="%.1f", key="_input_tax_amazon"
        )
        if _new_tax_az != st.session_state["cfg_tax_amazon"]:
            st.session_state["cfg_tax_amazon"]         = _new_tax_az
            st.session_state["cfg_cambios_pendientes"] = True

    with _t2:
        _new_tax_eb = st.number_input(
            "eBay Tax (%)", min_value=0.0, max_value=15.0,
            value=float(st.session_state["cfg_tax_ebay"]),
            step=0.5, format="%.1f", key="_input_tax_ebay"
        )
        if _new_tax_eb != st.session_state["cfg_tax_ebay"]:
            st.session_state["cfg_tax_ebay"]           = _new_tax_eb
            st.session_state["cfg_cambios_pendientes"] = True

    with _t3:
        _new_tax_wm = st.number_input(
            "Walmart Tax (%)", min_value=0.0, max_value=15.0,
            value=float(st.session_state["cfg_tax_walmart"]),
            step=0.5, format="%.1f", key="_input_tax_walmart"
        )
        if _new_tax_wm != st.session_state["cfg_tax_walmart"]:
            st.session_state["cfg_tax_walmart"]        = _new_tax_wm
            st.session_state["cfg_cambios_pendientes"] = True

    with _t4:
        _new_env_eb = st.number_input(
            "Env. Interno eBay ($)", min_value=0.0, max_value=50.0,
            value=float(st.session_state["cfg_env_ebay"]),
            step=0.5, format="%.2f", key="_input_env_ebay"
        )
        if _new_env_eb != st.session_state["cfg_env_ebay"]:
            st.session_state["cfg_env_ebay"]           = _new_env_eb
            st.session_state["cfg_cambios_pendientes"] = True

    st.markdown("""
    <div style="font-size:0.68rem;color:#64748b;margin-top:0.6rem;
                font-family:'DM Mono',monospace;letter-spacing:0.5px">
    ℹ️ AliExpress y Otro heredan 0% tax de fábrica. Configúralos en config_envios.py si cambian.
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  BLOQUE 5 — BOTONES DE ACCIÓN
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="cfg-sep"></div>', unsafe_allow_html=True)

_ba1, _ba2, _ba3 = st.columns([3, 1, 1])

with _ba1:
    if st.button(
        "⚡ APLICAR CONFIGURACIÓN",
        key="cfg_btn_apply",
        use_container_width=True,
        type="primary",
        disabled=not st.session_state.get("cfg_cambios_pendientes", False)
    ):
        _aplicar_cambios_config()
        st.rerun()

with _ba2:
    if st.button("↩️ Resetear", key="cfg_btn_reset", use_container_width=True):
        _resetear_config()
        st.rerun()

with _ba3:
    if st.button("📦 Ir al Lote", key="cfg_btn_lote", use_container_width=True):
        st.session_state["pagina_activa"] = "lote"
        st.rerun()

# ── Nota técnica ──────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="margin-top:1.4rem;background:#070d1a;border:1px solid #0f1829;
            border-radius:8px;padding:0.8rem 1.2rem;font-size:0.68rem;
            color:#374151;font-family:'DM Mono',monospace;line-height:1.7">
  <b style="color:#B8963E">ℹ️ NOTA TÉCNICA</b> — Los cambios aplicados aquí se guardan
  en la base de datos (<span style="color:{_bd_badge_color}">{_bd_badge_icon} {_bd_badge_label}</span>)
  y persisten permanentemente, sobreescribiendo
  a <code style="color:#B8963E">config_envios.py</code>.
</div>
""", unsafe_allow_html=True)