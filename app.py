# ═══════════════════════════════════════════════════════════════
# ADALIMPORT — app.py  (punto de entrada principal)
# Responsabilidades: config, sidebar, router custom
# Las páginas se ejecutan via exec() para el router custom
# ═══════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════════
# FIX DEFINITIVO v4 — Estructura real: Scripts/database/db_manager.py
# ──────────────────────────────────────────────────────────────────────────────
import sys, os as _os, builtins as _builtins, importlib as _importlib

_ROOT   = _os.path.dirname(_os.path.abspath(__file__))   # Scripts/
_DB_DIR = _os.path.join(_ROOT, "database")               # Scripts/database/

# Capa 1: sys.path — raíz + subcarpeta database
for _p in (_DB_DIR, _ROOT):                              # DB_DIR primero
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Capa 2: cwd
_os.chdir(_ROOT)

# Capa 3: builtins — heredados por TODOS los exec() anidados
_builtins._ADALIMPORT_ROOT   = _ROOT
_builtins._ADALIMPORT_DB_DIR = _DB_DIR

# ── Flag USE_SUPABASE ─────────────────────────────────────────────────────────
# Controla qué backend de BD usa toda la app.
# · False (default) → SQLite local vía db_manager.py      (desarrollo sin internet)
# · True            → Supabase PostgreSQL vía db_supabase.py (staging / producción)
#
# Cómo activarlo:
#   · Local:            añade USE_SUPABASE = "true" en secrets.toml  → [general]
#   · Streamlit Cloud:  añade USE_SUPABASE = "true" en Secrets del proyecto
#   · Fallback:         variable de entorno USE_SUPABASE=true
# ─────────────────────────────────────────────────────────────────────────────
def _resolver_use_supabase() -> bool:
    try:
        import streamlit as _st
        val = _st.secrets.get("general", {}).get("USE_SUPABASE", "false")
        return str(val).lower() == "true"
    except Exception:
        pass
    return _os.getenv("USE_SUPABASE", "false").lower() == "true"

_USE_SUPABASE = _resolver_use_supabase()

# Capa 4: sys.modules — pre-carga con directorio correcto por módulo
# Si USE_SUPABASE=true, db_supabase se registra bajo el nombre "db_manager"
# para que todas las páginas que hacen `from db_manager import ...`
# reciban automáticamente la implementación Supabase. 0 cambios en páginas.
_DB_MOD_NAME = "db_supabase" if _USE_SUPABASE else "db_manager"
_DB_MOD_DIR  = _DB_DIR

_CORE_MODULES = [
    (_DB_MOD_NAME,              _DB_MOD_DIR),
    ("calculadora_importacion", _ROOT),
    ("config_envios",           _ROOT),
    ("exportador_reportes",     _ROOT),
    ("generador_publicaciones", _ROOT),
    ("styles_adalimport",       _ROOT),
]
for _mod_name, _mod_dir in _CORE_MODULES:
    if _mod_name not in sys.modules:
        if _mod_dir not in sys.path:
            sys.path.insert(0, _mod_dir)
        try:
            _mod_obj = _importlib.import_module(_mod_name)
            sys.modules[_mod_name] = _mod_obj
            # Alias: si usamos Supabase, registrarlo también como "db_manager"
            if _USE_SUPABASE and _mod_name == "db_supabase":
                sys.modules["db_manager"] = _mod_obj
        except Exception as _e:
            import warnings
            warnings.warn(f"ADALIMPORT pre-load '{_mod_name}': {_e}")
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st
import pandas as pd
import contextlib as _contextlib
from styles_adalimport import aplicar_estilos

