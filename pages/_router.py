# ── Imports necesarios para el router ─────────────────────────
import streamlit as st
import contextlib as _contextlib
import sys as _sys, os as _os, builtins as _builtins

# ── Garantizar sys.path en este nivel de exec() ───────────────────────────────
_ROUTER_ROOT = getattr(_builtins, "_ADALIMPORT_ROOT", None) or _os.getcwd()
if _ROUTER_ROOT not in _sys.path:
    _sys.path.insert(0, _ROUTER_ROOT)
_os.chdir(_ROUTER_ROOT)

# ── modules/ disponible para todas las páginas del pipeline ──────────────────
_MODULES_DIR = _os.path.join(_ROUTER_ROOT, "modules")
if _MODULES_DIR not in _sys.path:
    _sys.path.insert(0, _MODULES_DIR)

# ══════════════════════════════════════════════════════════════════════════════
# ROUTER CUSTOM v3.0 — Nav simplificada a 5 ítems
#
# Nav bar (visible):
#   INICIO · PIPELINE · HISTORIAL · VALIDAR · CONFIG
#
# Rutas pipeline wizard (nuevas):
#   "paso1" | "paso2" | "paso3" | "paso4"
#
# Rutas legacy (conservadas como fallback silencioso, sin botón en nav):
#   "lote" | "publicaciones" | "estudio_visual"
#
# Las rutas legacy siguen funcionando si algún botón interno las invoca,
# pero no tienen ítem visible en la nav bar.
# ══════════════════════════════════════════════════════════════════════════════
if "pagina_activa" not in st.session_state:
    st.session_state["pagina_activa"] = "paso1"

_pagina = st.session_state["pagina_activa"]

# ── Claves de sesión del lote activo ─────────────────────────────────────────
_LOTE_KEYS = [
    "resultados_lote", "_lote_env_total", "_lote_costo_total",
    "_lote_ganancia",  "_lote_modo",      "_lote_origen",
    "_lote_aprobado",  "_estado_apr",     "_lote_id_reg",
    "_modo_activo_prev",
]

def _resetear_lote():
    _KEYS_REPORTE = [
        "_reporte_resultados", "_reporte_modo", "_reporte_lote_id",
        "_reporte_costo", "_reporte_ganancia", "_reporte_env",
    ]
    for _k in _LOTE_KEYS + _KEYS_REPORTE:
        st.session_state.pop(_k, None)
    st.session_state.pop("_zip_listo",      None)
    st.session_state.pop("_zip_n_archivos", None)
    st.session_state["productos"]       = []
    st.session_state["confirm_limpiar"] = False
    st.session_state["_cat_preview"]    = None

def _resetear_home():
    _KEYS_REPORTE = [
        "_reporte_resultados", "_reporte_modo", "_reporte_lote_id",
        "_reporte_costo", "_reporte_ganancia", "_reporte_env",
    ]
    for _k in _LOTE_KEYS + _KEYS_REPORTE:
        st.session_state.pop(_k, None)
    st.session_state.pop("_zip_listo",      None)
    st.session_state.pop("_zip_n_archivos", None)
    st.session_state["productos"]             = []
    st.session_state["confirm_limpiar"]       = False
    st.session_state["_cat_preview"]          = None
    st.session_state["catalogo_df"]           = None
    _uploader_counter = st.session_state.get("_uploader_counter", 0)
    st.session_state["_uploader_counter"]     = _uploader_counter + 1
    st.session_state["courier_sel"]           = None
    st.session_state["lote_activo_marketing"] = None
    for _wk in ["lote_id", "ev_paso2_completado", "excel_urls_imagenes",
                "excel_bytes_cms", "copys_generados_ok", "_wizard_nav_css_v20"]:
        st.session_state.pop(_wk, None)

# ── Estados de navegación ─────────────────────────────────────────────────────
_nav_pipeline  = _pagina in ("paso1", "paso2", "paso3", "paso4")
_nav_historial = _pagina == "historial"
_nav_validar   = _pagina == "validar"
_nav_config    = _pagina == "config"

# Indicador de lote activo en el pipeline
_tiene_lote_nav = bool(st.session_state.get("resultados_lote"))
_dot_pipeline   = '<span class="ada-nav-dot"></span>' if _tiene_lote_nav else ''

_cls_pipeline  = "ada-nav-item active" if _nav_pipeline  else "ada-nav-item"
_cls_historial = "ada-nav-item active" if _nav_historial else "ada-nav-item"
_cls_validar   = "ada-nav-item active" if _nav_validar   else "ada-nav-item"
_cls_config    = "ada-nav-item active" if _nav_config    else "ada-nav-item"

