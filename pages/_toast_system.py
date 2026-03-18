import sys, os as _os, builtins as _builtins
# ── FIX sys.path: raíz + subcarpeta database/ ────────────────────────────────
_ROOT   = getattr(_builtins, "_ADALIMPORT_ROOT",   _os.getcwd())
_DB_DIR = getattr(_builtins, "_ADALIMPORT_DB_DIR",
                  _os.path.join(_ROOT, "database"))
for _p in (_DB_DIR, _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)
# ─────────────────────────────────────────────────────────────────────────────
import streamlit as st

# ══════════════════════════════════════════════════════════════════════════════
#  ADALIMPORT — Toast Notification System
#  Helper reutilizable · Esquina inferior derecha · Auto-dismiss 3s
#  Tipos: "success" | "error" | "warning" | "info"
#  Uso:
#      from _toast_system import toast
#      toast("Lote guardado correctamente", "success")
#      toast("Error al conectar con la BD", "error")
#      toast("El lote está bajo el mínimo", "warning")
#      toast("Recalculando con courier alternativo", "info")
# ══════════════════════════════════════════════════════════════════════════════

# Mapa de estilos por tipo — paleta Navy/Oro/Neón del Design System
_TOAST_CONFIG = {
    "success": {
        "border":     "#00E676",
        "bg":         "rgba(0, 230, 118, 0.07)",
        "icon":       "✅",
        "label":      "ÉXITO",
        "label_color": "#00E676",
    },
    "error": {
        "border":     "#f87171",
        "bg":         "rgba(248, 113, 113, 0.07)",
        "icon":       "✖",
        "label":      "ERROR",
        "label_color": "#f87171",
    },
    "warning": {
        "border":     "#B8963E",
        "bg":         "rgba(184, 150, 62, 0.08)",
        "icon":       "⚠",
        "label":      "AVISO",
        "label_color": "#B8963E",
    },
    "info": {
        "border":     "#60a5fa",
        "bg":         "rgba(96, 165, 250, 0.07)",
        "icon":       "ℹ",
        "label":      "INFO",
        "label_color": "#60a5fa",
    },
}


def toast(mensaje: str, tipo: str = "info") -> None:
    """
    Muestra una notificación tipo toast en la esquina inferior derecha.

    - No desplaza el contenido de la página (position: fixed).
    - Se auto-descarta a los 3.5 segundos via animación CSS.
    - Tipografía DM Mono / Inter, paleta Navy/Oro/Neón.
    - Sin texto negro sobre fondo oscuro.

    Args:
        mensaje: Texto de la notificación.
        tipo:    "success" | "error" | "warning" | "info"
    """
    cfg = _TOAST_CONFIG.get(tipo, _TOAST_CONFIG["info"])

    # ID único para no colisionar si se llama varias veces en el mismo ciclo
    uid = f"ada_toast_{tipo}_{abs(hash(mensaje)) % 100000}"

    html = f"""
<style>
/* ── Toast container ─────────────────────────────────────────────────── */
#{uid} {{
    position: fixed;
    bottom: 28px;
    right: 28px;
    z-index: 99999;
    min-width: 280px;
    max-width: 420px;
    background: {cfg['bg']};
    border: 1px solid {cfg['border']};
    border-left: 3px solid {cfg['border']};
    border-radius: 10px;
    padding: 12px 16px 12px 14px;
    display: flex;
    align-items: flex-start;
    gap: 10px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.45), 0 0 16px {cfg['border']}22;
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    /* Animación: slide-in → pausa → fade-out */
    animation: ada-toast-life 3.5s cubic-bezier(0.4, 0, 0.2, 1) forwards;
    pointer-events: none;
}}

/* Ícono */
#{uid} .ada-toast-icon {{
    font-size: 1.05rem;
    line-height: 1.4;
    flex-shrink: 0;
    color: {cfg['border']};
}}

/* Contenido texto */
#{uid} .ada-toast-body {{
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
}}

#{uid} .ada-toast-label {{
    font-family: 'DM Mono', monospace;
    font-size: 0.58rem;
    font-weight: 500;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: {cfg['label_color']};
    line-height: 1;
}}

#{uid} .ada-toast-msg {{
    font-family: 'Inter', sans-serif;
    font-size: 0.82rem;
    font-weight: 400;
    color: #e2e8f0;
    line-height: 1.45;
    word-break: break-word;
}}

/* ── Keyframe: desliza desde la derecha, pausa, se desvanece ───────── */
@keyframes ada-toast-life {{
    0%   {{ opacity: 0; transform: translateX(32px); }}
    10%  {{ opacity: 1; transform: translateX(0);    }}
    75%  {{ opacity: 1; transform: translateX(0);    }}
    100% {{ opacity: 0; transform: translateX(8px);  }}
}}
</style>

<div id="{uid}">
    <span class="ada-toast-icon">{cfg['icon']}</span>
    <div class="ada-toast-body">
        <span class="ada-toast-label">{cfg['label']}</span>
        <span class="ada-toast-msg">{mensaje}</span>
    </div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)
