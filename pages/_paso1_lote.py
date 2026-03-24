import sys, os as _os, builtins as _builtins
# ── FIX sys.path: raíz + subcarpeta database/ ────────────────────────────────
_ROOT   = getattr(_builtins, "_ADALIMPORT_ROOT",   _os.getcwd())
_DB_DIR = getattr(_builtins, "_ADALIMPORT_DB_DIR",
                  _os.path.join(_ROOT, "database"))
for _p in (_DB_DIR, _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)
# ── Garantizar que modules/ esté en sys.path ──────────────────────────────────
_MODULES_DIR = _os.path.join(_ROOT, "modules")
if _MODULES_DIR not in sys.path:
    sys.path.insert(0, _MODULES_DIR)
# ─────────────────────────────────────────────────────────────────────────────
import streamlit as st

# ══════════════════════════════════════════════════════════════════════════════
#  ADALIMPORT — pages/_paso1_lote.py  ·  v1.2  (Paso 1 del Pipeline Wizard)
# ──────────────────────────────────────────────────────────────────────────────
#  v1.2 — SIMPLIFICACIÓN:
#    · Parche de rutas legacy ELIMINADO. Ya no es necesario porque
#      _lote_aprobacion.py v1.1 navega directamente a "paso2", "paso4" y "paso1".
#    · asegurar_lote_id() se mantiene como safety net para flujos externos
#      (carga desde historial, navegación directa a paso1).
#    · Código POST-RENDER simplificado a solo 2 safety nets de estado.
#
#  Responsabilidad única: orquestar los 3 submódulos del lote en orden,
#  precedidos por la barra wizard del pipeline.
#  Comunicación: EXCLUSIVAMENTE via st.session_state.
# ══════════════════════════════════════════════════════════════════════════════

# ── Importar componente wizard ────────────────────────────────────────────────
try:
    from modules._wizard_nav      import render_wizard_nav
    from modules._estado_pipeline import asegurar_lote_id
    _WIZARD_OK = True
except ImportError:
    _WIZARD_OK = False
    def render_wizard_nav(paso_actual: int) -> None:
        pass
    def asegurar_lote_id() -> bool:
        import streamlit as _st
        _id = _st.session_state.get("_lote_id_reg", "")
        if _id:
            _st.session_state["lote_id"] = _id
            return True
        return False

# ── Importar submódulos del lote ──────────────────────────────────────────────
from _lote_formulario  import render_formulario
from _lote_resultados  import render_resultados
from _lote_aprobacion  import render_aprobacion

# _resetear_home se hereda del contexto del router via exec() globals
_fn_reset = globals().get("_resetear_home", lambda: None)

# ── Barra wizard ──────────────────────────────────────────────────────────────
render_wizard_nav(paso_actual=1)

# ── 1. Formulario de entrada ──────────────────────────────────────────────────
render_formulario()

# ── 2. Análisis (solo si hay productos) ──────────────────────────────────────
if st.session_state.get("productos"):
    render_resultados()

# ── 3. Aprobación (solo si hay resultados calculados) ────────────────────────
if st.session_state.get("resultados_lote"):
    render_aprobacion(_fn_reset)

# ══════════════════════════════════════════════════════════════════════════════
# POST-RENDER: Safety nets de coherencia de estado
# En el flujo normal (aprobacion v1.1) estos bloques no hacen nada.
# Solo actúan si el usuario llega al Paso 1 desde un flujo externo.
# ══════════════════════════════════════════════════════════════════════════════

# Safety net 1: sincronizar lote_id si llegó por ruta externa sin clave canónica
asegurar_lote_id()

# Safety net 2: garantizar _lote_modo si solo existe dentro de lote_activo_marketing
if not st.session_state.get("_lote_modo"):
    _mkt = st.session_state.get("lote_activo_marketing", {})
    if _mkt.get("modo"):
        st.session_state["_lote_modo"] = _mkt["modo"]

# ── Estado vacío ──────────────────────────────────────────────────────────────
if not st.session_state.get("productos") and not st.session_state.get("resultados_lote"):
    st.markdown("""
    <div style="
        background: rgba(184,150,62,0.04);
        border: 1px solid rgba(184,150,62,0.15);
        border-left: 3px solid rgba(184,150,62,0.4);
        border-radius: 10px;
        padding: 1rem 1.4rem;
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        color: #94a3b8;
        margin-top: 1rem;
    ">
        ℹ &nbsp; Agrega productos al lote para comenzar el análisis.
    </div>
    """, unsafe_allow_html=True)
