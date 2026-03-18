# ══════════════════════════════════════════════════════════════════════════════
# ADALIMPORT · pages/_publicaciones.py  ·  v4.0 — Consola de Ventas Profesional
# Rediseño completo: Lista lateral + Tabs por canal + Generación masiva ZIP
# Design System v2.0 — Syne / Inter / DM Mono · Navy/Oro/Verde Neón
# ══════════════════════════════════════════════════════════════════════════════
import streamlit as st
import sys, os, builtins as _builtins

# ── FIX sys.path ──────────────────────────────────────────────────────────────
_PROJECT_ROOT = getattr(_builtins, "_ADALIMPORT_ROOT",   os.getcwd())
_DB_DIR       = getattr(_builtins, "_ADALIMPORT_DB_DIR",
                        os.path.join(_PROJECT_ROOT, "database"))
for _p in (_DB_DIR, _PROJECT_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)
# ─────────────────────────────────────────────────────────────────────────────

# ── Design System ─────────────────────────────────────────────────────────────
from styles_adalimport import aplicar_estilos
aplicar_estilos()

# ── Módulos core (atomicidad: sin imports cruzados entre páginas) ─────────────
from generador_publicaciones import (
    generar_titulo, generar_descripcion, generar_copy_instagram,
    extraer_puntos_clave,
)
from config_envios import COMISION_ML
import config_envios as cfg

try:
    from db_manager import obtener_todos_los_lotes, obtener_lote_por_id, obtener_items_por_lote
    _DB_DISPONIBLE = True
except Exception:
    _DB_DISPONIBLE = False

# ── Módulo de procesamiento de imágenes (Estudio Visual) ─────────────────────
# render_estudio_visual vive en procesador_estudio_visual.py (módulo Python puro importable)
# Nombre diferenciado de _estudio_visual.py (página en pages/) para evitar conflictos.
try:
    from procesador_estudio_visual import render_estudio_visual
    _PROCESADOR_DISPONIBLE = True
except Exception:
    _PROCESADOR_DISPONIBLE = False
    def render_estudio_visual(*_a, **_kw): pass  # noqa: fallback silencioso
# ─────────────────────────────────────────────────────────────────────────────

# ══════════════════════════════════════════════════════════════════════════════
# PLANTILLAS GLOBALES
# ══════════════════════════════════════════════════════════════════════════════
METODOS_PAGO  = ["Efectivo", "Pago Móvil", "Transferencia", "Binance (USDT)", "PayPal"]
METODOS_ENVIO = ["Retiro personal en San Bernardino (Caracas)", "MRW", "ZOOM"]
GARANTIA      = "3 días por defectos de fábrica"

_BLOQUE_PAGO_ML = (
    "=========================================\n"
    "💳 MÉTODOS DE PAGO:\n"
    "=========================================\n\n"
    + "\n".join(f"• {m}" for m in METODOS_PAGO)
)
_BLOQUE_ENVIO_ML = (
    "=========================================\n"
    "📍 ENTREGA Y ENVÍOS:\n"
    "=========================================\n\n"
    + "\n".join(f"• {e}" for e in METODOS_ENVIO)
    + "\n📦 El costo de envío corre por cuenta del comprador."
)
_BLOQUE_GARANTIA_ML = (
    "=========================================\n"
    f"🛡️ GARANTÍA: {GARANTIA}.\n"
    "========================================="
)

_BLOQUE_PAGO_WA  = "*💳 Métodos de Pago:*\n" + "\n".join(f"• {m}" for m in METODOS_PAGO)
_BLOQUE_ENVIO_WA = "*📍 Envíos:*\n"           + "\n".join(f"• {e}" for e in METODOS_ENVIO)
_BLOQUE_GARANTIA_WA = f"*🛡️ Garantía:* {GARANTIA}."

_BLOQUE_PAGO_IG  = "💳 " + " · ".join(METODOS_PAGO)
_BLOQUE_ENVIO_IG = "📦 " + " · ".join(METODOS_ENVIO)

_HASHTAGS_IG = (
    "#ADALIMPORT #Venezuela #Caracas #ImportadoUSA "
    "#TechVenezuela #ProductosUSA #ComprasOnline #EnviosVenezuela"
)


# ══════════════════════════════════════════════════════════════════════════════
# GENERADORES DE COPY POR CANAL
# ══════════════════════════════════════════════════════════════════════════════

def _copy_mercadolibre(titulo: str, precio: float, desc: str, marca: str) -> tuple:
    titulo_clean = titulo[:60].rstrip()
    if len(titulo) > 60:
        ultimo_sp = titulo_clean.rfind(" ")
        titulo_clean = titulo_clean[:ultimo_sp] if ultimo_sp != -1 else titulo_clean

    puntos = extraer_puntos_clave(desc, max_puntos=6)
    if puntos:
        ficha = "\n".join(f"• {p.capitalize()}" for p in puntos)
    else:
        ficha = (
            "• Producto nuevo y original 100%\n"
            "• Productos Importados\n"
            "• Disponible en Caracas · Envíos nacionales"
        )

    descripcion = f"""{titulo_clean.upper()}
══════════════════════════════════════════
Producto importado. Original y garantizado.

=========================================
📝 CARACTERÍSTICAS:
=========================================

{ficha}

=========================================
💰 PRECIO: ${precio:.2f}
=========================================

⚠️ Consultar disponibilidad antes de ofertar.
Respondemos a la brevedad posible.


{_BLOQUE_ENVIO_ML}


{_BLOQUE_PAGO_ML}


{_BLOQUE_GARANTIA_ML}
"""
    return titulo_clean, descripcion


def _copy_instagram(titulo: str, precio: float, desc: str) -> str:
    puntos = extraer_puntos_clave(desc, max_puntos=3)
    bullets = (
        "\n".join(f"✅ {p.capitalize()}" for p in puntos)
        if puntos
        else "✅ Original importado\n✅ Disponible en Caracas\n✅ Envíos a todo el país"
    )

    return f"""🔥 {titulo} 🔥

{bullets}

💰 Precio: ${precio:.2f}

{_BLOQUE_ENVIO_IG}
{_BLOQUE_PAGO_IG}
🛡️ {GARANTIA}

📩 Escríbenos por DM o WhatsApp para apartar el tuyo ⬇️

{_HASHTAGS_IG}"""


def _copy_whatsapp(titulo: str, precio: float, desc: str) -> str:
    puntos = extraer_puntos_clave(desc, max_puntos=3)
    bullets = (
        "\n".join(f"✅ {p.capitalize()}" for p in puntos)
        if puntos
        else "✅ Original importado\n✅ Disponible en Caracas\n✅ Envíos a todo el país"
    )

    return f"""*{titulo}*

{bullets}

💰 *Precio: ${precio:.2f}*

{_BLOQUE_ENVIO_WA}

{_BLOQUE_PAGO_WA}

{_BLOQUE_GARANTIA_WA}

📩 *¿Te interesa? Escríbenos.*"""


# ══════════════════════════════════════════════════════════════════════════════
# ESTILOS LOCALES — Consola de Ventas v4.0
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>

/* ══ PAGE LAYOUT ══════════════════════════════════════════════════════════════ */
.pub-page-header {
    padding: 0 0 20px 0;
    border-bottom: 1px solid rgba(184,150,62,0.12);
    margin-bottom: 24px;
}
.pub-page-eyebrow {
    font-family: var(--font-mono) !important;
    font-size: 0.58rem;
    letter-spacing: 4px;
    text-transform: uppercase;
    color: var(--gold);
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
}
.pub-page-eyebrow::before {
    content: '';
    display: inline-block;
    width: 20px;
    height: 1px;
    background: var(--gold);
    opacity: 0.5;
}
.pub-page-title {
    font-family: var(--font-display) !important;
    font-size: 1.7rem;
    font-weight: 800;
    color: var(--text);
    letter-spacing: -0.5px;
    line-height: 1.1;
    margin: 0 0 6px 0;
}
.pub-page-title span { color: var(--gold); }
.pub-page-desc {
    font-family: var(--font-body) !important;
    font-size: 0.82rem;
    color: var(--muted);
    margin: 0;
}