st.markdown(f"""
<style>
.ada-nav-bar {{
    display: flex; align-items: stretch; justify-content: space-between;
    background: #080e1a; border: 1px solid #141e30;
    border-radius: 12px; padding: 4px; margin-bottom: 0;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}}
.ada-nav-item {{
    flex: 1; display: flex; flex-direction: column;
    align-items: center; justify-content: center; gap: 4px;
    padding: 12px 4px; border-radius: 8px;
    cursor: pointer; position: relative; transition: all 0.3s ease;
}}
.ada-nav-item:hover {{ background: rgba(255,255,255,0.02); }}
.ada-nav-item.active {{
    background: linear-gradient(180deg, transparent 0%, rgba(184,150,62,0.08) 100%);
}}
.ada-nav-item.active::after {{
    content: ''; position: absolute;
    bottom: -4px; left: 20%; right: 20%; height: 3px;
    background: #B8963E; border-radius: 4px 4px 0 0;
    box-shadow: 0 -2px 12px rgba(184,150,62,0.6);
}}
.ada-nav-icon {{
    font-size: 1.3rem; line-height: 1;
    filter: grayscale(100%) opacity(0.5);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}}
.ada-nav-item.active .ada-nav-icon {{
    filter: grayscale(0%) opacity(1) drop-shadow(0 4px 8px rgba(184,150,62,0.4));
    transform: translateY(-2px) scale(1.05);
}}
.ada-nav-label {{
    font-family: 'DM Mono', monospace; font-size: 0.62rem;
    letter-spacing: 2px; text-transform: uppercase; font-weight: 700;
    color: #64748b; transition: color 0.3s;
}}
.ada-nav-item.active .ada-nav-label {{ color: #B8963E; }}
.ada-nav-sublabel {{
    font-size: 0.50rem; letter-spacing: 1px; color: #4a5568;
    font-family: 'DM Mono', monospace; white-space: nowrap; transition: color 0.3s;
}}
.ada-nav-item.active .ada-nav-sublabel {{ color: rgba(184,150,62,0.7); }}
.ada-nav-sep {{
    width: 1px; margin: 10px 2px;
    background: linear-gradient(180deg, transparent, #1c2a42, transparent);
}}
.ada-nav-dot {{
    position: absolute; top: 12px; right: 20%;
    width: 6px; height: 6px; border-radius: 50%;
    background: #00E676;
    box-shadow: 0 0 8px #00E676, 0 0 16px rgba(0,230,118,0.4);
    animation: pdot 2s ease-in-out infinite;
}}
@keyframes pdot {{
    0%,100% {{ opacity:1; box-shadow: 0 0 6px #00E676; }}
    50%      {{ opacity:0.4; box-shadow: 0 0 12px #00E676; }}
}}
div[data-testid="stHorizontalBlock"]:has(button[key^="nav_btn_"]) {{
    margin-top: -78px !important; position: relative !important; z-index: 100 !important;
}}
div[data-testid="stHorizontalBlock"]:has(button[key^="nav_btn_"]) button {{
    opacity: 0 !important; background: transparent !important;
    border: none !important; color: transparent !important;
    box-shadow: none !important; height: 78px !important; padding: 0 !important;
}}
</style>

<div class="ada-nav-bar">
  <div class="ada-nav-item">
    <span class="ada-nav-icon">🏠</span>
    <span class="ada-nav-label">INICIO</span>
    <span class="ada-nav-sublabel">Courier</span>
  </div>
  <div class="ada-nav-sep"></div>
  <div class="{_cls_pipeline}">{_dot_pipeline}
    <span class="ada-nav-icon">🔄</span>
    <span class="ada-nav-label">PIPELINE</span>
    <span class="ada-nav-sublabel">Pasos 1 · 2 · 3 · 4</span>
  </div>
  <div class="ada-nav-sep"></div>
  <div class="{_cls_historial}">
    <span class="ada-nav-icon">📊</span>
    <span class="ada-nav-label">HISTORIAL</span>
    <span class="ada-nav-sublabel">Lotes · Métricas</span>
  </div>
  <div class="ada-nav-sep"></div>
  <div class="{_cls_validar}">
    <span class="ada-nav-icon">🔍</span>
    <span class="ada-nav-label">VALIDAR</span>
    <span class="ada-nav-sublabel">Competencia ML</span>
  </div>
  <div class="ada-nav-sep"></div>
  <div class="{_cls_config}">
    <span class="ada-nav-icon">⚙️</span>
    <span class="ada-nav-label">CONFIG</span>
    <span class="ada-nav-sublabel">Parámetros</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Botones reales del router (opacity 0, superpuestos) ───────────────────────
_nc0, _nc1, _nc2, _nc3, _nc4 = st.columns(5)

with _nc0:
    if st.button("INICIO", key="nav_btn_inicio", use_container_width=True):
        st.session_state["pagina_activa"] = "paso1"
        _resetear_home()
        st.rerun()
with _nc1:
    if st.button("PIPELINE", key="nav_btn_pipeline", use_container_width=True):
        st.session_state["pagina_activa"] = "paso1"
        st.rerun()
with _nc2:
    if st.button("HISTORIAL", key="nav_btn_historial", use_container_width=True):
        st.session_state["pagina_activa"] = "historial"
        st.rerun()
with _nc3:
    if st.button("VALIDAR", key="nav_btn_val", use_container_width=True):
        st.session_state["pagina_activa"] = "validar"
        st.rerun()
with _nc4:
    if st.button("CONFIG", key="nav_btn_config", use_container_width=True):
        st.session_state["pagina_activa"] = "config"
        st.rerun()

st.markdown('<div style="margin-bottom:1.4rem"></div>', unsafe_allow_html=True)

# ── Overlay de carga ──────────────────────────────────────────────────────────
st.markdown("""
<div id="ada-page-loader" class="ada-page-loading ada-loaded">
    <div class="ada-loader-spinner"></div>
</div>
<script>
(function() {
    function attachNavListeners() {
        var btns = document.querySelectorAll('button');
        btns.forEach(function(btn) {
            var txt = (btn.textContent || '').trim().toUpperCase();
            var labels = ['INICIO','PIPELINE','HISTORIAL','VALIDAR','CONFIG'];
            if (labels.indexOf(txt) !== -1 && !btn._adaNavBound) {
                btn._adaNavBound = true;
                btn.addEventListener('click', function() {
                    var loader = document.getElementById('ada-page-loader');
                    if (loader) {
                        loader.classList.remove('ada-loaded');
                        loader.classList.add('ada-showing');
                        setTimeout(function() {
                            loader.classList.add('ada-loaded');
                            loader.classList.remove('ada-showing');
                        }, 4000);
                    }
                });
            }
        });
    }
    attachNavListeners();
    var observer = new MutationObserver(function() { attachNavListeners(); });
    observer.observe(document.body, { childList: true, subtree: true });
})();
</script>
""", unsafe_allow_html=True)

# ── Contexto condicional ──────────────────────────────────────────────────────
@_contextlib.contextmanager
def _pagina_ctx(nombre):
    if st.session_state["pagina_activa"] == nombre:
        yield True
    else:
        with st.empty():
            yield False

class _ConditionalContainer:
    def __init__(self, pagina):
        self._pagina    = pagina
        self._active    = st.session_state["pagina_activa"] == pagina
        self._container = st.container() if self._active else None
    def __enter__(self):
        if self._active:
            return self._container.__enter__()
        return self
    def __exit__(self, *args):
        if self._active and self._container:
            return self._container.__exit__(*args)
    def __bool__(self):
        return self._active

# ── Contenedores pipeline wizard ─────────────────────────────────────────────
tab_paso1 = _ConditionalContainer("paso1")
tab_paso2 = _ConditionalContainer("paso2")
tab_paso3 = _ConditionalContainer("paso3")
tab_paso4 = _ConditionalContainer("paso4")

# ── Contenedores utilidades ───────────────────────────────────────────────────
tab_historial = _ConditionalContainer("historial")
tab_validar   = _ConditionalContainer("validar")
tab_config    = _ConditionalContainer("config")

# ── Contenedores legacy (fallback silencioso, sin botón en nav) ───────────────
tab_lote      = _ConditionalContainer("lote")
tab_pub       = _ConditionalContainer("publicaciones")
tab_estudio   = _ConditionalContainer("estudio_visual")

# ══════════════════════════════════════════════════════════════════════════════
# DESPACHO DE PÁGINAS
# ══════════════════════════════════════════════════════════════════════════════
_pagina_activa = st.session_state.get("pagina_activa", "paso1")

def _exec_subpagina(nombre_archivo: str):
    _pages_dir = _os.path.join(_ROUTER_ROOT, "pages")
    if _ROUTER_ROOT not in _sys.path:
        _sys.path.insert(0, _ROUTER_ROOT)
    if _pages_dir not in _sys.path:
        _sys.path.insert(0, _pages_dir)
    if _MODULES_DIR not in _sys.path:
        _sys.path.insert(0, _MODULES_DIR)
    _os.chdir(_ROUTER_ROOT)
    _abs = _os.path.join(_pages_dir, nombre_archivo)
    exec(open(_abs, encoding="utf-8").read(), globals())

# ── Pipeline wizard ───────────────────────────────────────────────────────────
if _pagina_activa == "paso1":
    with tab_paso1:
        _exec_subpagina("_paso1_lote.py")

elif _pagina_activa == "paso2":
    with tab_paso2:
        _exec_subpagina("_paso2_estudio.py")

elif _pagina_activa == "paso3":
    with tab_paso3:
        _exec_subpagina("_paso3_exportacion.py")

elif _pagina_activa == "paso4":
    with tab_paso4:
        _exec_subpagina("_paso4_publicaciones.py")

# ── Utilidades ────────────────────────────────────────────────────────────────
elif _pagina_activa == "historial":
    with tab_historial:
        _exec_subpagina("_historial.py")

elif _pagina_activa == "validar":
    with tab_validar:
        _exec_subpagina("_validar.py")

elif _pagina_activa == "config":
    with tab_config:
        _exec_subpagina("_config_master.py")

# ── Legacy fallback (sin botón en nav, accesibles desde botones internos) ─────
elif _pagina_activa == "lote":
    with tab_lote:
        _exec_subpagina("_lote.py")

elif _pagina_activa == "publicaciones":
    with tab_pub:
        _exec_subpagina("_publicaciones.py")

elif _pagina_activa == "estudio_visual":
    with tab_estudio:
        _exec_subpagina("_estudio_visual.py")

else:
    st.session_state["pagina_activa"] = "paso1"
    st.rerun()
