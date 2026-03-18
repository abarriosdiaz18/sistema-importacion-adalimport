import streamlit as st


def aplicar_estilos():
    st.markdown("""
<style>
/* ══════════════════════════════════════════════════════════════════════════════
   ADALIMPORT — Design System v2.0
   Tipografía unificada + Identidad Navy/Oro/Verde Neón
   Fuentes: Syne (display) · Inter (body) · DM Mono (numeric)
══════════════════════════════════════════════════════════════════════════════ */
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300&family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Token Map ──────────────────────────────────────────────────────────────── */
:root {
    /* Brand */
    --gold:        #B8963E;
    --gold-lt:     #d4aa55;
    --gold-dk:     #8a6e2a;
    --neon:        #00E676;
    --neon-dk:     #00b85a;

    /* Background scale — negro profundo con tinte azul apenas visible */
    --navy:        #05090f;
    --navy-md:     #080e1a;
    --navy-lt:     #0d1424;

    /* Borders — sutiles, finos */
    --border:      #141e30;
    --border-lt:   #1c2a42;

    /* Text scale */
    --text:        #e2e8f0;
    --text-muted:  #94a3b8;
    --muted:       #4a5568;

    /* Semantic */
    --green:       #4ade80;
    --yellow:      #FFD600;
    --red:         #f87171;
    --orange:      #fb923c;
    --blue:        #60a5fa;

    /* Typography */
    --font-display: 'Syne', sans-serif;
    --font-body:    'Inter', sans-serif;
    --font-mono:    'DM Mono', monospace;
}

/* ══════════════════════════════════════════════════════════════════════════════
   TIPOGRAFÍA GLOBAL — Herencia Forzada
══════════════════════════════════════════════════════════════════════════════ */

/* Base: Inter para todo el cuerpo */
html, body,
.stApp, .main {
    font-family: var(--font-body) !important;
    background-color: var(--navy) !important;
}

/* Solo forzar background en los contenedores principales de Streamlit */
.stApp > div,
.main > div,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > section.main,
[data-testid="stMain"] {
    background-color: var(--navy) !important;
}

/* Color de texto base — sin afectar backgrounds */
body, .stApp *, .main * {
    color: var(--text);
}

/* ── H1 / Títulos Primarios: Syne 800, Blanco ───────────────────────────────
   El título principal del sistema es BLANCO en negrita (estilo bienvenida).
   El color Oro (#B8963E) se reserva únicamente para la clase .ada-title y
   para elementos de identidad de marca (logo, badges, accents).
   Aplicado a: st.title(), st.markdown con <h1>
────────────────────────────────────────────────────────────────────────────── */
h1,
.stApp h1,
[data-testid="stHeadingWithActionElements"] h1,
[data-testid="stMarkdownContainer"] h1 {
    font-family: var(--font-display) !important;
    font-weight: 800 !important;
    font-size: 2.5rem !important;
    color: var(--text) !important;
    letter-spacing: -0.5px !important;
    line-height: 1.15 !important;
    margin-bottom: 0.5rem !important;
}

/* ── H2 / Subtítulos: Syne 600, Verde Neón (éxito) o Blanco ─────────────────
   Aplicado a: st.subheader(), .h2-ada, st.markdown con <h2>
────────────────────────────────────────────────────────────────────────────── */
h2,
.stApp h2,
[data-testid="stHeadingWithActionElements"] h2,
[data-testid="stMarkdownContainer"] h2 {
    font-family: var(--font-display) !important;
    font-weight: 600 !important;
    font-size: 1.5rem !important;
    color: var(--neon) !important;
    letter-spacing: 0.5px !important;
    line-height: 1.25 !important;
}

/* ── H3 / Subtítulos de Sección: Syne 600, Blanco ───────────────────────────
   Aplicado a: st.markdown con <h3>
────────────────────────────────────────────────────────────────────────────── */
h3,
.stApp h3,
[data-testid="stHeadingWithActionElements"] h3,
[data-testid="stMarkdownContainer"] h3 {
    font-family: var(--font-display) !important;
    font-weight: 600 !important;
    font-size: 1.15rem !important;
    color: var(--text) !important;
    letter-spacing: 0.3px !important;
}

/* ── Párrafos y texto base ───────────────────────────────────────────────────*/
p,
[data-testid="stMarkdownContainer"] p {
    font-family: var(--font-body) !important;
    font-size: 0.9rem !important;
    line-height: 1.6 !important;
    color: var(--text-muted) !important;
}

/* ── Datos Numéricos / Monetarios: DM Mono ───────────────────────────────────
   Clases utilitarias + inputs + tablas de datos
────────────────────────────────────────────────────────────────────────────── */
.mono, .num, .currency,
code, pre, kbd,
[data-testid="stMetricValue"],
[data-testid="stDataFrame"] td,
[data-testid="stDataFrame"] th {
    font-family: var(--font-mono) !important;
}

/* Anular el background por defecto de <code> en contexto normal */
[data-testid="stMarkdownContainer"] code {
    background: rgba(184,150,62,0.08) !important;
    border: 1px solid rgba(184,150,62,0.2) !important;
    border-radius: 4px !important;
    padding: 1px 5px !important;
    font-family: var(--font-mono) !important;
    font-size: 0.82em !important;
    color: var(--gold-lt) !important;
}

/* ══════════════════════════════════════════════════════════════════════════════
   CLASES UTILITARIAS DE TIPOGRAFÍA
   Usar en st.markdown() para imponer jerarquía sin depender de Hx nativos
══════════════════════════════════════════════════════════════════════════════ */

/* Título de página — blanco bold por defecto */
.ada-title {
    font-family: var(--font-display) !important;
    font-size: 2.5rem !important;
    font-weight: 800 !important;
    color: var(--text) !important;
    letter-spacing: -0.5px !important;
    line-height: 1.15 !important;
    margin: 0 0 0.25rem 0 !important;
}

/* Título con acento dorado explícito (identidad de marca) */
.ada-title-gold {
    font-family: var(--font-display) !important;
    font-size: 2.5rem !important;
    font-weight: 800 !important;
    color: var(--gold) !important;
    letter-spacing: 1px !important;
    line-height: 1.15 !important;
    margin: 0 0 0.25rem 0 !important;
}

/* Subtítulo / Indicador de éxito (verde neón) */
.ada-subtitle {
    font-family: var(--font-display) !important;
    font-size: 1.5rem !important;
    font-weight: 600 !important;
    color: var(--neon) !important;
    letter-spacing: 0.5px !important;
    line-height: 1.25 !important;
    margin: 0 0 0.2rem 0 !important;
}

/* Subtítulo blanco para secciones neutras */
.ada-subtitle-white {
    font-family: var(--font-display) !important;
    font-size: 1.5rem !important;
    font-weight: 600 !important;
    color: var(--text) !important;
    letter-spacing: 0.3px !important;
    line-height: 1.25 !important;
}

/* Label de sección (estilo eyebrow) */
.ada-eyebrow {
    font-family: var(--font-mono) !important;
    font-size: 0.62rem !important;
    font-weight: 500 !important;
    letter-spacing: 3px !important;
    text-transform: uppercase !important;
    color: var(--muted) !important;
}

/* Valor monetario grande */
.ada-money {
    font-family: var(--font-mono) !important;
    font-size: 1.7rem !important;
    font-weight: 500 !important;
    line-height: 1 !important;
    color: var(--text) !important;
}
.ada-money-gold  { color: var(--gold) !important; }
.ada-money-green { color: var(--neon) !important; }
.ada-money-red   { color: var(--red)  !important; }

/* ══════════════════════════════════════════════════════════════════════════════
   OCULTAR BARRA NATIVA DE STREAMLIT MULTIPAGE + DECORACIONES
   La navegación en ADALIMPORT es 100% custom via _router.py
══════════════════════════════════════════════════════════════════════════════ */

/* Barra de navegación nativa (multipage) */
[data-testid="stSidebarNav"],
[data-testid="collapsedControl"],
header[data-testid="stHeader"],
div[data-testid="stDecoration"] {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    overflow: hidden !important;
}

/* Eliminar el padding-top que Streamlit agrega cuando hay header */
.main .block-container {
    padding-top: 1.5rem !important;
}

/* ══════════════════════════════════════════════════════════════════════════════
   SIDEBAR
══════════════════════════════════════════════════════════════════════════════ */
section[data-testid="stSidebar"] {
    background: var(--navy-md) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] > div:first-child,
section[data-testid="stSidebar"] [data-testid="stSidebarContent"],
section[data-testid="stSidebar"] .block-container,
section[data-testid="stSidebar"] > div > div:first-child {
    padding-top: 0 !important;
    margin-top: 0 !important;
}

/* Labels y texto en sidebar */
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span {
    font-family: var(--font-body) !important;
    color: var(--muted) !important;
    font-size: 0.78rem !important;
}
section[data-testid="stSidebar"] strong {
    font-family: var(--font-body) !important;
    color: var(--text) !important;
    font-size: 0.82rem !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
}

/* ── Logo ───────────────────────────────────────────────────────────────────── */
.ada-logo-wrap {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 18px 0 14px 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 18px;
}
.ada-logo-img {
    width: 58px; height: 58px;
    border-radius: 50%;
    background: #fff;
    padding: 5px;
    flex-shrink: 0;
    box-shadow: 0 0 0 2px rgba(184,150,62,0.35);
}
.ada-logo {
    font-family: var(--font-display) !important;
    font-size: 1.1rem;
    font-weight: 800;
    color: var(--gold) !important;
    letter-spacing: 2px;
    line-height: 1.1;
}
.ada-sub {
    font-family: var(--font-body) !important;
    font-size: 0.72rem;
    color: var(--gold);
    letter-spacing: 2.5px;
    text-transform: uppercase;
    margin-top: 2px;
    font-weight: 600;
    opacity: 0.85;
}

/* ══════════════════════════════════════════════════════════════════════════════
   KPI CARDS
══════════════════════════════════════════════════════════════════════════════ */
.kpi-card {
    background: var(--navy-lt);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.6rem;
}
.kpi-label {
    font-family: var(--font-mono) !important;
    font-size: 0.62rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 0.25rem;
}
.kpi-value {
    font-family: var(--font-mono) !important;
    font-size: 1.7rem;
    font-weight: 500;
    line-height: 1;
}
.kpi-green  { color: var(--green);  }
.kpi-yellow { color: var(--yellow); }
.kpi-red    { color: var(--red);    }
.kpi-white  { color: var(--text);   }
.kpi-gold   { color: var(--gold);   }
.kpi-neon   { color: var(--neon);   }

/* ── At-a-Glance KPI Header (Config Master) ─────────────────────────────────*/
.atag-banner {
    background: linear-gradient(135deg, var(--navy-md) 0%, var(--navy) 100%);
    border: 1px solid var(--border);
    border-top: 3px solid var(--gold);
    border-radius: 14px;
    padding: 1.2rem 1.6rem;
    margin-bottom: 1.6rem;
}
.atag-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
}
.atag-cell {
    text-align: center;
    padding: 0.8rem 0.5rem;
    background: rgba(15,24,41,0.7);
    border: 1px solid var(--border);
    border-radius: 10px;
    position: relative;
    overflow: hidden;
}
.atag-cell::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
}
.atag-cell.gold-accent::before  { background: var(--gold); }
.atag-cell.green-accent::before { background: var(--neon); }
.atag-cell.blue-accent::before  { background: var(--blue); }
.atag-cell.white-accent::before { background: var(--text-muted); }

.atag-icon  { font-size: 1.4rem; line-height: 1; margin-bottom: 4px; }
.atag-label {
    font-family: var(--font-mono);
    font-size: 0.58rem;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 6px;
}
.atag-value {
    font-family: var(--font-mono);
    font-size: 1.6rem;
    font-weight: 500;
    line-height: 1;
}
.atag-value.gold  { color: var(--gold); }
.atag-value.neon  { color: var(--neon); }
.atag-value.blue  { color: var(--blue); }
.atag-value.white { color: var(--text); }
.atag-sub {
    font-family: var(--font-mono);
    font-size: 0.65rem;
    color: var(--muted);
    margin-top: 4px;
    line-height: 1.3;
}

/* ══════════════════════════════════════════════════════════════════════════════
   TABLA DE RESULTADOS
══════════════════════════════════════════════════════════════════════════════ */
.res-table { width: 100%; border-collapse: collapse; margin-top: 0.8rem; }
.res-table th {
    font-family: var(--font-mono) !important;
    font-size: 0.6rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: var(--muted);
    padding: 0.55rem 0.8rem;
    border-bottom: 1px solid var(--border);
    background: rgba(184,150,62,0.04);
    text-align: left;
}
.res-table td {
    font-family: var(--font-body) !important;
    padding: 0.7rem 0.8rem;
    border-bottom: 1px solid rgba(26,37,64,0.8);
    font-size: 0.88rem;
}
.res-table td.mono-cell {
    font-family: var(--font-mono) !important;
}
.res-table tr:last-child td { border-bottom: none; }
.res-table tr:hover td { background: rgba(184,150,62,0.03); }
.badge-ok     { color: var(--green);  font-weight: 700; font-family: var(--font-mono) !important; font-size: 0.75rem; }
.badge-warn   { color: var(--yellow); font-weight: 700; font-family: var(--font-mono) !important; font-size: 0.75rem; }
.badge-bad    { color: var(--red);    font-weight: 700; font-family: var(--font-mono) !important; font-size: 0.75rem; }
.badge-inapto {
    color: #E65100;
    font-weight: 700;
    font-family: var(--font-mono) !important;
    font-size: 0.72rem;
    background: rgba(230, 81, 0, 0.10);
    border: 1px solid rgba(230, 81, 0, 0.35);
    border-radius: 4px;
    padding: 1px 5px;
}

/* ══════════════════════════════════════════════════════════════════════════════
   COMPONENTES ESPECÍFICOS DE PÁGINAS
══════════════════════════════════════════════════════════════════════════════ */

/* Precio ML validado (_validar.py) */
.precio-validado {
    background: linear-gradient(135deg, rgba(27,42,74,0.5), rgba(184,150,62,0.06));
    border: 1px solid rgba(184,150,62,0.35);
    border-radius: 10px;
    padding: 1rem 1.4rem;
    margin: 0.5rem 0;
}
.precio-validado .label {
    font-family: var(--font-mono) !important;
    font-size: 0.62rem; color: var(--muted);
    text-transform: uppercase; letter-spacing: 2px;
}
.precio-validado .valor {
    font-family: var(--font-mono) !important;
    font-size: 1.4rem; color: var(--gold); font-weight: 500;
}
.precio-validado .fuente {
    font-family: var(--font-body) !important;
    font-size: 0.7rem; color: #3a4a6a; margin-top: 0.3rem;
}

/* Publicación (_publicaciones.py) */
.pub-box {
    background: var(--navy-lt);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.2rem;
    margin-top: 0.8rem;
    font-size: 0.85rem;
    white-space: pre-wrap;
    font-family: var(--font-mono) !important;
    color: #94a3b8;
    max-height: 300px;
    overflow-y: auto;
    line-height: 1.6;
}

/* Section title eyebrow */
.section-title {
    font-family: var(--font-mono) !important;
    font-size: 0.62rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--muted);
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.5rem;
    margin: 1.5rem 0 1rem 0;
}

/* ══════════════════════════════════════════════════════════════════════════════
   INPUTS STREAMLIT & CHECKBOXES
══════════════════════════════════════════════════════════════════════════════ */
div[data-testid="stNumberInput"] input,
div[data-testid="stTextInput"] input,
div[data-testid="stSelectbox"] select,
textarea {
    background: var(--navy-lt) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 6px !important;
    font-family: var(--font-mono) !important;
    font-size: 0.88rem !important;
    outline: none !important;
}

/* FIX: Asesinar el focus ring nativo (rojo/naranja) en todos los niveles de DOM */
*:focus, *:focus-visible {
    outline: none !important;
}

div[data-testid="stNumberInput"] div[data-baseweb="input"]:focus-within,
div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within,
div[data-testid="stSelectbox"] div[data-baseweb="select"]:focus-within,
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within,
div[data-baseweb="input"] > div:focus-within,
div[data-baseweb="base-input"] > input:focus {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 1px var(--gold) !important;
    outline: none !important;
}

/* Checkbox activo a Verde Neón */
div[data-testid="stCheckbox"] div[data-baseweb="checkbox"] input:checked + div {
    background-color: var(--neon) !important;
    border-color: var(--neon) !important;
}
div[data-testid="stCheckbox"] div[data-baseweb="checkbox"] input:checked + div svg {
    fill: #05090f !important;
    color: #05090f !important;
}

/* Labels de inputs */
div[data-testid="stNumberInput"] label,
div[data-testid="stTextInput"] label,
div[data-testid="stSelectbox"] label,
div[data-testid="stSlider"] label,
div[data-testid="stTextArea"] label,
div[data-testid="stCheckbox"] label p {
    font-family: var(--font-body) !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    color: var(--text-muted) !important;
    letter-spacing: 0.3px !important;
}

/* ══════════════════════════════════════════════════════════════════════════════
   BOTONES — Dorado sólido premium, glow en hover
══════════════════════════════════════════════════════════════════════════════ */

/* Botón por defecto y PRIMARIO (Fondo dorado, texto ultra oscuro) */
.stButton > button,
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--gold) 0%, var(--gold-lt) 100%) !important;
    color: #0a0a0a !important;
    font-family: var(--font-display) !important;
    font-weight: 800 !important;
    font-size: 0.72rem !important;
    letter-spacing: 2px !important;
    border: 1px solid var(--gold) !important;
    border-radius: 8px !important;
    padding: 0.65rem 1.4rem !important;
    width: 100% !important;
    text-transform: uppercase !important;
    transition: all 0.2s ease !important;
    box-shadow:
        0 2px 12px rgba(184,150,62,0.20),
        inset 0 1px 0 rgba(255,255,255,0.12) !important;
}

/* FIX CRÍTICO: Forzar texto negro en cualquier elemento interno del botón primario */
.stButton > button[kind="primary"] *,
.stButton > button[kind="primary"] p,
.stButton > button[kind="primary"] div {
    color: #0a0a0a !important;
}

.stButton > button:hover,
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, var(--gold-lt) 0%, #e8c060 100%) !important;
    transform: translateY(-1px) !important;
    box-shadow:
        0 6px 24px rgba(184,150,62,0.40),
        0 0 0 1px rgba(184,150,62,0.5),
        inset 0 1px 0 rgba(255,255,255,0.18) !important;
    color: #000000 !important;
}

/* Mantener el negro profundo también en el hover */
.stButton > button[kind="primary"]:hover *,
.stButton > button[kind="primary"]:hover p {
    color: #000000 !important;
}

.stButton > button:active,
.stButton > button[kind="primary"]:active {
    transform: translateY(0) !important;
    box-shadow: 0 2px 8px rgba(184,150,62,0.20) !important;
}

/* Botón secundario (type="secondary") — borde dorado, fondo transparente */
.stButton > button[kind="secondary"] {
    background: transparent !important;
    color: var(--gold) !important;
    border: 1px solid rgba(184,150,62,0.55) !important;
    box-shadow: none !important;
}

/* FIX: Forzar color dorado en el texto interno del botón secundario */
.stButton > button[kind="secondary"] *,
.stButton > button[kind="secondary"] p {
    color: var(--gold) !important;
}

.stButton > button[kind="secondary"]:hover {
    background: rgba(184,150,62,0.08) !important;
    border-color: var(--gold) !important;
    box-shadow: 0 0 12px rgba(184,150,62,0.15) !important;
    transform: none !important;
    color: var(--gold-lt) !important;
}

.stButton > button[kind="secondary"]:hover *,
.stButton > button[kind="secondary"]:hover p {
    color: var(--gold-lt) !important;
}

/* ══════════════════════════════════════════════════════════════════════════════
   TABS
══════════════════════════════════════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
    background: var(--navy-md) !important;
    border-bottom: 1px solid var(--border) !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: var(--font-mono) !important;
    font-size: 0.72rem !important;
    letter-spacing: 1px !important;
    color: var(--muted) !important;
    background: transparent !important;
    padding: 0.8rem 1.2rem !important;
}
.stTabs [aria-selected="true"] {
    color: var(--gold) !important;
    border-bottom: 2px solid var(--gold) !important;
}
.stTabs [data-baseweb="tab-highlight"] { background: var(--gold) !important; }

/* ══════════════════════════════════════════════════════════════════════════════
   RADIO → Toggle Pills
══════════════════════════════════════════════════════════════════════════════ */
div[data-testid="stRadio"] > label {
    font-family: var(--font-mono) !important;
    font-size: 0.62rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: var(--muted) !important;
    margin-bottom: 6px !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] {
    display: flex !important;
    flex-direction: row !important;
    gap: 3px !important;
    background: rgba(7, 13, 26, 0.8) !important;
    border: 1px solid var(--border) !important;
    border-radius: 9px !important;
    padding: 3px !important;
    width: fit-content !important;
    flex-wrap: nowrap !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] > label {
    display: flex !important;
    align-items: center !important;
    gap: 0 !important;
    padding: 6px 16px !important;
    border-radius: 6px !important;
    cursor: pointer !important;
    font-family: var(--font-body) !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.03em !important;
    color: #38485e !important;
    background: transparent !important;
    border: 1px solid transparent !important;
    transition: color 0.15s ease, background 0.15s ease, border-color 0.15s ease !important;
    white-space: nowrap !important;
    user-select: none !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] > label:hover {
    color: #6a7d92 !important;
    background: rgba(15, 24, 41, 0.7) !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) {
    background: var(--navy-lt) !important;
    border-color: rgba(184, 150, 62, 0.45) !important;
    color: var(--gold-lt) !important;
    box-shadow:
        0 0 0 1px rgba(184, 150, 62, 0.10),
        0 2px 8px rgba(0, 0, 0, 0.4) !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child {
    display: none !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] > label > div:last-child p {
    font-size: 0.78rem !important;
    margin: 0 !important;
    line-height: 1 !important;
    color: inherit !important;
    font-family: inherit !important;
}

/* ══════════════════════════════════════════════════════════════════════════════
   EXPANDERS / ACCORDIONS
══════════════════════════════════════════════════════════════════════════════ */
div[data-testid="stExpander"] {
    background: var(--navy-lt) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
}
div[data-testid="stExpander"]:hover {
    border-color: var(--gold) !important;
}
div[data-testid="stExpander"] summary {
    font-family: var(--font-body) !important;
    color: var(--muted) !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
}
div[data-testid="stExpander"] summary:hover {
    color: var(--gold) !important;
}

/* ══════════════════════════════════════════════════════════════════════════════
   ALERTS / INFO BOXES
══════════════════════════════════════════════════════════════════════════════ */
div[data-testid="stInfo"] {
    background: rgba(27,42,74,0.4) !important;
    border: 1px solid var(--border-lt) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-family: var(--font-body) !important;
}
div[data-testid="stWarning"] {
    background: rgba(184,150,62,0.08) !important;
    border: 1px solid rgba(184,150,62,0.3) !important;
    border-radius: 8px !important;
    font-family: var(--font-body) !important;
}
div[data-testid="stError"] {
    background: rgba(248,113,113,0.08) !important;
    border: 1px solid rgba(248,113,113,0.25) !important;
    border-radius: 8px !important;
    font-family: var(--font-body) !important;
}
div[data-testid="stSuccess"] {
    background: rgba(74,222,128,0.06) !important;
    border: 1px solid rgba(74,222,128,0.25) !important;
    border-radius: 8px !important;
    font-family: var(--font-body) !important;
}

/* ══════════════════════════════════════════════════════════════════════════════
   METRICS (st.metric)
══════════════════════════════════════════════════════════════════════════════ */
[data-testid="stMetricLabel"] {
    font-family: var(--font-mono) !important;
    font-size: 0.62rem !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    color: var(--muted) !important;
}
[data-testid="stMetricValue"] {
    font-family: var(--font-mono) !important;
    font-size: 1.6rem !important;
    font-weight: 500 !important;
    color: var(--text) !important;
}
[data-testid="stMetricDelta"] {
    font-family: var(--font-mono) !important;
    font-size: 0.75rem !important;
}

/* ══════════════════════════════════════════════════════════════════════════════
   DATAFRAME
══════════════════════════════════════════════════════════════════════════════ */
div[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
}
div[data-testid="stDataFrame"] th {
    font-family: var(--font-mono) !important;
    font-size: 0.7rem !important;
    letter-spacing: 1px !important;
    background: rgba(184,150,62,0.04) !important;
    color: var(--muted) !important;
}
div[data-testid="stDataFrame"] td {
    font-family: var(--font-mono) !important;
    font-size: 0.82rem !important;
}

/* ══════════════════════════════════════════════════════════════════════════════
   SELECTBOX
══════════════════════════════════════════════════════════════════════════════ */
div[data-testid="stSelectbox"] > div {
    background: var(--navy-lt) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    font-family: var(--font-mono) !important;
}

/* ══════════════════════════════════════════════════════════════════════════════
   SCROLLBARS
══════════════════════════════════════════════════════════════════════════════ */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--navy); }
::-webkit-scrollbar-thumb { background: var(--border-lt); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--gold); }

/* ══════════════════════════════════════════════════════════════════════════════
   CONFIG MASTER — CSS exclusivo
══════════════════════════════════════════════════════════════════════════════ */
.cfg-section-title {
    font-family: var(--font-display) !important;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--gold);
    border-bottom: 1px solid var(--border);
    padding-bottom: 6px;
    margin: 0 0 14px 0;
}
.cfg-card {
    background: var(--navy-md);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.2rem 1.4rem 1rem 1.4rem;
    margin-bottom: 1.2rem;
    position: relative;
}
.cfg-card-accent-gold  { border-left: 3px solid var(--gold)  !important; }
.cfg-card-accent-green { border-left: 3px solid var(--neon)  !important; }
.cfg-card-accent-blue  { border-left: 3px solid var(--blue)  !important; }
.cfg-badge {
    display: inline-block;
    font-family: var(--font-mono) !important;
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    padding: 2px 9px;
    border-radius: 20px;
    margin-left: 8px;
    vertical-align: middle;
}
.cfg-badge-active   { background:#003820; color:var(--neon); border:1px solid var(--neon); }
.cfg-badge-modified { background:#1a0f00; color:var(--gold); border:1px solid var(--gold); }
.cfg-metric-row {
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
    margin-top: 0.4rem;
}
.cfg-metric-chip {
    font-family: var(--font-mono) !important;
    font-size: 0.72rem;
    background: var(--navy-lt);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 4px 10px;
    color: var(--muted);
}
.cfg-metric-chip b { color: var(--text); }
.cfg-alert-change {
    background: #0d1a0d;
    border: 1px solid var(--neon);
    border-radius: 8px;
    padding: 0.6rem 1rem;
    font-family: var(--font-body) !important;
    font-size: 0.78rem;
    color: var(--neon);
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 8px;
}
.cfg-hero {
    background: linear-gradient(135deg, var(--navy-md) 0%, var(--navy) 100%);
    border: 1px solid var(--border);
    border-top: 3px solid var(--gold);
    border-radius: 14px;
    padding: 1.4rem 1.8rem;
    margin-bottom: 1.8rem;
    display: flex;
    align-items: center;
    gap: 16px;
}
.cfg-hero-icon {
    font-size: 2.4rem;
    line-height: 1;
    filter: drop-shadow(0 0 12px rgba(184,150,62,0.5));
}
.cfg-hero-title {
    font-family: var(--font-display) !important;
    font-size: 1.35rem;
    font-weight: 800;
    color: var(--gold);
    letter-spacing: 1px;
    margin: 0;
    line-height: 1.2;
}
.cfg-hero-sub {
    font-family: var(--font-mono) !important;
    font-size: 0.75rem;
    color: var(--muted);
    margin: 2px 0 0 0;
    letter-spacing: 1px;
}
.cfg-sep {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border) 30%, var(--border) 70%, transparent);
    margin: 1.4rem 0;
}
div[data-testid="stButton"]:has(button[key="cfg_btn_apply"]) button {
    background: linear-gradient(135deg, var(--neon), var(--neon-dk)) !important;
    color: #000 !important;
    font-weight: 800 !important;
    font-size: 0.85rem !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    border: none !important;
    border-radius: 10px !important;
    box-shadow: 0 0 20px rgba(0,230,118,0.3) !important;
}
div[data-testid="stButton"]:has(button[key="cfg_btn_reset"]) button {
    background: transparent !important;
    color: var(--muted) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    font-size: 0.75rem !important;
}

/* ══════════════════════════════════════════════════════════════════════════════
   PAGE LOADING OVERLAY — Transiciones suaves entre páginas
   Spinner dorado sobre fondo navy semitransparente.
   SEGURO: Inicia OCULTO (.ada-loaded). JS lo muestra al clic en nav.
   Auto-dismiss via CSS animation finita como fallback de seguridad.
══════════════════════════════════════════════════════════════════════════════ */
.ada-page-loading {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(5, 9, 15, 0.65);
    backdrop-filter: blur(4px);
    -webkit-backdrop-filter: blur(4px);
    opacity: 0;
    visibility: hidden;
    transition: opacity 0.3s ease, visibility 0.3s ease;
    pointer-events: none;
}

/* Estado activo — overlay visible (activado por JS al clic en nav) */
.ada-page-loading.ada-showing {
    opacity: 1;
    visibility: visible;
}

/* Estado cargado / default — overlay oculto */
.ada-page-loading.ada-loaded {
    opacity: 0;
    visibility: hidden;
}

/* Spinner dorado animado */
.ada-loader-spinner {
    width: 36px;
    height: 36px;
    border: 3px solid rgba(184, 150, 62, 0.15);
    border-top: 3px solid var(--gold, #B8963E);
    border-radius: 50%;
    animation: ada-spin 0.8s cubic-bezier(0.4, 0, 0.2, 1) infinite;
    box-shadow: 0 0 20px rgba(184, 150, 62, 0.2);
}

@keyframes ada-spin {
    0%   { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* ══════════════════════════════════════════════════════════════════════════════
   TOAST NOTIFICATIONS — Sistema premium de notificaciones
   Posición fija esquina inferior derecha · Auto-dismiss via CSS animation
   Tipos: success (neón), error (rojo), warning (oro), info (azul)
   NO desplazan el contenido · Tipografía DM Mono / Inter
   NUNCA texto negro sobre fondo oscuro
══════════════════════════════════════════════════════════════════════════════ */

/* Keyframe compartido: slide desde la derecha → pausa → fade-out */
@keyframes ada-toast-life {
    0%   { opacity: 0; transform: translateX(32px); }
    10%  { opacity: 1; transform: translateX(0);    }
    75%  { opacity: 1; transform: translateX(0);    }
    100% { opacity: 0; transform: translateX(8px);  }
}

/* Label eyebrow (tipo en mayúsculas) */
[id^="ada_toast_"] .ada-toast-label {
    font-family: var(--font-mono) !important;
    font-size: 0.58rem !important;
    font-weight: 500 !important;
    letter-spacing: 2.5px !important;
    text-transform: uppercase !important;
    line-height: 1 !important;
}

/* Mensaje principal */
[id^="ada_toast_"] .ada-toast-msg {
    font-family: var(--font-body) !important;
    font-size: 0.82rem !important;
    font-weight: 400 !important;
    color: var(--text) !important;
    line-height: 1.45 !important;
    word-break: break-word !important;
}
</style>
""", unsafe_allow_html=True)