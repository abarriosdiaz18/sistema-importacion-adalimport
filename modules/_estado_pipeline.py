# ══════════════════════════════════════════════════════════════════════════════
# ADALIMPORT · modules/_estado_pipeline.py  ·  v1.0
# ──────────────────────────────────────────────────────────────────────────────
# Contrato de session_state entre los 4 pasos del pipeline wizard.
# Define qué REQUIERE y qué PRODUCE cada paso.
#
# REGLAS:
#   · Módulo Python puro — NO importa streamlit a nivel de módulo.
#   · Streamlit se importa SOLO dentro de las funciones (lazy import).
#   · No importa nada de otras páginas (_paso1, _paso2, etc.).
#   · Esta es la ÚNICA fuente de verdad sobre prerequisitos del wizard.
#
# USO (en cualquier archivo _pasoN_*.py):
#   from modules._estado_pipeline import paso_habilitado, paso_completado
#
# UBICACIÓN: carpeta modules/ en la raíz del proyecto (al mismo nivel que app.py)
# ══════════════════════════════════════════════════════════════════════════════

# ── Contrato de estado por paso ───────────────────────────────────────────────
# "requiere" → claves que DEBEN existir y ser truthy en session_state
#              para que el paso esté disponible (botón habilitado).
# "produce"  → claves que el paso deposita al completarse.
#              paso_completado(n) verifica que todas existen.
# "label"    → texto corto para mostrar en la barra wizard.
# "emoji"    → ícono visual del paso.
# ─────────────────────────────────────────────────────────────────────────────
ESTADO_PASO: dict = {
    1: {
        "requiere": [],                                       # Paso 1: sin prerequisitos
        "produce":  ["lote_id", "resultados_lote", "_lote_aprobado"],
        "label":    "Lote",
        "emoji":    "📦",
        "desc":     "Carga y cálculo",
    },
    2: {
        "requiere": ["lote_id", "_lote_aprobado"],            # Necesita lote aprobado
        "produce":  ["ev_paso2_completado"],                  # Flag explícito de paso 2
        "label":    "Estudio",
        "emoji":    "🎨",
        "desc":     "Edición visual",
    },
    3: {
        "requiere": ["lote_id", "resultados_lote"],           # Solo necesita resultados
        "produce":  ["excel_bytes_cms"],                      # Bytes del .xlsx generado
        "label":    "Exportar",
        "emoji":    "📊",
        "desc":     "Excel para CMS",
    },
    4: {
        "requiere": ["lote_id", "resultados_lote"],           # Solo necesita resultados
        "produce":  ["copys_generados_ok"],                   # Flag de copys generados
        "label":    "Publicar",
        "emoji":    "✍️",
        "desc":     "Copys y textos",
    },
}


# ── Funciones públicas ────────────────────────────────────────────────────────

def paso_habilitado(n: int) -> bool:
    """
    Verifica si el paso N puede ser accedido.
    Retorna True si TODAS las claves en 'requiere' existen
    y son truthy en st.session_state.

    Paso 1 siempre está habilitado (sin prerequisitos).
    """
    import streamlit as st
    reqs = ESTADO_PASO.get(n, {}).get("requiere", [])
    return all(bool(st.session_state.get(k)) for k in reqs)


def paso_completado(n: int) -> bool:
    """
    Verifica si el paso N fue completado.
    Retorna True si TODAS las claves en 'produce' existen
    y son truthy en st.session_state.
    """
    import streamlit as st
    produce = ESTADO_PASO.get(n, {}).get("produce", [])
    return all(bool(st.session_state.get(k)) for k in produce)


def get_paso_actual() -> int:
    """
    Detecta el paso actual lógico basándose en el estado.
    Devuelve el primer paso habilitado que NO está completado.
    Si todos están completados, devuelve 4.
    Si ninguno está completado, devuelve 1.
    """
    for n in [1, 2, 3, 4]:
        if paso_habilitado(n) and not paso_completado(n):
            return n
    return 4


def resumen_estado() -> dict:
    """
    Devuelve un dict con el estado de todos los pasos.
    Útil para debug o para mostrar un panel de estado completo.

    Retorna:
        {
            1: {"habilitado": bool, "completado": bool, "label": str, "emoji": str},
            2: {...},
            ...
        }
    """
    return {
        n: {
            "habilitado": paso_habilitado(n),
            "completado": paso_completado(n),
            "label":      ESTADO_PASO[n]["label"],
            "emoji":      ESTADO_PASO[n]["emoji"],
            "desc":       ESTADO_PASO[n]["desc"],
        }
        for n in [1, 2, 3, 4]
    }


def marcar_paso2_completado() -> None:
    """
    Helper para que _paso2_estudio.py marque el paso 2 como completado
    sin necesidad de conocer el nombre exacto de la clave 'produce'.
    Llámalo después de que al menos 1 imagen fue procesada exitosamente.
    """
    import streamlit as st
    st.session_state["ev_paso2_completado"] = True


def marcar_copys_generados() -> None:
    """
    Helper para que _paso4_publicaciones.py marque el paso 4 como completado.
    Llámalo después de que al menos 1 copy fue generado exitosamente.
    """
    import streamlit as st
    st.session_state["copys_generados_ok"] = True


def resetear_pipeline() -> None:
    """
    Limpia ÚNICAMENTE las claves 'produce' de todos los pasos.
    NO toca los datos del lote (resultados_lote, productos, etc.).
    Úsalo para reiniciar el progreso del wizard sin perder los datos base.
    """
    import streamlit as st
    todas_las_produce = []
    for n in [1, 2, 3, 4]:
        todas_las_produce.extend(ESTADO_PASO[n].get("produce", []))
    for k in todas_las_produce:
        st.session_state.pop(k, None)
