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
#  ADALIMPORT — pages/_paso1_lote.py  (Paso 1 del Pipeline Wizard)
#  Versión: refactor de _lote.py con barra de progreso wizard integrada.
#
#  Responsabilidad única: orquestar los 3 submódulos del lote en orden,
#  precedidos por la barra wizard del pipeline.
#
#  Submódulos (sin cambios):
#    · _lote_formulario.py  → modo/origen, carga catálogo, formulario manual
#    · _lote_resultados.py  → análisis, KPIs, tabla, decisión maestra
#    · _lote_aprobacion.py  → aprobación, guardado BD, PDF, navegación
#
#  CAMBIOS respecto a _lote.py:
#    1. Agrega render_wizard_nav(paso_actual=1) al inicio del contenido.
#    2. Los botones de navegación en _lote_aprobacion usan rutas del wizard:
#       "paso2" (antes "estudio_visual") y "paso4" (antes "publicaciones").
#       ⚠️  Esto se controla desde _lote_aprobacion.py mediante la clave
#       "pagina_activa". El presente archivo NO modifica _lote_aprobacion.py.
#       Parche de rutas aplicado debajo via session_state post-render.
#    3. Al aprobar, deposita "lote_id" en session_state (clave del contrato).
#
#  Reglas de negocio: calculadora_importacion.py — NO SE MODIFICA.
#  Comunicación: EXCLUSIVAMENTE via st.session_state.
# ══════════════════════════════════════════════════════════════════════════════

# ── Importar componente wizard ────────────────────────────────────────────────
# Paso 1 no tiene prerequisitos → no necesita guard_prerequisito()
try:
    from modules._wizard_nav import render_wizard_nav
    _WIZARD_OK = True
except ImportError:
    _WIZARD_OK = False
    def render_wizard_nav(paso_actual: int) -> None:
        pass  # fallback silencioso si modules/ no está instalado aún

# ── Importar submódulos del lote (igual que _lote.py) ────────────────────────
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

# ── Parche de rutas wizard post-aprobación ────────────────────────────────────
# _lote_aprobacion.py navega a "publicaciones" y "estudio_visual" (rutas legacy).
# Aquí interceptamos esas rutas y las redirigimos a las rutas del pipeline wizard.
# Esto garantiza compatibilidad sin modificar _lote_aprobacion.py.
_pagina_destino = st.session_state.get("pagina_activa", "")
if _pagina_destino == "estudio_visual":
    st.session_state["pagina_activa"] = "paso2"
    st.rerun()
elif _pagina_destino == "publicaciones":
    st.session_state["pagina_activa"] = "paso4"
    st.rerun()

# ── Depositar "lote_id" en session_state (clave del contrato del pipeline) ───
# _lote_aprobacion.py guarda el ID en "_lote_id_reg". Lo copiamos a "lote_id"
# para que paso_habilitado(2), (3) y (4) funcionen correctamente.
if st.session_state.get("_lote_id_reg") and not st.session_state.get("lote_id"):
    st.session_state["lote_id"] = st.session_state["_lote_id_reg"]

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
