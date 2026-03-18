# ── Imports necesarios para el router ─────────────────────────
import streamlit as st
import contextlib as _contextlib
import sys as _sys, os as _os, builtins as _builtins

# ── Garantizar sys.path en este nivel de exec() ───────────────────────────────
# app.py inyecta _ADALIMPORT_ROOT en builtins antes de cualquier exec().
# Re-aplicamos aquí para que los exec() que lanza _router también lo hereden.
_ROUTER_ROOT = getattr(_builtins, "_ADALIMPORT_ROOT", None) or _os.getcwd()
if _ROUTER_ROOT not in _sys.path:
    _sys.path.insert(0, _ROUTER_ROOT)
_os.chdir(_ROUTER_ROOT)

# ══════════════════════════════════════════════════════════════════════════════
# ROUTER CUSTOM — Navegación 100% controlada desde Python via session_state
# Sin st.tabs() nativas — renderizado condicional por página activa.
# páginas: "lote" | "publicaciones" | "validar" | "config" | "historial"
# ══════════════════════════════════════════════════════════════════════════════
if "pagina_activa" not in st.session_state:
    st.session_state["pagina_activa"] = "lote"

_pagina = st.session_state["pagina_activa"]


# ── Claves de sesión del lote activo — scope GLOBAL ──────────────────────────
# MOVIDO ARRIBA: Para que los botones las puedan usar sin error de "not defined"
_LOTE_KEYS = [
    "resultados_lote", "_lote_env_total", "_lote_costo_total",
    "_lote_ganancia",  "_lote_modo",      "_lote_origen",
    "_lote_aprobado",  "_estado_apr",     "_lote_id_reg",
    "_modo_activo_prev",
]

def _resetear_lote():
    """Limpia todas las variables del lote activo.
    Conserva courier_sel para volver al analizador del mismo courier."""
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
    """Reset PROFUNDO: limpia TODO y vuelve a la pantalla de bienvenida."""
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
    # ⚡ CLAVE: courier_sel = None → Home muestra tarjetas de selección
    st.session_state["courier_sel"]           = None
    st.session_state["lote_activo_marketing"] = None


# ── Barra de navegación custom ────────────────────────────────────────────────
_nav_lote     = _pagina == "lote"
_nav_pub      = _pagina == "publicaciones"
_nav_val      = _pagina == "validar"
_nav_config   = _pagina == "config"
_nav_historial= _pagina == "historial"
_nav_estudio  = _pagina == "estudio_visual"

# Indicadores de estado para las pestañas
_tiene_lote_nav = bool(st.session_state.get("resultados_lote"))
_tiene_pub_nav  = bool(st.session_state.get("lote_activo_marketing"))

_dot_lote_html = '<span class="ada-nav-dot"></span>' if _tiene_lote_nav else ''
_dot_pub_html  = '<span class="ada-nav-dot"></span>' if _tiene_pub_nav  else ''

_cls_lote     = "ada-nav-item active" if _nav_lote      else "ada-nav-item"
_cls_pub      = "ada-nav-item active" if _nav_pub       else "ada-nav-item"
_cls_val      = "ada-nav-item active" if _nav_val       else "ada-nav-item"
_cls_config   = "ada-nav-item active" if _nav_config    else "ada-nav-item"
_cls_historial= "ada-nav-item active" if _nav_historial else "ada-nav-item"
_cls_estudio  = "ada-nav-item active" if _nav_estudio  else "ada-nav-item"

