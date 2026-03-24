# ══════════════════════════════════════════════════════════════════════════════
# ADALIMPORT · modules/_wizard_nav.py  ·  v2.0  (100% Streamlit nativo)
# ──────────────────────────────────────────────────────────────────────────────
# Barra de progreso del pipeline wizard de 4 pasos.
#
# v2.0 — CAMBIO TOTAL DE ARQUITECTURA:
#   Elimina completamente unsafe_allow_html para la barra visual.
#   Causa: exec() anidado del router no propagaba el contexto de unsafe_allow_html.
#   Solución: barra construida 100% con st.columns + st.button nativos de Streamlit.
#   El CSS de estilo sí se inyecta via unsafe_allow_html (solo CSS, no estructura).
#
# DISEÑO:
#   · Paso ACTIVO     → st.button type="primary"  (dorado/primary del design system)
#   · Paso COMPLETADO → st.button con ✓ prefix,   habilitado, navigable
#   · Paso DISPONIBLE → st.button con ○ prefix,   habilitado, navigable
#   · Paso BLOQUEADO  → st.button con 🔒 prefix,  disabled=True
#
# Paleta: Navy (#05090F) · Oro (#B8963E) · Verde Neón (#00E676)
# ══════════════════════════════════════════════════════════════════════════════

import sys
import os
import builtins as _builtins

_ROOT = getattr(_builtins, "_ADALIMPORT_ROOT", None) or os.getcwd()
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import streamlit as st
from modules._estado_pipeline import paso_habilitado, paso_completado, ESTADO_PASO

_CSS_KEY = "_wizard_nav_css_v20"


def _inyectar_css_wizard() -> None:
    """Inyecta CSS de apoyo — solo estilos, no estructura HTML."""
    if st.session_state.get(_CSS_KEY):
        return

    st.markdown("""
<style>
/* ══════════════════════════════════════════════════════════════════════════
   WIZARD NAV v2.0 — Estilos para botones nativos de Streamlit
   La barra usa st.columns + st.button, no HTML personalizado.
══════════════════════════════════════════════════════════════════════════ */

/* Contenedor de los 4 botones del wizard — fondo oscuro unificado */
div[data-testid="stHorizontalBlock"]:has(button[key^="wiz2_"]) {
    background: #080e1a !important;
    border: 1px solid #141e30 !important;
    border-radius: 12px !important;
    padding: 6px !important;
    gap: 6px !important;
    margin-bottom: 4px !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important;
}

/* ── Botón ACTIVO (primary) — Verde Neón ───────────────────────────────── */
div[data-testid="stHorizontalBlock"]:has(button[key^="wiz2_"]) button[key$="_activo"] {
    background: rgba(0,230,118,0.12) !important;
    border: 1px solid rgba(0,230,118,0.5) !important;
    color: #00E676 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.62rem !important;
    letter-spacing: 1.5px !important;
    font-weight: 700 !important;
    box-shadow: 0 0 12px rgba(0,230,118,0.15) !important;
}

/* ── Botón COMPLETADO — Oro ────────────────────────────────────────────── */
div[data-testid="stHorizontalBlock"]:has(button[key^="wiz2_"]) button[key$="_completado"] {
    background: rgba(184,150,62,0.12) !important;
    border: 1px solid rgba(184,150,62,0.45) !important;
    color: #B8963E !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.62rem !important;
    letter-spacing: 1.5px !important;
    font-weight: 700 !important;
}
div[data-testid="stHorizontalBlock"]:has(button[key^="wiz2_"]) button[key$="_completado"]:hover {
    background: rgba(184,150,62,0.22) !important;
    box-shadow: 0 0 12px rgba(184,150,62,0.3) !important;
}

/* ── Botón DISPONIBLE — Gris claro ─────────────────────────────────────── */
div[data-testid="stHorizontalBlock"]:has(button[key^="wiz2_"]) button[key$="_disponible"] {
    background: transparent !important;
    border: 1px solid rgba(100,116,139,0.3) !important;
    color: #64748b !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.62rem !important;
    letter-spacing: 1.5px !important;
}
div[data-testid="stHorizontalBlock"]:has(button[key^="wiz2_"]) button[key$="_disponible"]:hover {
    border-color: rgba(184,150,62,0.4) !important;
    color: #B8963E !important;
}

/* ── Botón BLOQUEADO — Muy oscuro, disabled ────────────────────────────── */
div[data-testid="stHorizontalBlock"]:has(button[key^="wiz2_"]) button[key$="_bloqueado"] {
    background: transparent !important;
    border: 1px solid rgba(30,40,55,0.6) !important;
    color: #2d3748 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.62rem !important;
    letter-spacing: 1.5px !important;
    opacity: 0.4 !important;
    cursor: not-allowed !important;
}

/* Separador debajo del wizard */
.wiz-hr {
    border: none;
    border-top: 1px solid #0e1826;
    margin: 4px 0 1.2rem 0;
}
</style>
""", unsafe_allow_html=True)
    st.session_state[_CSS_KEY] = True