/* ══ BARRA SUPERIOR — ACCIONES MASIVAS ═══════════════════════════════════════ */
.pub-topbar {
    background: linear-gradient(135deg, rgba(184,150,62,0.07) 0%, rgba(8,14,26,0.8) 100%);
    border: 1px solid rgba(184,150,62,0.22);
    border-top: 2px solid var(--gold);
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 22px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    flex-wrap: wrap;
}
.pub-topbar-info {
    font-family: var(--font-body) !important;
    font-size: 0.82rem;
    color: var(--muted);
    line-height: 1.5;
}
.pub-topbar-info strong { color: var(--gold-lt); }
.pub-topbar-stat {
    font-family: var(--font-mono) !important;
    font-size: 1.4rem;
    font-weight: 500;
    color: var(--text);
}
.pub-topbar-stat-label {
    font-family: var(--font-mono) !important;
    font-size: 0.58rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--muted);
    display: block;
}

/* ══ LAYOUT PRINCIPAL: LISTA LATERAL + ÁREA CENTRAL ══════════════════════════ */
/* (gestionado con st.columns — CSS de soporte) */

/* ── Panel lateral de productos ──────────────────────────────────────────── */
.pub-product-list-wrap {
    background: var(--navy-md);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
}
.pub-list-header {
    background: rgba(184,150,62,0.06);
    border-bottom: 1px solid var(--border);
    padding: 12px 14px;
    font-family: var(--font-mono) !important;
    font-size: 0.62rem;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: var(--gold);
    display: flex;
    align-items: center;
    gap: 8px;
}
.pub-product-item {
    padding: 10px 14px;
    border-bottom: 1px solid rgba(20,30,48,0.8);
    cursor: pointer;
    transition: background 0.15s;
    display: flex;
    align-items: center;
    gap: 10px;
}
.pub-product-item:hover {
    background: rgba(184,150,62,0.05);
}
.pub-product-item.active {
    background: rgba(184,150,62,0.10);
    border-left: 2px solid var(--gold);
}
.pub-product-item-name {
    font-family: var(--font-body) !important;
    font-size: 0.82rem;
    font-weight: 500;
    color: var(--text);
    line-height: 1.3;
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.pub-product-item-price {
    font-family: var(--font-mono) !important;
    font-size: 0.72rem;
    color: var(--gold);
    flex-shrink: 0;
}
.pub-product-item-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    flex-shrink: 0;
}
.dot-ok   { background: var(--neon); }
.dot-warn { background: var(--yellow); }
.dot-none { background: var(--muted); }

/* ══ ÁREA CENTRAL — CONSOLA ══════════════════════════════════════════════════ */
.pub-console-header {
    background: linear-gradient(135deg, var(--navy-lt) 0%, var(--navy-md) 100%);
    border: 1px solid var(--border-lt);
    border-radius: 12px;
    padding: 18px 20px 14px;
    margin-bottom: 18px;
    position: relative;
    overflow: hidden;
}
.pub-console-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--gold), transparent);
}
.pub-console-eyebrow {
    font-family: var(--font-mono) !important;
    font-size: 0.58rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 6px;
}
.pub-console-product-name {
    font-family: var(--font-display) !important;
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text);
    line-height: 1.2;
    margin: 0 0 8px 0;
}
.pub-console-meta {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    margin-top: 8px;
}
.pub-console-chip {
    font-family: var(--font-mono) !important;
    font-size: 0.68rem;
    background: var(--navy);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 3px 10px;
    color: var(--muted);
}
.pub-console-chip b { color: var(--text); }
.pub-console-price {
    font-family: var(--font-mono) !important;
    font-size: 1.15rem;
    font-weight: 500;
    color: var(--gold);
}

/* ══ TÍTULO BOX ML ═══════════════════════════════════════════════════════════ */
.pub-titulo-box {
    background: rgba(184,150,62,0.05);
    border: 1px solid rgba(184,150,62,0.18);
    border-left: 3px solid var(--gold);
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin-bottom: 14px;
}
.pub-titulo-box .tit-label {
    font-family: var(--font-mono) !important;
    font-size: 0.60rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 5px;
    display: block;
}
.pub-titulo-box .tit-value {
    font-family: var(--font-body) !important;
    font-weight: 600;
    font-size: 1rem;
    color: var(--text);
    line-height: 1.3;
}
.pub-titulo-box .tit-chars {
    font-family: var(--font-mono) !important;
    font-size: 0.68rem;
    margin-top: 5px;
    display: block;
}
.tit-chars-ok   { color: var(--neon); }
.tit-chars-warn { color: var(--red); }

/* ══ TABS ════════════════════════════════════════════════════════════════════ */
div[data-testid="stTabs"] [data-testid="stTab"] {
    font-family: var(--font-mono) !important;
    font-size: 0.78rem;
    letter-spacing: 0.8px;
    font-weight: 500;
    padding: 8px 14px;
}
div[data-testid="stTabs"] [aria-selected="true"] {
    border-bottom-color: var(--gold) !important;
    color: var(--gold) !important;
}