st.markdown(f"""
<style>
/* ── Nav Bar Principal Premium ───────────────────────────────────────────── */
.ada-nav-bar {{
    display: flex; align-items: stretch; justify-content: space-between;
    background: #080e1a;
    border: 1px solid #141e30;
    border-radius: 12px; 
    padding: 4px; 
    margin-bottom: 0;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}}
.ada-nav-item {{
    flex: 1; display: flex; flex-direction: column;
    align-items: center; justify-content: center; gap: 4px;
    padding: 12px 4px; border-radius: 8px;
    cursor: pointer; position: relative;
    transition: all 0.3s ease;
}}
.ada-nav-item:hover {{
    background: rgba(255,255,255,0.02);
}}
/* Estilo del ítem ACTIVO */
.ada-nav-item.active {{
    background: linear-gradient(180deg, transparent 0%, rgba(184,150,62,0.08) 100%);
}}
/* Línea dorada luminosa en la base del activo */
.ada-nav-item.active::after {{
    content: ''; position: absolute;
    bottom: -4px; left: 20%; right: 20%; height: 3px;
    background: #B8963E; border-radius: 4px 4px 0 0;
    box-shadow: 0 -2px 12px rgba(184,150,62,0.6);
}}
/* Iconos: escala de grises inactivos, color vibrante activos */
.ada-nav-icon {{
    font-size: 1.3rem; line-height: 1;
    filter: grayscale(100%) opacity(0.5);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}}
.ada-nav-item.active .ada-nav-icon {{
    filter: grayscale(0%) opacity(1) drop-shadow(0 4px 8px rgba(184,150,62,0.4));
    transform: translateY(-2px) scale(1.05);
}}
/* Textos */
.ada-nav-label {{
    font-family: 'DM Mono', monospace; font-size: 0.62rem;
    letter-spacing: 2px; text-transform: uppercase; font-weight: 700;
    color: #64748b; transition: color 0.3s;
}}
.ada-nav-item.active .ada-nav-label {{
    color: #B8963E;
}}
.ada-nav-sublabel {{
    font-size: 0.50rem; letter-spacing: 1px;
    color: #4a5568; font-family: 'DM Mono', monospace;
    white-space: nowrap; transition: color 0.3s;
}}
.ada-nav-item.active .ada-nav-sublabel {{
    color: rgba(184,150,62,0.7);
}}
/* Separador sutil entre botones */
.ada-nav-sep {{
    width: 1px; margin: 10px 2px;
    background: linear-gradient(180deg, transparent, #1c2a42, transparent);
}}

/* Indicador Verde Neón animado para alertas */
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

/* ── FIX: Invisibilidad de botones reales de Streamlit ───────────────────── */
div[data-testid="stHorizontalBlock"]:has(button[key^="nav_btn_"]) {{
    margin-top: -78px !important; position: relative !important; z-index: 100 !important;
}}
div[data-testid="stHorizontalBlock"]:has(button[key^="nav_btn_"]) button {{
    opacity: 0 !important;
    background: transparent !important;
    border: none !important;
    color: transparent !important;
    box-shadow: none !important;
    height: 78px !important;
    padding: 0 !important;
}}
</style>

<div class="ada-nav-bar">
  <div class="ada-nav-item">
    <span class="ada-nav-icon">🏠</span>
    <span class="ada-nav-label">INICIO</span>
    <span class="ada-nav-sublabel">Courier</span>
  </div>
  <div class="ada-nav-sep"></div>
  <div class="{_cls_lote}">{_dot_lote_html}
    <span class="ada-nav-icon">📦</span>
    <span class="ada-nav-label">LOTE</span>
    <span class="ada-nav-sublabel">Análisis · Costos</span>
  </div>
  <div class="ada-nav-sep"></div>
  <div class="{_cls_pub}">{_dot_pub_html}
    <span class="ada-nav-icon">🚀</span>
    <span class="ada-nav-label">PUBLICACIÓN</span>
    <span class="ada-nav-sublabel">Copys · ZIP</span>
  </div>
  <div class="ada-nav-sep"></div>
  <div class="{_cls_val}">
    <span class="ada-nav-icon">🔍</span>
    <span class="ada-nav-label">VALIDAR</span>
    <span class="ada-nav-sublabel">Competencia ML</span>
  </div>
  <div class="ada-nav-sep"></div>
  <div class="{_cls_historial}">
    <span class="ada-nav-icon">📊</span>
    <span class="ada-nav-label">HISTORIAL</span>
    <span class="ada-nav-sublabel">Métricas BD</span>
  </div>
  <div class="ada-nav-sep"></div>
  <div class="{_cls_estudio}">
    <span class="ada-nav-icon">🎨</span>
    <span class="ada-nav-label">ESTUDIO</span>
    <span class="ada-nav-sublabel">Imágenes IA</span>
  </div>
  <div class="ada-nav-sep"></div>
  <div class="{_cls_config}">
    <span class="ada-nav-icon">⚙️</span>
    <span class="ada-nav-label">CONFIG</span>
    <span class="ada-nav-sublabel">Parámetros</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Botones reales del router (opacity 0 absoluto, superpuestos) ──────────────
_nc0, _nc1, _nc2, _nc3, _nc4, _nc5, _nc6 = st.columns(7)

with _nc0:
    if st.button("INICIO", key="nav_btn_inicio", use_container_width=True):
        st.session_state["pagina_activa"] = "lote"
        _resetear_home()
        st.rerun()
with _nc1:
    if st.button("LOTE", key="nav_btn_lote", use_container_width=True):
        st.session_state["pagina_activa"] = "lote"
        st.rerun()
with _nc2:
    if st.button("PUBLICACIONES", key="nav_btn_pub", use_container_width=True):
        st.session_state["pagina_activa"] = "publicaciones"
        st.rerun()
with _nc3:
    if st.button("VALIDAR", key="nav_btn_val", use_container_width=True):
        st.session_state["pagina_activa"] = "validar"
        st.rerun()
with _nc4:
    if st.button("HISTORIAL", key="nav_btn_historial", use_container_width=True):
        st.session_state["pagina_activa"] = "historial"
        st.rerun()
with _nc5:
    if st.button("ESTUDIO", key="nav_btn_estudio", use_container_width=True):
        st.session_state["pagina_activa"] = "estudio_visual"
        st.rerun()
with _nc6:
    if st.button("CONFIG", key="nav_btn_config", use_container_width=True):
        st.session_state["pagina_activa"] = "config"
        st.rerun()

st.markdown('<div style="margin-bottom:1.4rem"></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# OVERLAY DE CARGA PREMIUM — Transición suave entre páginas
# Estrategia SEGURA: overlay inicia OCULTO (opacity:0, visibility:hidden).
# Solo se muestra al hacer clic en nav via JS. CSS animation con duración
# finita garantiza que NUNCA se quede bloqueando la pantalla.
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div id="ada-page-loader" class="ada-page-loading ada-loaded">
    <div class="ada-loader-spinner"></div>
</div>

<script>
(function() {
    // Interceptar clicks en la zona de botones reales de nav
    // Usamos MutationObserver porque Streamlit puede re-renderizar el DOM
    function attachNavListeners() {
        var btns = document.querySelectorAll('button');
        btns.forEach(function(btn) {
            // Detectar botones de nav por su texto o key
            var txt = (btn.textContent || '').trim().toUpperCase();
            var navLabels = ['INICIO','LOTE','PUBLICACIONES','VALIDAR','HISTORIAL','ESTUDIO','CONFIG'];
            if (navLabels.indexOf(txt) !== -1 && !btn._adaNavBound) {
                btn._adaNavBound = true;
                btn.addEventListener('click', function() {
                    var loader = document.getElementById('ada-page-loader');
                    if (loader) {
                        loader.classList.remove('ada-loaded');
                        loader.classList.add('ada-showing');
                        // Fallback seguro: ocultar después de 4s por si Streamlit
                        // no completa el re-render (evita bloqueo permanente)
                        setTimeout(function() {
                            loader.classList.add('ada-loaded');
                            loader.classList.remove('ada-showing');
                        }, 4000);
                    }
                });
            }
        });
    }

    // Ejecutar ahora y observar cambios futuros del DOM
    attachNavListeners();
    var observer = new MutationObserver(function() { attachNavListeners(); });
    observer.observe(document.body, { childList: true, subtree: true });
})();
</script>
""", unsafe_allow_html=True)