def render_wizard_nav(paso_actual: int) -> None:
    """
    Renderiza la barra de progreso del pipeline de 4 pasos.

    v2.0: 100% st.columns + st.button nativos.
    El CSS de fondo y bordes se aplica via selectores CSS específicos por key.

    Cada botón tiene key con formato: wiz2_N_ESTADO
    donde N = número de paso (1-4) y ESTADO = activo|completado|disponible|bloqueado
    Esto permite que el CSS selectore por sufijo sea determinista.
    """
    _inyectar_css_wizard()

    # ── Estado de cada paso ───────────────────────────────────────────────────
    estados = {}
    for n in [1, 2, 3, 4]:
        completado = paso_completado(n)
        habilitado = paso_habilitado(n)
        es_activo  = (n == paso_actual)

        if es_activo:
            estado = "activo"
        elif completado:
            estado = "completado"
        elif habilitado:
            estado = "disponible"
        else:
            estado = "bloqueado"

        cfg = ESTADO_PASO[n]

        # Label del botón según estado
        if estado == "activo":
            label = f"◉ {cfg['emoji']} {cfg['label'].upper()}"
        elif estado == "completado":
            label = f"✓ {cfg['emoji']} {cfg['label'].upper()}"
        elif estado == "disponible":
            label = f"○ {cfg['emoji']} {cfg['label'].upper()}"
        else:
            label = f"🔒 {cfg['label'].upper()}"

        estados[n] = {
            "estado":  estado,
            "label":   label,
            "key":     f"wiz2_{n}_{estado}",
            "nav_key": f"paso{n}",
            "desc":    cfg["desc"],
        }

    # ── Renderizar 4 columnas con botones ─────────────────────────────────────
    _cols = st.columns(4, gap="small")

    for idx, n in enumerate([1, 2, 3, 4]):
        e = estados[n]
        with _cols[idx]:
            if e["estado"] == "bloqueado":
                st.button(
                    e["label"],
                    key=e["key"],
                    use_container_width=True,
                    disabled=True,
                    help=f"Paso {n} bloqueado — completa el paso anterior primero",
                )
            elif e["estado"] == "activo":
                # Activo — no navega, solo visual. Usamos disabled=True para
                # evitar que se presione, pero el CSS lo estiliza como activo.
                st.button(
                    e["label"],
                    key=e["key"],
                    use_container_width=True,
                    disabled=True,
                    help=f"Paso {n} activo — {e['desc']}",
                )
            else:
                # Completado o Disponible — navega al paso
                if st.button(
                    e["label"],
                    key=e["key"],
                    use_container_width=True,
                    help=f"Ir al Paso {n} — {e['desc']}",
                ):
                    st.session_state["pagina_activa"] = e["nav_key"]
                    st.rerun()

    # ── Separador ─────────────────────────────────────────────────────────────
    st.markdown(
        '<hr class="wiz-hr">',
        unsafe_allow_html=True,
    )


def guard_prerequisito(n: int, pagina_retroceso: str = "paso1") -> bool:
    """
    Verifica prerequisitos del paso N.
    Si no se cumplen: muestra banner + botón retroceso + llama st.stop().
    Retorna True si los prerequisitos están OK.
    """
    if paso_habilitado(n):
        return True

    cfg_prev   = ESTADO_PASO.get(n - 1, {})
    prev_label = cfg_prev.get("label", f"Paso {n - 1}")
    prev_emoji = cfg_prev.get("emoji", "")

    st.warning(
        f"⚠️ **Prerequisito pendiente** — Para acceder al Paso {n} "
        f"primero debes completar el **Paso {n-1} {prev_emoji} {prev_label}**."
    )

    if st.button(
        f"← Volver al Paso {n-1} — {prev_emoji} {prev_label}",
        key=f"guard_retroceso_paso{n}",
        type="primary",
    ):
        st.session_state["pagina_activa"] = pagina_retroceso
        st.rerun()

    st.stop()
    return False
