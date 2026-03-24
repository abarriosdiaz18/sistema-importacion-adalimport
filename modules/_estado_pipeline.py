# ══════════════════════════════════════════════════════════════════════════════
# ADALIMPORT · modules/_estado_pipeline.py  ·  v1.1  (Fix contrato E2E)
# ──────────────────────────────────────────────────────────────────────────────
# Contrato de session_state entre los 4 pasos del pipeline wizard.
# Define qué REQUIERE y qué PRODUCE cada paso.
#
# v1.1 — CAMBIOS RESPECTO A v1.0:
#   · Paso 1 "produce" ampliado: incluye "_lote_modo", "_lote_costo_total",
#     "_lote_ganancia", "_lote_env_total" para garantizar que el Paso 3
#     siempre tenga los datos financieros del lote.
#   · Nuevo helper: asegurar_lote_id() — copia _lote_id_reg → lote_id
#     de forma idempotente. Evita race condition en _paso1_lote.py.
#   · Nuevo helper: debug_estado_pipeline() — imprime en consola el estado
#     completo para diagnóstico sin interferir con la UI.
#   · ESTADO_PASO[3]["requiere"] ampliado: incluye "_lote_modo" para
#     garantizar que los datos financieros existan antes de exportar.
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
        # Paso 1: sin prerequisitos — siempre accesible
        "requiere": [],
        # v1.1: ampliado con claves financieras que garantizan el Paso 3
        "produce":  [
            "lote_id",            # ID único del lote aprobado
            "resultados_lote",    # Lista de dicts con resultados por ítem
            "_lote_aprobado",     # Flag booleano de aprobación
            "_lote_modo",         # "aereo" | "maritimo"
            "_lote_costo_total",  # float — inversión total
            "_lote_ganancia",     # float — ganancia proyectada total
            "_lote_env_total",    # float — costo envío total prorateado
        ],
        "label":    "Lote",
        "emoji":    "📦",
        "desc":     "Carga y cálculo",
    },
    2: {
        # Paso 2 requiere lote aprobado del Paso 1
        "requiere": ["lote_id", "_lote_aprobado"],
        "produce":  ["ev_paso2_completado"],   # Flag explícito de paso 2
        "label":    "Estudio",
        "emoji":    "🎨",
        "desc":     "Edición visual",
    },
    3: {
        # v1.1: agregado "_lote_modo" para garantizar datos financieros completos
        "requiere": ["lote_id", "resultados_lote", "_lote_modo"],
        "produce":  ["excel_bytes_cms"],       # Bytes del .xlsx generado
        "label":    "Exportar",
        "emoji":    "📊",
        "desc":     "Excel para CMS",
    },
    4: {
        # Paso 4: solo necesita resultados (copys pueden generarse sin imágenes)
        "requiere": ["lote_id", "resultados_lote"],
        "produce":  ["copys_generados_ok"],    # Flag de copys generados
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


def asegurar_lote_id() -> bool:
    """
    v1.1 — Helper para _paso1_lote.py.
    Copia '_lote_id_reg' → 'lote_id' de forma IDEMPOTENTE.
    Siempre sincroniza (no solo si lote_id no existe), para que
    una re-aprobación con nuevo ID actualice correctamente.

    Retorna True si lote_id quedó seteado, False si no había _lote_id_reg.
    """
    import streamlit as st
    _id = st.session_state.get("_lote_id_reg", "")
    if _id:
        st.session_state["lote_id"] = _id
        return True
    return False


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


def debug_estado_pipeline() -> None:
    """
    v1.1 — Imprime en consola (no en UI) el estado completo del pipeline.
    Útil durante desarrollo. Llámalo desde cualquier _pasoN_*.py con:
        from modules._estado_pipeline import debug_estado_pipeline
        debug_estado_pipeline()
    """
    import streamlit as st
    print("\n" + "═" * 60)
    print("  ADALIMPORT · DEBUG ESTADO PIPELINE")
    print("═" * 60)

    todas_claves = set()
    for n in [1, 2, 3, 4]:
        todas_claves.update(ESTADO_PASO[n].get("requiere", []))
        todas_claves.update(ESTADO_PASO[n].get("produce",  []))

    for clave in sorted(todas_claves):
        valor = st.session_state.get(clave, "⬜ NO EXISTE")
        if valor != "⬜ NO EXISTE":
            tipo = type(valor).__name__
            resumen = str(valor)[:60] if not isinstance(valor, (list, dict)) else f"[{tipo} len={len(valor)}]"
            print(f"  ✅ {clave:<35} = {resumen}")
        else:
            print(f"  ❌ {clave}")

    print("─" * 60)
    for n in [1, 2, 3, 4]:
        cfg = ESTADO_PASO[n]
        hab = paso_habilitado(n)
        comp = paso_completado(n)
        estado_txt = "✅ COMPLETADO" if comp else ("🔓 HABILITADO" if hab else "🔒 BLOQUEADO")
        print(f"  Paso {n} {cfg['emoji']} {cfg['label']:<12}: {estado_txt}")
    print("═" * 60 + "\n")