/* ══ COPY AREA ═══════════════════════════════════════════════════════════════ */
.pub-copy-wrap {
    background: var(--navy-lt);
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 12px;
}
.pub-copy-topbar {
    background: rgba(184,150,62,0.04);
    border-bottom: 1px solid var(--border);
    padding: 8px 14px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
}
.pub-copy-topbar-label {
    font-family: var(--font-mono) !important;
    font-size: 0.60rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--muted);
}
.pub-copy-canal-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-family: var(--font-mono) !important;
    font-size: 0.62rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    padding: 2px 9px;
    border-radius: 20px;
    border: 1px solid;
}
.badge-ml  { color: #FFD600; border-color: rgba(255,214,0,0.3);  background: rgba(255,214,0,0.05); }
.badge-ig  { color: #e1306c; border-color: rgba(225,48,108,0.3); background: rgba(225,48,108,0.05); }
.badge-wa  { color: var(--neon); border-color: rgba(0,230,118,0.3); background: rgba(0,230,118,0.05); }

/* ══ PLANTILLA BADGE INFO ════════════════════════════════════════════════════ */
.pub-template-badge {
    background: rgba(184,150,62,0.04);
    border: 1px solid rgba(184,150,62,0.14);
    border-left: 3px solid var(--gold);
    border-radius: 0 8px 8px 0;
    padding: 8px 14px;
    margin: 0 0 14px 0;
    font-family: var(--font-body) !important;
    font-size: 0.78rem;
    color: var(--muted);
    line-height: 1.6;
}
.pub-template-badge strong { color: var(--gold-lt); }

/* ══ EMPTY / WARNING STATES ══════════════════════════════════════════════════ */
.pub-empty-state {
    background: linear-gradient(135deg, var(--navy-md), var(--navy));
    border: 1px solid var(--border-lt);
    border-radius: 14px;
    padding: 2.2rem 1.8rem;
    margin: 1rem 0 1.5rem;
    text-align: center;
}
.pub-empty-state .empty-ico   { font-size: 2.2rem; margin-bottom: 0.8rem; display: block; }
.pub-empty-state .empty-title {
    font-family: var(--font-display) !important;
    font-weight: 700;
    font-size: 1rem;
    color: var(--gold);
    margin-bottom: 0.5rem;
}
.pub-empty-state .empty-desc {
    font-family: var(--font-body) !important;
    font-weight: 400;
    color: var(--muted);
    font-size: 0.85rem;
    line-height: 1.65;
    margin-bottom: 0.8rem;
}
.pub-empty-state .empty-hint {
    font-family: var(--font-mono) !important;
    font-size: 0.68rem;
    color: var(--border-lt);
    border-top: 1px solid var(--border);
    padding-top: 0.8rem;
    margin-top: 0.5rem;
}

/* ══ NO DESCRIPCIÓN — WARNING CARD ══════════════════════════════════════════ */
.pub-nodesc-card {
    background: rgba(184,150,62,0.05);
    border: 1px solid rgba(184,150,62,0.28);
    border-left: 3px solid var(--gold);
    border-radius: 0 10px 10px 0;
    padding: 12px 16px;
    margin-bottom: 14px;
}
.pub-nodesc-title {
    font-family: var(--font-display) !important;
    font-weight: 700;
    font-size: 0.85rem;
    color: var(--gold);
    margin-bottom: 4px;
}
.pub-nodesc-desc {
    font-family: var(--font-body) !important;
    font-size: 0.8rem;
    color: var(--muted);
    line-height: 1.5;
}
.pub-nodesc-desc strong { color: var(--text); }

/* ══ BADGES CONTEXTO ══════════════════════════════════════════════════════════ */
.pub-badge-activo {
    background: rgba(0,230,118,0.05);
    border: 1px solid rgba(0,230,118,0.18);
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 0.8rem;
    color: rgba(0,230,118,0.75);
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-family: var(--font-body) !important;
}
.pub-badge-manual {
    background: rgba(184,150,62,0.05);
    border: 1px solid rgba(184,150,62,0.2);
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 0.8rem;
    color: rgba(184,150,62,0.85);
    margin-bottom: 14px;
    font-family: var(--font-body) !important;
}

/* ══ HISTORIAL BUSCADOR ══════════════════════════════════════════════════════ */
.pub-buscador-wrap {
    background: linear-gradient(135deg, var(--navy-md) 0%, var(--navy-lt) 100%);
    border: 1px solid rgba(184,150,62,0.22);
    border-top: 2px solid var(--gold);
    border-radius: 12px;
    padding: 16px 18px 18px;
    margin-bottom: 18px;
}
.pub-buscador-eyebrow {
    font-family: var(--font-mono) !important;
    font-size: 0.58rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--gold);
    margin-bottom: 4px;
}
.pub-buscador-title {
    font-family: var(--font-display) !important;
    font-size: 1rem;
    font-weight: 700;
    color: var(--text);
    margin: 0 0 4px 0;
}
.pub-buscador-desc {
    font-family: var(--font-body) !important;
    font-size: 0.80rem;
    color: var(--muted);
    margin: 0 0 12px 0;
}
.pub-hist-banner {
    background: rgba(0,230,118,0.04);
    border: 1px solid rgba(0,230,118,0.18);
    border-radius: 8px;
    padding: 8px 14px;
    font-family: var(--font-body) !important;
    font-size: 0.82rem;
    color: var(--neon);
    margin-top: 10px;
}

/* ══ SECCIÓN LOTE MASIVO ══════════════════════════════════════════════════════ */
.pub-masivo-header {
    background: linear-gradient(135deg, rgba(0,26,13,0.9) 0%, var(--navy-md) 100%);
    border: 1px solid rgba(0,230,118,0.2);
    border-top: 2px solid var(--neon);
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 18px;
    display: flex;
    align-items: center;
    gap: 14px;
}
.pub-masivo-ico {
    font-size: 1.8rem;
    line-height: 1;
    filter: drop-shadow(0 0 10px rgba(0,230,118,0.4));
}
.pub-masivo-title {
    font-family: var(--font-display) !important;
    font-weight: 700;
    font-size: 1rem;
    color: var(--neon);
    margin: 0 0 3px 0;
}
.pub-masivo-sub {
    font-family: var(--font-body) !important;
    font-size: 0.78rem;
    color: var(--muted);
}
.pub-preview-price {
    font-family: var(--font-mono) !important;
    color: var(--gold);
    font-weight: 700;
}
.pub-preview-desc-ok   { color: var(--neon);   font-size: 0.78rem; font-family: var(--font-body) !important; }
.pub-preview-desc-warn { color: var(--yellow); font-size: 0.78rem; font-family: var(--font-body) !important; }
.pub-dl-banner {
    background: rgba(13,26,13,0.8);
    border: 1px solid rgba(26,58,26,0.8);
    border-radius: 8px;
    padding: 0.8rem 1.2rem;
    font-family: var(--font-body) !important;
    font-size: 0.82rem;
    color: var(--muted);
    margin: 0.5rem 0;
    line-height: 1.55;
}

/* ══ CIERRE DE CICLO ═════════════════════════════════════════════════════════ */
.pub-cycle-close {
    background: var(--navy-md);
    border: 1px solid var(--border-lt);
    border-radius: 10px;
    padding: 0.9rem 1.2rem;
    text-align: center;
    margin-bottom: 0.8rem;
}
.pub-cycle-close .cycle-label {
    font-family: var(--font-mono) !important;
    color: var(--blue);
    font-size: 0.72rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 0.3rem;
    display: block;
}
.pub-cycle-close .cycle-msg {
    font-family: var(--font-body) !important;
    font-weight: 600;
    color: var(--text);
    font-size: 0.9rem;
}

/* ══ SELECTBOX FOCUS ═════════════════════════════════════════════════════════ */
div[data-testid="stSelectbox"] > div:focus-within {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 2px rgba(184,150,62,0.14) !important;
}

/* ══ INSTRUCCIÓN DE COPIA ════════════════════════════════════════════════════ */
.pub-copy-hint {
    font-family: var(--font-mono) !important;
    font-size: 0.62rem;
    color: var(--muted);
    text-align: center;
    letter-spacing: 0.5px;
    margin-top: 4px;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def _safe_str(v) -> str:
    if v is None or (isinstance(v, float) and v != v):
        return ""
    return str(v).strip()


_LOTE_KEYS = [
    "lote_activo", "lote_activo_marketing", "resultados_lote",
    "catalogo_df", "_lote_id_reg", "pub_modo_manual",
    "_pub_nombre", "_pub_marca", "_pub_precio", "_pub_desc", "_pub_sel_ant",
    "_zip_listo", "_zip_n_archivos", "_desc_temporales",
    "_pub_copy_ml", "_pub_copy_ig", "_pub_copy_wa",
]

def _resetear_home():
    """Limpia todo el session_state y regresa al selector de courier."""
    for _k in _LOTE_KEYS:
        st.session_state.pop(_k, None)
    st.session_state["courier_sel"] = None


def _template_info():
    pagos  = " · ".join(METODOS_PAGO)
    envios = " · ".join(METODOS_ENVIO)
    st.markdown(f"""
    <div class="pub-template-badge">
        <strong>💳 Pago:</strong> {pagos}<br>
        <strong>📍 Envío:</strong> {envios}<br>
        <strong>🛡️ Garantía:</strong> {GARANTIA}
    </div>""", unsafe_allow_html=True)


def _render_copy_block(texto: str, canal_label: str, canal_class: str, key_ta: str, height: int = 220):
    """
    Renderiza el bloque de copia para un canal dado.
    Muestra st.code (preview) + st.text_area para copiar.
    """
    st.markdown(f"""
    <div class="pub-copy-wrap">
        <div class="pub-copy-topbar">
            <span class="pub-copy-topbar-label">Vista previa del copy</span>
            <span class="pub-copy-canal-badge {canal_class}">{canal_label}</span>
        </div>
    </div>""", unsafe_allow_html=True)

    st.code(texto, language=None)

    st.markdown(
        '<span style="font-family:var(--font-mono);font-size:0.60rem;'
        'letter-spacing:2px;text-transform:uppercase;color:var(--muted);">'
        '▸ Seleccionar y copiar</span>',
        unsafe_allow_html=True,
    )
    st.text_area(
        "copy_area",
        value=texto,
        height=height,
        key=key_ta,
        label_visibility="collapsed",
        help="Haz clic aquí → Ctrl+A → Ctrl+C",
    )
    st.markdown(
        '<p class="pub-copy-hint">💡 Clic en el campo → Ctrl+A → Ctrl+C</p>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# HEADER DE PÁGINA
# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
# HEADER DE PÁGINA
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div style="background:linear-gradient(135deg,rgba(13,20,36,0.9) 0%,rgba(5,9,15,0.95) 100%);
            border:1px solid rgba(184,150,62,0.2);border-top:2px solid var(--gold);
            border-radius:14px;padding:20px 24px;margin-bottom:24px;
            display:flex;align-items:center;gap:16px;">
  <span style="font-size:2rem;line-height:1;filter:drop-shadow(0 0 10px rgba(184,150,62,0.4));">📣</span>
  <div style="flex:1">
    <div style="font-family:'DM Mono',monospace;font-size:0.58rem;letter-spacing:3px;
                text-transform:uppercase;color:var(--gold);margin-bottom:4px;">
      Publicaciones · Consola de Ventas
    </div>
    <div style="font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:800;
                color:var(--text);line-height:1.1;margin-bottom:4px;">
      Consola de <span style="color:var(--gold);">Marketing</span>
    </div>
    <div style="font-family:'Inter',sans-serif;font-size:0.82rem;color:var(--muted);">
      Genera copys optimizados para MercadoLibre, Instagram y WhatsApp desde el lote aprobado
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# 📂 BUSCADOR DE LOTES DESDE HISTORIAL
# ══════════════════════════════════════════════════════════════════════════════
if _DB_DISPONIBLE:
    st.markdown("""
    <div class="pub-buscador-wrap">
      <div class="pub-buscador-eyebrow">▸ Base de datos · Lotes archivados</div>
      <div class="pub-buscador-title">📂 Cargar Lote desde el Historial</div>
      <div class="pub-buscador-desc">
        Selecciona un lote cerrado para regenerar sus copys sin necesidad de reprocesarlo.
      </div>
    </div>
    """, unsafe_allow_html=True)

    try:
        _lotes_hist = obtener_todos_los_lotes()
    except Exception as _e_hist:
        _lotes_hist = []
        st.warning(f"No se pudo acceder al historial: {_e_hist}")

    if not _lotes_hist:
        st.markdown("""
        <div style="font-family:var(--font-body);font-size:0.82rem;color:var(--muted);
                    padding:14px;text-align:center;
                    border:1px dashed rgba(184,150,62,0.15);
                    border-radius:8px;margin-bottom:20px;">
            📭 Aún no hay lotes archivados. Aprueba un lote primero.
        </div>""", unsafe_allow_html=True)
    else:
        _opts_map = {}
        for _lh in _lotes_hist:
            _modo_ico = "✈" if str(_lh.get("modo", "")) == "Aéreo" else "🚢"
            _n_items  = _lh.get("total_items", 0)
            _label = (
                f"{_lh['lote_id_text']}  ·  {_lh['fecha']}  ·  "
                f"{_lh.get('courier','—')}  ·  {_modo_ico} {_n_items} ítems"
            )
            _opts_map[_label] = _lh["lote_id_text"]

        _PLACEHOLDER_HIST = "— Seleccionar lote archivado —"
        _opciones_hist    = [_PLACEHOLDER_HIST] + list(_opts_map.keys())

        _col_sel_h, _col_btn_h = st.columns([3, 1])
        with _col_sel_h:
            st.markdown(
                '<label style="font-family:var(--font-body);font-size:0.78rem;'
                'color:var(--muted);display:block;margin-bottom:4px;">Lote archivado</label>',
                unsafe_allow_html=True,
            )
            _sel_hist = st.selectbox(
                "Lote archivado",
                options=_opciones_hist,
                index=0,
                label_visibility="collapsed",
                key="hist_recover_sel",
                help="Filtra por ID, fecha, courier o modo de envío",
            )
        with _col_btn_h:
            st.markdown('<div style="margin-top:24px"></div>', unsafe_allow_html=True)
            _btn_cargar_hist = st.button(
                "📥 Cargar",
                use_container_width=True,
                key="btn_cargar_hist",
                disabled=(_sel_hist == _PLACEHOLDER_HIST),
            )
            if st.button(
                "🗑️ Limpiar",
                use_container_width=True,
                key="btn_limpiar_marketing",
                help="Descarga el lote activo y reinicia el módulo",
            ):
                for _kl in [
                    "lote_activo_marketing", "resultados_lote",
                    "_zip_listo", "_zip_n_archivos", "_lote_id_reg",
                    "_desc_temporales", "_pub_copy_ml", "_pub_copy_ig", "_pub_copy_wa",
                ]:
                    st.session_state.pop(_kl, None)
                st.session_state["pub_modo_manual"] = False
                st.rerun()

        if _btn_cargar_hist and _sel_hist != _PLACEHOLDER_HIST:
            _lote_id_rec = _opts_map.get(_sel_hist, "")
            if _lote_id_rec:
                try:
                    _header_rec = obtener_lote_por_id(_lote_id_rec)
                    _items_rec  = obtener_items_por_lote(_lote_id_rec)
                    if _items_rec:
                        _resultados_mapped = [
                            {
                                "nombre":             _it.get("nombre", ""),
                                "cantidad":           _it.get("cantidad", 1),
                                "tienda":             _it.get("tienda", ""),
                                "precio_tienda":      _it.get("costo_unitario", 0),
                                "envio_courier":      _it.get("flete_individual", 0),
                                "costo_real":         _it.get("costo_real", 0),
                                "precio_ml":          _it.get("precio_venta", 0),
                                "precio_ml_objetivo": _it.get("precio_venta", 0),
                                "ganancia_objetivo":  _it.get("ganancia_neta", 0),
                                "margen_pct":         _it.get("margen_pct", 0),
                            }
                            for _it in _items_rec
                        ]
                        st.session_state["resultados_lote"]       = _resultados_mapped
                        st.session_state["lote_activo_marketing"] = {
                            "lote_id":          _lote_id_rec,
                            "modo":             "aereo" if str(_header_rec.get("modo","")) == "Aéreo" else "maritimo",
                            "courier":          _header_rec.get("courier", ""),
                            "resultados":       _resultados_mapped,
                            "origen_historial": True,
                        }
                        st.session_state["_llegada_pub"]    = True
                        st.session_state["_lote_id_reg"]    = _lote_id_rec
                        st.session_state["pub_modo_manual"] = False
                        st.success(
                            f"✅ **{_lote_id_rec}** cargado — "
                            f"{len(_resultados_mapped)} producto(s) disponibles."
                        )
                        st.rerun()
                    else:
                        st.warning(f"El lote **{_lote_id_rec}** no tiene ítems registrados.")
                except Exception as _exc_hist:
                    st.error(f"Error al recuperar el lote: {_exc_hist}")

        _lmkt = st.session_state.get("lote_activo_marketing") or {}
        if _lmkt.get("origen_historial") and _lmkt.get("lote_id"):
            st.markdown(f"""
            <div class="pub-hist-banner">
                📂 Lote archivado activo:
                <strong style="font-family:var(--font-mono);color:var(--neon);">
                  {_lmkt['lote_id']}
                </strong>
                <span style="color:var(--muted);">
                  ({len(_lmkt.get('resultados', []))} productos cargados desde historial)
                </span>
            </div>""", unsafe_allow_html=True)

    st.markdown(
        '<hr style="border:none;border-top:1px solid rgba(184,150,62,0.10);margin:4px 0 20px;">',
        unsafe_allow_html=True,
    )

# ── Llegada desde "IR A PUBLICACIONES" ───────────────────────────────────────
_acaba_de_llegar = st.session_state.pop("_llegada_pub", False)
if _acaba_de_llegar:
    _lote_id_arr = st.session_state.get("_lote_id_reg", "")
    st.markdown(f"""
    <div style="background:rgba(13,26,13,0.9);border:1px solid var(--neon);
                border-radius:8px;padding:0.8rem 1.2rem;
                font-family:var(--font-body);font-size:0.85rem;
                color:var(--neon);margin-bottom:1rem;">
        ✅ <strong>Lote
          <span style="font-family:var(--font-mono);">{_lote_id_arr}</span>
          cargado
        </strong> — Selecciona un producto del lote para generar su publicación.
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# VALIDACIÓN: ¿Hay lote aprobado o modo manual?
# ══════════════════════════════════════════════════════════════════════════════
_lote_mkt          = st.session_state.get("lote_activo_marketing")
_tiene_lote        = bool(_lote_mkt and _lote_mkt.get("resultados"))
_tiene_lote_sesion = bool(st.session_state.get("resultados_lote"))

if "pub_modo_manual" not in st.session_state:
    st.session_state["pub_modo_manual"] = False

if not _tiene_lote and not _tiene_lote_sesion and not st.session_state["pub_modo_manual"]:
    st.markdown("""
    <div class="pub-empty-state">
        <span class="empty-ico">📭</span>
        <div class="empty-title">Aún no has aprobado un lote para publicar</div>
        <div class="empty-desc">
            Ve a la pestaña <strong style="color:var(--blue);">📦 LOTE</strong>,
            analiza tus productos y aprueba la vía ganadora.<br>
            Los datos se cargarán aquí automáticamente.
        </div>
        <div class="empty-hint">
            ¿Quieres generar una publicación para un solo producto sin un lote?
        </div>
    </div>""", unsafe_allow_html=True)

    _col_or1, _col_or2, _col_or3 = st.columns([1, 1, 1])
    with _col_or2:
        if st.button(
            "✍️  Entrada Manual (1 producto)",
            use_container_width=True,
            key="btn_modo_manual_pub",
        ):
            st.session_state["pub_modo_manual"] = True
            st.rerun()
    st.stop()

# ── Badge de contexto ─────────────────────────────────────────────────────────
if _tiene_lote:
    _lote_id_badge = _lote_mkt.get("lote_id", "")
    _modo_badge    = "✈️ AÉREO" if _lote_mkt.get("modo") == "aereo" else "🚢 MARÍTIMO"
    st.markdown(f"""
    <div class="pub-badge-activo">
        <span style="color:var(--neon);">●</span>
        <span>Lote
          <strong style="font-family:var(--font-mono);color:var(--neon);">{_lote_id_badge}</strong>
          aprobado ({_modo_badge}) — datos disponibles
        </span>
    </div>""", unsafe_allow_html=True)
elif st.session_state["pub_modo_manual"]:
    _col_badge, _col_back = st.columns([4, 1])
    with _col_badge:
        st.markdown("""
        <div class="pub-badge-manual">
            ✍️ <strong style="color:var(--gold);">Modo Manual</strong>
            — Ingresa los datos del producto directamente
        </div>""", unsafe_allow_html=True)
    with _col_back:
        if st.button("✕ Cancelar", key="btn_cancel_manual", use_container_width=True):
            st.session_state["pub_modo_manual"] = False
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# BARRA SUPERIOR — GENERACIÓN MASIVA (prominente, siempre visible si hay lote)
# ══════════════════════════════════════════════════════════════════════════════
_n_lote = len(st.session_state.get("resultados_lote", []))

if _n_lote >= 1:
    st.markdown(f"""
    <div class="pub-topbar">
        <div>
            <span class="pub-topbar-stat-label">Productos en lote</span>
            <span class="pub-topbar-stat">{_n_lote}</span>
        </div>
        <div class="pub-topbar-info">
            Genera <strong>todos los copys de una vez</strong>
            y descarga el ZIP con archivos .txt listos para publicar.
        </div>
    </div>""", unsafe_allow_html=True)

    _col_masivo_a, _col_masivo_b = st.columns([3, 1])
    with _col_masivo_a:
        st.markdown(
            '<div style="font-family:var(--font-body);font-size:0.80rem;'
            'color:var(--muted);padding:8px 0;">',
            unsafe_allow_html=True,
        )
    with _col_masivo_b:
        _btn_masivo = st.button(
            "📦 Pack Masivo (ZIP)",
            use_container_width=True,
            key="btn_masivo_top",
            help=f"Genera un .txt con los 3 copys por cada uno de los {_n_lote} productos",
        )
    if _btn_masivo:
        st.session_state["_trigger_masivo"] = True
        st.rerun()

    st.markdown(
        '<hr style="border:none;border-top:1px solid rgba(184,150,62,0.10);margin:0 0 20px;">',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# ESTADO INTERNO
# ══════════════════════════════════════════════════════════════════════════════
for key, default in [
    ("_pub_nombre", ""), ("_pub_marca", ""), ("_pub_precio", 0.00),
    ("_pub_desc", ""), ("_pub_sel_ant", "— nuevo producto —"),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ══════════════════════════════════════════════════════════════════════════════
# LAYOUT PRINCIPAL: SELECTOR DE PRODUCTOS (izq) + CONSOLA (der)
# ══════════════════════════════════════════════════════════════════════════════
_resultados_lote = st.session_state.get("resultados_lote", [])
_cat             = st.session_state.get("catalogo_df", None)


def _resolver_desc_marca(nombre_prod: str):
    """Extrae marca y descripción del catálogo para un nombre dado."""
    marca_v, desc_v = "", ""
    if _cat is not None:
        _match = _cat[_cat["producto"].str.strip() == nombre_prod.strip()]
        if not _match.empty:
            _row = _match.iloc[0]
            marca_v = _safe_str(_row.get("marca", ""))
            desc_v  = _safe_str(_row.get("descripcion", _row.get("descripcion_origen", "")))
    return marca_v, desc_v


# ── Con lote: diseño 2 columnas (lista + consola) ─────────────────────────────
if _resultados_lote:
    nombres_lote = [r["nombre"] for r in _resultados_lote]
    opciones_sel = ["— Seleccionar producto —"] + nombres_lote

    # Selectbox prominent (funciona mejor que columnas HTML para el state)
    st.markdown(
        '<span style="font-family:var(--font-mono);font-size:0.62rem;'
        'letter-spacing:3px;text-transform:uppercase;color:var(--gold);">'
        '▸ Producto del lote</span>',
        unsafe_allow_html=True,
    )

    _col_sel, _col_counter = st.columns([4, 1])
    with _col_sel:
        _sel_ant = st.session_state["_pub_sel_ant"]
        _idx     = opciones_sel.index(_sel_ant) if _sel_ant in opciones_sel else 0
        _sel     = st.selectbox(
            "Seleccionar producto",
            opciones_sel,
            index=_idx,
            key="pub_selectbox_producto",
            label_visibility="collapsed",
        )
    with _col_counter:
        st.markdown(
            f'<div style="text-align:right;padding-top:8px;">'
            f'<span style="font-family:var(--font-mono);font-size:1.1rem;'
            f'font-weight:500;color:var(--text);">{_n_lote}</span>'
            f'<span style="font-family:var(--font-mono);font-size:0.6rem;'
            f'letter-spacing:1px;color:var(--muted);display:block;">productos</span></div>',
            unsafe_allow_html=True,
        )

    # Cambio de selección → actualiza state
    if _sel != _sel_ant:
        st.session_state["_pub_sel_ant"] = _sel
        for _ck in ["_pub_copy_ml", "_pub_copy_ig", "_pub_copy_wa"]:
            st.session_state.pop(_ck, None)

        if _sel != "— Seleccionar producto —":
            _prod_sel = next(r for r in _resultados_lote if r["nombre"] == _sel)
            _m, _d    = _resolver_desc_marca(_prod_sel["nombre"])
            st.session_state["_pub_nombre"] = _prod_sel["nombre"]
            st.session_state["_pub_marca"]  = _m
            st.session_state["_pub_precio"] = float(_prod_sel["precio_ml"])
            st.session_state["_pub_desc"]   = _d
        else:
            st.session_state["_pub_nombre"] = ""
            st.session_state["_pub_marca"]  = ""
            st.session_state["_pub_precio"] = 0.00
            st.session_state["_pub_desc"]   = ""
        st.rerun()

    # Mini-índice visual del lote
    with st.expander(f"📋 Ver todos los productos del lote ({_n_lote})", expanded=False):
        _filas_idx = ""
        for _idx_p, _r in enumerate(_resultados_lote, 1):
            _m_p, _d_p = _resolver_desc_marca(_r["nombre"])
            _dot_cls   = "dot-ok" if _d_p else "dot-warn"
            _dot_tip   = "Con descripción" if _d_p else "Sin descripción"
            _is_act    = "active" if _r["nombre"] == _sel else ""
            _filas_idx += (
                f'<div class="pub-product-item {_is_act}" title="{_dot_tip}">'
                f'  <span class="pub-product-item-dot {_dot_cls}"></span>'
                f'  <span class="pub-product-item-name">{_r["nombre"]}</span>'
                f'  <span class="pub-product-item-price">${_r["precio_ml"]:.2f}</span>'
                f'</div>'
            )
        st.markdown(
            f'<div class="pub-product-list-wrap">'
            f'  <div class="pub-list-header">▸ LOTE COMPLETO</div>'
            f'  {_filas_idx}'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# FORMULARIO DE PRODUCTO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    '<span style="font-family:var(--font-mono);font-size:0.62rem;'
    'letter-spacing:3px;text-transform:uppercase;color:var(--muted);">'
    '▸ Datos del producto</span>',
    unsafe_allow_html=True,
)

col_p1, col_p2 = st.columns(2)
with col_p1:
    p_nombre = st.text_input(
        "Nombre del producto",
        value=st.session_state["_pub_nombre"],
        placeholder="Ej: Pilas AAA Energizer 4pk",
        key="manual_input_nombre",
    )
    p_marca = st.text_input(
        "Marca",
        value=st.session_state["_pub_marca"],
        placeholder="Ej: Energizer",
        key="manual_input_marca",
    )
    p_precio = st.number_input(
        "Precio ML ($)",
        min_value=0.00,
        step=0.50,
        value=max(0.00, st.session_state["_pub_precio"]),
        key="manual_input_precio",
    )
with col_p2:
    # ── FIX descripciones vacías: aviso prominente + textarea antes de generar ──
    _desc_actual = st.session_state["_pub_desc"]
    _tiene_desc  = bool(_desc_actual and _desc_actual.strip())

    if not _tiene_desc and st.session_state["_pub_nombre"]:
        st.markdown("""
        <div class="pub-nodesc-card">
            <div class="pub-nodesc-title">⚠️ Sin descripción</div>
            <div class="pub-nodesc-desc">
                Este producto no tiene descripción en la base de datos.<br>
                Escríbela o pégala abajo para generar copys más precisos.
            </div>
        </div>""", unsafe_allow_html=True)

    p_desc_origen = st.text_area(
        "Descripción (pega en español desde la tienda)" if _tiene_desc
        else "✏️ Escribe la descripción del producto aquí",
        value=_desc_actual,
        placeholder="Ej: Pilas AA Energizer recargables, paquete de 4 unidades, 2000mAh...",
        height=180,
        key="manual_input_desc",
    )

# ── FIX: Snapshot temporal para modo manual ──────────────────────────────────
# Se actualiza en cada render con los valores ACTUALES de los inputs.
# La consola lo usará si pub_modo_manual=True y no hay copys generados aún,
# evitando KeyError/AttributeError al leer session_state con datos obsoletos.
if st.session_state.get("pub_modo_manual"):
    st.session_state["_pub_current_manual_snap"] = {
        "nombre": p_nombre,
        "marca":  p_marca,
        "precio": p_precio,
        "desc":   p_desc_origen,
    }

btn_col, clear_col = st.columns([2, 1])
with btn_col:
    generar = st.button("✨  GENERAR PUBLICACIÓN", use_container_width=True, type="primary")
with clear_col:
    if st.button("🗑  Limpiar campos", use_container_width=True):
        for _ck in [
            "_pub_nombre", "_pub_marca", "_pub_desc",
            "_pub_copy_ml", "_pub_copy_ig", "_pub_copy_wa",
        ]:
            st.session_state.pop(_ck, None)
        st.session_state["_pub_precio"]  = 0.00
        st.session_state["_pub_sel_ant"] = "— Seleccionar producto —"
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# GENERACIÓN — produce los 3 copys y los guarda en session_state
# ══════════════════════════════════════════════════════════════════════════════
if generar:
    if not p_nombre.strip():
        st.warning("Ingresa el nombre del producto.")
    else:
        _titulo_base   = generar_titulo(p_nombre, p_marca, p_desc_origen)
        _tit_ml, _desc_ml = _copy_mercadolibre(_titulo_base, p_precio, p_desc_origen, p_marca)
        _ig            = _copy_instagram(_titulo_base, p_precio, p_desc_origen)
        _wa            = _copy_whatsapp(_titulo_base, p_precio, p_desc_origen)

        st.session_state["_pub_copy_ml"] = (_tit_ml, _desc_ml)
        st.session_state["_pub_copy_ig"] = _ig
        st.session_state["_pub_copy_wa"] = _wa
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# CONSOLA DE MARKETING — 3 TABS
# ══════════════════════════════════════════════════════════════════════════════
_copy_ml_data = st.session_state.get("_pub_copy_ml")
_copy_ig_data = st.session_state.get("_pub_copy_ig")
_copy_wa_data = st.session_state.get("_pub_copy_wa")

if _copy_ml_data:
    _tit_ml, _desc_ml = _copy_ml_data

    # ── FIX modo manual: leer del snapshot si está disponible ────────────────
    # En modo manual los campos de texto son la fuente de verdad hasta que se
    # genera el copy. Si existe el snap (creado justo arriba en este render),
    # lo usamos para que la consola nunca muestre datos obsoletos o vacíos.
    _snap = st.session_state.get("_pub_current_manual_snap", {})
    if st.session_state.get("pub_modo_manual") and _snap:
        _nombre_activo = _snap.get("nombre") or st.session_state.get("_pub_nombre", "")
        _precio_activo = float(_snap.get("precio") or st.session_state.get("_pub_precio", 0.0))
        _marca_activa  = _snap.get("marca")  or st.session_state.get("_pub_marca", "")
    else:
        _nombre_activo = st.session_state.get("_pub_nombre", "")
        _precio_activo = float(st.session_state.get("_pub_precio", 0.0))
        _marca_activa  = st.session_state.get("_pub_marca", "")

    st.markdown(
        '<hr style="border:none;border-top:1px solid rgba(184,150,62,0.15);margin:1.2rem 0;">',
        unsafe_allow_html=True,
    )

    # Header de consola con nombre del producto en Syne
    _chars   = len(_tit_ml)
    _chars_cls = "tit-chars-ok" if _chars <= 60 else "tit-chars-warn"
    _marca_chip = (
        f'<span class="pub-console-chip"><b>Marca:</b> {_marca_activa}</span>'
        if _marca_activa else ""
    )

    st.markdown(f"""
    <div class="pub-console-header">
        <div class="pub-console-eyebrow">▸ Consola de Marketing · Producto Activo</div>
        <div class="pub-console-product-name">{_nombre_activo}</div>
        <div class="pub-console-meta">
            <span class="pub-console-price">${_precio_activo:.2f}</span>
            {_marca_chip}
            <span class="pub-console-chip" style="color:var(--neon);">
                ✅ Copys generados
            </span>
        </div>
    </div>""", unsafe_allow_html=True)

    # Badge de plantillas globales
    _template_info()

    # ── 3 TABS ────────────────────────────────────────────────────────────────
    tab_ml, tab_ig, tab_wa = st.tabs(["📦 Mercado Libre", "📸 Instagram", "💬 WhatsApp"])

    # ── TAB 1: MERCADO LIBRE ──────────────────────────────────────────────────
    with tab_ml:
        st.markdown(f"""
        <div class="pub-titulo-box">
            <span class="tit-label">Título SEO optimizado (máx 60 caracteres)</span>
            <span class="tit-value">{_tit_ml}</span>
            <span class="tit-chars {_chars_cls}">{_chars}/60 caracteres</span>
        </div>""", unsafe_allow_html=True)

        st.markdown(
            '<span style="font-family:var(--font-mono);font-size:0.60rem;'
            'letter-spacing:2px;text-transform:uppercase;color:var(--muted);">'
            '▸ Descripción completa — <span style="color:var(--neon);">incluye título · copia todo de una vez</span></span>',
            unsafe_allow_html=True,
        )

        _render_copy_block(
            texto=_desc_ml,
            canal_label="📦 MERCADOLIBRE",
            canal_class="badge-ml",
            key_ta="ta_copy_ml",
            height=280,
        )

    # ── TAB 2: INSTAGRAM ──────────────────────────────────────────────────────
    with tab_ig:
        _render_copy_block(
            texto=_copy_ig_data,
            canal_label="📸 INSTAGRAM",
            canal_class="badge-ig",
            key_ta="ta_copy_ig",
            height=240,
        )

        st.markdown(
            '<span style="font-family:var(--font-mono);font-size:0.60rem;'
            'letter-spacing:2px;text-transform:uppercase;color:var(--muted);">'
            '▸ Hashtags (editables)</span>',
            unsafe_allow_html=True,
        )
        st.text_input(
            "Hashtags",
            value=_HASHTAGS_IG,
            key="ig_hashtags_edit",
            label_visibility="collapsed",
        )

    # ── TAB 3: WHATSAPP ───────────────────────────────────────────────────────
    with tab_wa:
        _render_copy_block(
            texto=_copy_wa_data,
            canal_label="💬 WHATSAPP",
            canal_class="badge-wa",
            key_ta="ta_copy_wa",
            height=240,
        )

    # ── Estudio Visual disponible siempre que haya copys generados ────────────
    st.markdown(
        '<hr style="border:none;border-top:1px solid rgba(184,150,62,0.12);margin:1.5rem 0 0.5rem 0">',
        unsafe_allow_html=True,
    )
    _render_estudio_visual(
        nombre_producto=_nombre_activo,
        precio_producto=_precio_activo,
        lista_productos=None,   # modo individual — sin selector de lote
        modo="individual",
    )


# ══════════════════════════════════════════════════════════════════════════════
# _render_estudio_visual — Alias al módulo Python puro procesador_estudio_visual.py
# La función completa vive en procesador_estudio_visual.py (importable sin exec()).
# Este alias mantiene la firma idéntica para no cambiar ninguna de las 2
# llamadas existentes en este archivo.
# ══════════════════════════════════════════════════════════════════════════════
def _render_estudio_visual(
    nombre_producto: str,
    precio_producto: float,
    lista_productos,        # list[dict] con claves nombre/precio, o None en modo individual
    modo: str = "individual",  # "individual" | "lote"
) -> None:
    """Delegación directa a procesador_estudio_visual.render_estudio_visual (módulo Python puro)."""
    render_estudio_visual(
        nombre_producto=nombre_producto,
        precio_producto=precio_producto,
        lista_productos=lista_productos,
        modo=modo,
    )



# ══════════════════════════════════════════════════════════════════════════════
# PUBLICACIONES MASIVAS — Genera ZIP con .txt por producto
# ══════════════════════════════════════════════════════════════════════════════
_hay_lote_para_masivo = (
    st.session_state.get("resultados_lote")
    and not st.session_state.get("_reseteando", False)
)

if _hay_lote_para_masivo:
    st.markdown("---")

    st.markdown("""
    <div class="pub-masivo-header">
        <span class="pub-masivo-ico">📦</span>
        <div>
            <div class="pub-masivo-title">Generación Masiva del Lote</div>
            <div class="pub-masivo-sub">
                Un .txt por producto con los 3 copys (ML · Instagram · WhatsApp) listos para copiar y pegar.
                Incluye métodos de pago, envío y garantía automáticamente.
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    res_lote = st.session_state.resultados_lote
    cat      = st.session_state.get("catalogo_df", None)

    # Construir lista de productos con marca + desc resueltas
    productos_pub = []
    for _r in res_lote:
        _n  = _r["nombre"]
        _pr = _r["precio_ml"]
        _m, _d = "", ""
        if cat is not None:
            _match_c = cat[cat["producto"].str.strip() == _n.strip()]
            if not _match_c.empty:
                _row_c = _match_c.iloc[0]
                _m = _safe_str(_row_c.get("marca", ""))
                _d = _safe_str(_row_c.get("descripcion", _row_c.get("descripcion_origen", "")))
        productos_pub.append({
            "nombre": _n, "marca": _m, "precio": _pr, "desc": _d,
            "tienda": _r.get("tienda", ""),
        })

    # ── Preview table con columna Preview (👁️) ────────────────────────────────
    st.markdown(
        f'<span style="font-family:var(--font-mono);font-size:0.62rem;letter-spacing:2px;'
        f'text-transform:uppercase;color:var(--muted);display:block;margin-bottom:8px;">'
        f'▸ {len(productos_pub)} producto(s) en el lote</span>',
        unsafe_allow_html=True,
    )

    # Cabecera HTML de tabla (sin columna interactiva — se añade con st.columns)
    _cols_tabla = st.columns([0.4, 3.5, 1.5, 1.2, 1.8, 0.8])
    _hdrs = ["#", "Producto", "Marca", "Precio ML", "Descripción", "Preview"]
    _hdr_styles = [
        "color:var(--muted);font-family:var(--font-mono);font-size:0.68rem;letter-spacing:1px;text-transform:uppercase;",
        "color:var(--muted);font-family:var(--font-mono);font-size:0.68rem;letter-spacing:1px;text-transform:uppercase;",
        "color:var(--muted);font-family:var(--font-mono);font-size:0.68rem;letter-spacing:1px;text-transform:uppercase;",
        "color:var(--muted);font-family:var(--font-mono);font-size:0.68rem;letter-spacing:1px;text-transform:uppercase;",
        "color:var(--muted);font-family:var(--font-mono);font-size:0.68rem;letter-spacing:1px;text-transform:uppercase;",
        "color:var(--gold);font-family:var(--font-mono);font-size:0.68rem;letter-spacing:1px;text-transform:uppercase;",
    ]
    for _c, _h, _s in zip(_cols_tabla, _hdrs, _hdr_styles):
        _c.markdown(f'<span style="{_s}">{_h}</span>', unsafe_allow_html=True)

    st.markdown('<hr style="border:none;border-top:1px solid rgba(184,150,62,0.12);margin:2px 0 4px 0">', unsafe_allow_html=True)

    # ── Dialog de preview individual ──────────────────────────────────────────
    @st.dialog("👁️ Preview de Publicación", width="large")
    def _modal_preview_item(prod: dict):
        _tb_m = generar_titulo(prod["nombre"], prod["marca"], prod["desc"])
        _tm, _dm = _copy_mercadolibre(_tb_m, prod["precio"], prod["desc"], prod["marca"])
        _ci      = _copy_instagram(_tb_m, prod["precio"], prod["desc"])
        _cw      = _copy_whatsapp(_tb_m, prod["precio"], prod["desc"])

        st.markdown(
            f'<p style="font-family:\'Syne\',sans-serif;font-size:1.1rem;font-weight:700;'
            f'color:var(--text);margin:0 0 4px 0;">{prod["nombre"]}</p>'
            f'<span style="font-family:var(--font-mono);font-size:0.65rem;color:var(--gold);">'
            f'${prod["precio"]:.2f} · {prod["marca"] or "Sin marca"}</span>',
            unsafe_allow_html=True,
        )
        st.markdown('<hr style="border:none;border-top:1px solid rgba(184,150,62,0.15);margin:10px 0">', unsafe_allow_html=True)

        _tab_m, _tab_i, _tab_w = st.tabs(["🟡 MercadoLibre", "📸 Instagram", "💬 WhatsApp"])
        with _tab_m:
            st.markdown(
                f'<span style="font-family:var(--font-mono);font-size:0.60rem;color:var(--muted);'
                f'letter-spacing:2px;text-transform:uppercase;">Título generado</span>',
                unsafe_allow_html=True,
            )
            st.info(f"**{_tm}** `{len(_tm)} chars`")
            st.markdown(
                f'<span style="font-family:var(--font-mono);font-size:0.60rem;color:var(--muted);'
                f'letter-spacing:2px;text-transform:uppercase;display:block;margin:8px 0 4px;">Descripción completa</span>',
                unsafe_allow_html=True,
            )
            st.code(_dm, language=None)
        with _tab_i:
            st.code(_ci, language=None)
        with _tab_w:
            st.code(_cw, language=None)

    # ── Filas de tabla con columnas Streamlit ─────────────────────────────────
    for _i, _p in enumerate(productos_pub, 1):
        _tiene_d  = "✅ Con desc."  if _p["desc"] else "⚠️ Sin desc."
        _desc_col = "color:var(--neon)" if _p["desc"] else "color:var(--yellow)"
        _row_cols = st.columns([0.4, 3.5, 1.5, 1.2, 1.8, 0.8])
        _row_cols[0].markdown(f'<span style="color:var(--muted);font-family:var(--font-mono);font-size:0.75rem;">{_i}</span>', unsafe_allow_html=True)
        _row_cols[1].markdown(f'<span style="font-family:var(--font-body);font-weight:500;font-size:0.85rem;">{_p["nombre"]}</span>', unsafe_allow_html=True)
        _row_cols[2].markdown(f'<span style="color:var(--muted);font-family:var(--font-body);font-size:0.82rem;">{_p["marca"] or "—"}</span>', unsafe_allow_html=True)
        _row_cols[3].markdown(f'<span style="font-family:var(--font-mono);color:var(--gold);font-weight:700;">${_p["precio"]:.2f}</span>', unsafe_allow_html=True)
        _row_cols[4].markdown(f'<span style="font-size:0.78rem;font-family:var(--font-body);{_desc_col}">{_tiene_d}</span>', unsafe_allow_html=True)
        if _row_cols[5].button("👁️", key=f"prev_item_{_i}", help=f"Preview copys de: {_p['nombre']}"):
            _modal_preview_item(_p)

    st.markdown("<br>", unsafe_allow_html=True)
    # ── Estudio Visual en modo lote ───────────────────────────────────────────
    _render_estudio_visual(
        nombre_producto=st.session_state.get("_pub_nombre", ""),
        precio_producto=float(st.session_state.get("_pub_precio", 0.00)),
        lista_productos=productos_pub,
        modo="lote",
    )


 
    # ── Espacio de separación antes de descripciones temporales ───────────────
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Descripciones temporales para productos sin desc ──────────────────────
    _desc_temporales = st.session_state.get("_desc_temporales", {})
    _hay_sin_desc    = False

    for _idx_p, _p in enumerate(productos_pub):
        if not _p["desc"]:
            _hay_sin_desc    = True
            _nombre_sin_desc = _p["nombre"]
            st.markdown(f"""
            <div class="pub-nodesc-card">
                <div class="pub-nodesc-title">⚠️ Sin descripción — {_nombre_sin_desc}</div>
                <div class="pub-nodesc-desc">
                    Añade la descripción temporalmente para mejorar el copy generado.
                </div>
            </div>""", unsafe_allow_html=True)

            _key_ta   = f"lote_desc_tmp_idx{_idx_p}"
            _desc_tmp = st.text_area(
                f"Descripción temporal para «{_nombre_sin_desc}»",
                value=_desc_temporales.get(f"idx{_idx_p}_{_nombre_sin_desc}", ""),
                placeholder="Pega aquí la descripción del producto desde la tienda origen...",
                height=100,
                key=_key_ta,
            )
            if _desc_tmp:
                _desc_temporales[f"idx{_idx_p}_{_nombre_sin_desc}"] = _desc_tmp
                _p["desc"] = _desc_tmp

    if _hay_sin_desc:
        st.session_state["_desc_temporales"] = _desc_temporales

    st.markdown('<hr style="border:none;border-top:1px solid rgba(184,150,62,0.1);margin:0.2rem 0 1rem 0">', unsafe_allow_html=True)

    # ── Trigger masivo (desde topbar) ─────────────────────────────────────────
    _trigger_masivo = st.session_state.pop("_trigger_masivo", False)

    # ── Botón de generación ZIP ───────────────────────────────────────────────
    _btn_generar_zip = st.button(
        "📦  Generar Pack de Publicaciones Masivas (ZIP)",
        use_container_width=True,
        key="btn_generar_zip",
    )

    if _btn_generar_zip or _trigger_masivo:
        import zipfile, io, re as _re

        _zip_buffer         = io.BytesIO()
        _archivos_generados = []

        with zipfile.ZipFile(_zip_buffer, "w", zipfile.ZIP_DEFLATED) as _zf:
            for _p in productos_pub:
                _tb      = generar_titulo(_p["nombre"], _p["marca"], _p["desc"])
                _tm, _dm = _copy_mercadolibre(_tb, _p["precio"], _p["desc"], _p["marca"])
                _ci      = _copy_instagram(_tb, _p["precio"], _p["desc"])
                _cw      = _copy_whatsapp(_tb, _p["precio"], _p["desc"])

                _sep = "═" * 55
                _contenido = f"""{_sep}
{_p["nombre"].upper()}
{_sep}

━━━ MERCADOLIBRE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TÍTULO: {_tm}

- - - - - - - - - - - - - - - - - - - - - - - - - - -

{_dm}

━━━ INSTAGRAM ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{_ci}

━━━ WHATSAPP ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{_cw}

{_sep}
Generado por ADALIMPORT · Precio ML: ${_p["precio"]:.2f}
{_sep}
"""
                _nombre_arch = _re.sub(r'[^a-zA-Z0-9_\- ]', '', _p["nombre"]).strip()
                _nombre_arch = _nombre_arch.replace(" ", "_")[:50]
                _zf.writestr(f"{_nombre_arch}.txt", _contenido.encode("utf-8"))
                _archivos_generados.append(_nombre_arch)

        _zip_buffer.seek(0)
        st.session_state["_zip_listo"]      = _zip_buffer.getvalue()
        st.session_state["_zip_n_archivos"] = len(_archivos_generados)
        st.rerun()

    # ── Franja de éxito unificada — persiste tras rerun ───────────────────────
    if st.session_state.get("_zip_listo") is not None:
        _n_zip = st.session_state["_zip_n_archivos"]

        # Fila única: mensaje + 2 botones perfectamente alineados
        _col_msg, _col_dl, _col_home = st.columns([3.2, 1.2, 1.2])

        with _col_msg:
            st.markdown(
                f'<div style="background:rgba(0,230,118,0.08);border:1px solid rgba(0,230,118,0.32);'
                f'border-radius:10px;padding:12px 16px;display:flex;align-items:center;gap:10px;">'
                f'<span style="font-size:1.25rem;line-height:1;">✅</span>'
                f'<div>'
                f'<span style="font-family:\'Syne\',sans-serif;font-weight:700;font-size:0.92rem;'
                f'color:var(--neon);display:block;line-height:1.2;">Pack de Publicaciones listo</span>'
                f'<span style="font-family:var(--font-mono);font-size:0.62rem;color:rgba(0,230,118,0.55);'
                f'display:block;margin-top:3px;">{_n_zip} archivo(s) · ML · Instagram · WhatsApp</span>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

        with _col_dl:
            st.download_button(
                label="⬇️  Descargar ZIP",
                data=st.session_state["_zip_listo"],
                file_name="ADALIMPORT_publicaciones.zip",
                mime="application/zip",
                use_container_width=True,
                key="btn_descarga_zip",
            )

        with _col_home:
            if st.button(
                "🏠 Volver al Inicio",
                key="btn_home_publicaciones",
                use_container_width=True,
                type="secondary",
                help="Limpia todo y regresa a la pantalla de selección de courier",
            ):
                st.session_state.pop("_zip_listo",      None)
                st.session_state.pop("_zip_n_archivos", None)
                _resetear_home()
                st.session_state["pagina_activa"] = "lote"
                st.rerun()

        st.markdown(
            '<p style="font-family:\'Inter\',sans-serif;font-size:0.78rem;'
            'color:var(--muted);margin:6px 0 0 2px;">'
            'Ciclo completado. ¿Deseas procesar un nuevo lote?</p>',
            unsafe_allow_html=True,
        )