st.set_page_config(
    page_title="ADALIMPORT",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Analítica")
# RECUERDA: Cambia el enlace de abajo por la URL real de tu dashboard en Vercel
st.sidebar.link_button("Ir al Dashboard (Vercel)", "https://adalimport-web.vercel.app/admin/dashboard", use_container_width=True)
st.sidebar.markdown("---")

aplicar_estilos()

# ── Cargar configuración desde BD en el inicio de la sesión ──────────
if "_config_cargada" not in st.session_state:
    try:
        from db_manager import cargar_configuracion
        _db_config = cargar_configuracion()
        if _db_config:
            # Poblamos el session_state con lo guardado en SQLite
            for key, val in _db_config.items():
                st.session_state[key] = val
    except Exception:
        pass
    st.session_state["_config_cargada"] = True


# ── helpers ──────────────────────────────────────────────────
def _safe_float(val, default=0.0):
    try:
        if val is None or (isinstance(val, float) and __import__('math').isnan(val)):
            return default
        return float(val)
    except: return default

def _safe_int(val, default=1):
    try:
        if val is None or (isinstance(val, float) and __import__('math').isnan(val)):
            return default
        return int(float(val))
    except: return default

def _safe_str(val, default=""):
    try:
        if val is None or (isinstance(val, float) and __import__('math').isnan(val)):
            return default
        s = str(val).strip()
        return default if s.lower() == 'nan' else s
    except: return default

import types
_helpers = types.SimpleNamespace(safe_float=_safe_float, safe_int=_safe_int, safe_str=_safe_str)

# ── Courier vía query_params ──────────────────────────────────
if "courier_sel" not in st.session_state:
    st.session_state.courier_sel = None
_qp_courier = st.query_params.get("courier", None)
if _qp_courier:
    st.session_state.courier_sel = _qp_courier
    st.query_params.clear()
    st.rerun()

# ── Catálogo ──────────────────────────────────────────────────
CATALOGO_PATH = "productos_catalogo.xlsm"
if "catalogo_df" not in st.session_state:
    try:
        df_cat = pd.read_excel(CATALOGO_PATH, sheet_name="catalogo")
        df_cat.columns = (df_cat.columns.str.strip().str.lower()
                          .str.replace(r"[^a-záéíóúñ_]", "_", regex=True)
                          .str.replace(r"_+", "_", regex=True).str.strip("_"))
        rename_map = {}
        for col in df_cat.columns:
            if col.startswith("product") or col == "producto": rename_map[col] = "producto"
            elif col.startswith("marc"):  rename_map[col] = "marca"
            elif col.startswith("tiend"): rename_map[col] = "tienda"
            elif col.startswith("costo"): rename_map[col] = "costo"
            elif col.startswith("peso"):  rename_map[col] = "peso_lb"
            elif col.startswith("larg"):  rename_map[col] = "largo"
            elif col.startswith("anch"):  rename_map[col] = "ancho"
            elif col.startswith("alt"):   rename_map[col] = "alto"
            elif col.startswith("cant"):  rename_map[col] = "cantidad"
            elif col.startswith("descr"): rename_map[col] = "descripcion"
            elif col.startswith("activ"): rename_map[col] = "activo"
        df_cat = df_cat.rename(columns=rename_map)
        st.session_state.catalogo_df = df_cat
    except FileNotFoundError:
        st.session_state.catalogo_df = None

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    # ── Logo marca ───────────────────────────────────────────────────────────
    st.markdown('''
    <div class="ada-logo-wrap">
        <div>
            <div class="ada-logo">ADALIMPORT</div>
            <div class="ada-sub" style="font-size:0.72rem;letter-spacing:2.5px;color:#B8963E;font-weight:600">SISTEMA DE IMPORTACIÓN</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # ── Courier activo ───────────────────────────────────────────────────────
    from config_envios import COURIERS
    courier_sel = st.session_state.get("courier_sel", None)
    st.markdown("**🚚 Empresa courier**")
    if courier_sel:
        courier_cfg  = COURIERS[courier_sel]
        _consol      = courier_cfg.get("consolidado_dias")
        _consol_html = f'<br>📦 <b style="color:#B8963E">Consolida {_consol} días</b> desde 1er artículo' if _consol else ''
        _aer_us  = courier_cfg["aereo"]["us"]
        _aer_cn  = courier_cfg["aereo"].get("cn")
        _mar_us  = courier_cfg["maritimo"]["us"]
        _mar_cn  = courier_cfg["maritimo"].get("cn")
        _rows  = f'✈️ USA: <b style="color:#aaa">${_aer_us["tarifa_lb"]:.2f}/lb</b> · mín ${_aer_us["minimo_usd"]:.2f}<br>'
        if _aer_cn: _rows += f'✈️ CN: <b style="color:#aaa">${_aer_cn["tarifa_lb"]:.2f}/lb</b> · mín ${_aer_cn["minimo_usd"]:.2f}<br>'
        _rows += f'🚢 USA: <b style="color:#aaa">${_mar_us["tarifa_ft3"]:.2f}/ft³</b> · mín ${_mar_us["minimo_usd"]:.2f}<br>'
        if _mar_cn: _rows += f'🚢 CN: <b style="color:#aaa">${_mar_cn["tarifa_ft3"]:.2f}/ft³</b> · mín ${_mar_cn["minimo_usd"]:.2f}<br>'
        st.markdown(f"""
        <div style="background:#0b1a0b;border:1px solid #1a4a1a;border-radius:8px;
                    padding:0.6rem 0.9rem;font-size:0.75rem;color:#666;margin-bottom:0.5rem">
        <div style="color:#00E676;font-weight:700;font-size:0.8rem;margin-bottom:0.3rem">
            ✅ {courier_sel}
        </div>
        {_rows}{_consol_html}
        </div>""", unsafe_allow_html=True)
        if st.button("🔄 Cambiar courier", use_container_width=True):
            st.session_state.courier_sel = None
            st.rerun()
    else:
        st.markdown("""
        <div style="background:#1a1000;border:1px solid #B8963E;border-radius:8px;
                    padding:0.6rem 0.9rem;font-size:0.78rem;color:#888;margin-bottom:0.5rem">
        ⬅️ Selecciona una empresa en la <b style="color:#B8963E">pantalla de inicio</b>
        </div>""", unsafe_allow_html=True)

    st.markdown("**🛒 MercadoLibre**")

    # ── Sincronizar con _config_master (y la BD) ──────────
    _cfg_comision = st.session_state.get("cfg_comision_ml", 11.0)
    _cfg_ganancia = st.session_state.get("cfg_margen_gan",  35.0)
    _cfg_capital  = st.session_state.get("cfg_capital",    150.0)
    _cfg_tax_az   = st.session_state.get("cfg_tax_amazon",   7.0)
    _cfg_tax_eb   = st.session_state.get("cfg_tax_ebay",     7.0)
    _cfg_tax_wm   = st.session_state.get("cfg_tax_walmart",  7.0)
    _cfg_env_eb   = st.session_state.get("cfg_env_ebay",     5.0)

    comision    = st.number_input("Comisión ML (%)",    value=_cfg_comision,  step=0.5) / 100
    margen_gan  = st.number_input("Ganancia deseada (%)", value=_cfg_ganancia, step=1.0,
                                   help="% sobre el precio de venta ML. 35% = de cada $100 vendidos, $35 es tu ganancia.") / 100
    capital     = st.number_input("Mi capital ($)",     value=_cfg_capital, step=5.0)

    st.markdown("---")
    st.markdown("**🧾 Sales Tax por tienda (defaults)**")
    tax_amazon   = st.number_input("Amazon (%)",   value=_cfg_tax_az, step=0.5, format="%.1f") / 100
    tax_ebay     = st.number_input("eBay (%)",     value=_cfg_tax_eb, step=0.5, format="%.1f") / 100
    tax_walmart  = st.number_input("Walmart (%)",  value=_cfg_tax_wm, step=0.5, format="%.1f") / 100
    env_int_ebay = st.number_input("Env. interno eBay ($)", value=_cfg_env_eb, step=0.5, format="%.2f")

    # ── Reflejar cambios del sidebar → session_state ─────
    st.session_state["cfg_comision_ml"]  = round(comision    * 100, 2)
    st.session_state["cfg_margen_gan"]   = round(margen_gan  * 100, 2)
    st.session_state["cfg_capital"]      = capital
    st.session_state["cfg_tax_amazon"]   = round(tax_amazon  * 100, 2)
    st.session_state["cfg_tax_ebay"]     = round(tax_ebay    * 100, 2)
    st.session_state["cfg_tax_walmart"]  = round(tax_walmart * 100, 2)
    st.session_state["cfg_env_ebay"]     = env_int_ebay

    st.markdown("---")
    st.markdown(
        f"<small style='color:#444'>"
        f"Courier: <b style='color:#00E676'>{courier_sel or '—'}</b><br>"
        f"ML: <b style='color:#888'>{comision*100:.0f}%</b> · "
        f"Ganancia: <b style='color:#00E676'>{margen_gan*100:.0f}%</b> · "
        f"Capital: <b style='color:#888'>${capital:.0f}</b>"
        f"</small>",
        unsafe_allow_html=True
    )

    # ── Acceso a Configuración Maestra ───────────────────────────────────────
    st.markdown("---")

    # ── Backend de BD activo ──────────────────────────────────────────────────
    if _USE_SUPABASE:
        st.markdown(
            '<div style="background:rgba(0,230,118,0.06);border:1px solid rgba(0,230,118,0.2);'
            'border-radius:8px;padding:6px 12px;font-size:0.72rem;color:rgba(0,230,118,0.8);'
            'font-family:\'DM Mono\',monospace;text-align:center;">'
            '🟢 BD · Supabase (PostgreSQL)'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="background:rgba(184,150,62,0.05);border:1px solid rgba(184,150,62,0.15);'
            'border-radius:8px;padding:6px 12px;font-size:0.72rem;color:rgba(184,150,62,0.6);'
            'font-family:\'DM Mono\',monospace;text-align:center;">'
            '🟡 BD · SQLite (local)'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    _cfg_pendientes = st.session_state.get("cfg_cambios_pendientes", False)
    _badge_html = ""
    if _cfg_pendientes:
        _badge_html = '<span style="display:inline-block;font-size:0.58rem;font-weight:700;letter-spacing:1px;text-transform:uppercase;padding:2px 7px;border-radius:10px;background:#1a0f00;color:#B8963E;border:1px solid #B8963E;margin-left:6px;vertical-align:middle">PENDIENTE</span>'

    st.markdown(f"""
    <div style="font-size:0.62rem;letter-spacing:2px;text-transform:uppercase;
                color:#374151;font-family:'DM Mono',monospace;margin-bottom:6px">
    ⚙️ Administrador{_badge_html}
    </div>""", unsafe_allow_html=True)

    if st.button(
        "⚙️ Ajustes de Administrador",
        use_container_width=True,
        key="sidebar_btn_config",
        type="secondary",
        help="Editar tarifas, márgenes y capital en el panel maestro."
    ):
        st.session_state["pagina_activa"] = "config"
        st.rerun()

# ── Inyectar parámetros en módulos ────────────────────────────
import config_envios as cfg
if courier_sel:
    cfg.COURIER_ACTIVO = courier_sel
cfg.COMISION_ML                    = comision
cfg.MARGEN_GANANCIA                = margen_gan
cfg.SALES_TAX_TIENDAS["Amazon"]    = tax_amazon
cfg.SALES_TAX_TIENDAS["eBay"]      = tax_ebay
cfg.SALES_TAX_TIENDAS["Walmart"]   = tax_walmart
cfg.ENVIO_INTERNO_TIENDAS["eBay"]  = env_int_ebay

# ─── ROUTER CUSTOM ────────────────────────────────────────────
if not courier_sel:
    exec(open("pages/_bienvenida.py", encoding="utf-8").read())
else:
    exec(open("pages/_router.py", encoding="utf-8").read())