# ── Context manager condicional ───────────────────────────────────────────────
@_contextlib.contextmanager
def _pagina_ctx(nombre):
    """Renderiza el bloque solo si la página activa coincide."""
    if st.session_state["pagina_activa"] == nombre:
        yield True
    else:
        with st.empty():
            yield False

class _ConditionalContainer:
    """Reemplaza 'with tabX:' — solo renderiza si la página coincide."""
    def __init__(self, pagina):
        self._pagina  = pagina
        self._active  = st.session_state["pagina_activa"] == pagina
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

tab1 = _ConditionalContainer("lote")
tab2 = _ConditionalContainer("validar")
tab3 = _ConditionalContainer("publicaciones")
tab4 = _ConditionalContainer("config")
tab5 = _ConditionalContainer("historial")
tab6 = _ConditionalContainer("estudio_visual")

# ══════════════════════════════════════════════════════════════════════════════
# DESPACHO DE PÁGINAS — rutas absolutas para evitar problemas de cwd en Windows
# ══════════════════════════════════════════════════════════════════════════════
_pagina_activa = st.session_state.get("pagina_activa", "lote")

def _exec_subpagina(nombre_archivo: str):
    """
    Ejecuta una subpágina usando ruta ABSOLUTA.
    Garantiza sys.path y cwd antes de cada exec() para aislar problemas
    de contexto en cadenas de exec() anidados en Windows.
    """
    _pages_dir = _os.path.join(_ROUTER_ROOT, "pages")
    if _ROUTER_ROOT not in _sys.path:
        _sys.path.insert(0, _ROUTER_ROOT)
    # Agregar pages/ al sys.path para que imports entre páginas funcionen
    # Esto permite: from _toast_system import toast, etc.
    if _pages_dir not in _sys.path:
        _sys.path.insert(0, _pages_dir)
    _os.chdir(_ROUTER_ROOT)
    _abs = _os.path.join(_pages_dir, nombre_archivo)
    exec(open(_abs, encoding="utf-8").read(), globals())

if _pagina_activa == "lote":
    with tab1:
        _exec_subpagina("_lote.py")
elif _pagina_activa == "validar":
    with tab2:
        _exec_subpagina("_validar.py")
elif _pagina_activa == "publicaciones":
    with tab3:
        _exec_subpagina("_publicaciones.py")
elif _pagina_activa == "config":
    with tab4:
        _exec_subpagina("_config_master.py")
elif _pagina_activa == "historial":
    with tab5:
        _exec_subpagina("_historial.py")
elif _pagina_activa == "estudio_visual":
    with tab6:
        _exec_subpagina("_estudio_visual.py")
