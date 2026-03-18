# ═══════════════════════════════════════════════════════════════
#  ADALIMPORT — Generador de publicaciones
#  A partir de la descripción pegada de la tienda (en español),
#  genera título ML, descripción y copy para Instagram/WhatsApp.
# ═══════════════════════════════════════════════════════════════

import re

PALABRAS_PROHIBIDAS_ML = {
    'OFERTA', 'NUEVO', 'GRATIS', 'BARATO', 'DESCUENTO', 'FULL',
    'MEJOR', 'PRECIO', 'INCREIBLE', 'SUPER', 'MEGA', 'ULTRA'
}

# Límite de caracteres para procesar: evita O(n) sobre textos largos pegados desde tiendas.
# Un texto de 2000 chars cubre ~300 palabras — más que suficiente para extraer puntos clave.
_MAX_DESC_CHARS = 2000

# Patrones compilados una sola vez al importar el módulo (no en cada llamada)
_PATS_VALOR = re.compile(
    r'(\d+\s*(?:mah|mAh|wh|w|v|a|gb|mb|tb|kg|lb|g|mm|cm|in|ft)'
    r'|\d+\s*(?:unidades?|piezas?|pack|pk|count)'
    r'|\d+\s*(?:horas?|hrs?|días?|meses?|años?)'
    r'|\d+\s*(?:veces|ciclos|cargas?)'
    r'|recargabl\w*|importad\w*|original\w*|garantía|compatib\w*|incluye|pre.cargad\w*'
    r'|alto rendimiento|larga duración|uso prolongado|profesional'
    r'|intel|amd|nvidia|usb|hdmi|bluetooth|wifi)',
    re.IGNORECASE
)

_PATS_TITULO = re.compile(
    r'(\d+\s*(?:unidades?|pack|pk|piezas?)'
    r'|\d+\s*(?:mah|wh|gb|tb|g\b)'
    r'|\d+\s*(?:veces|ciclos)'
    r'|recargabl\w+'
    r'|pre.cargad\w+)',
    re.IGNORECASE
)

_SEP = re.compile(r'[.\n,;]+')


# ─── Extracción inteligente de puntos clave ──────────────────────
def extraer_puntos_clave(descripcion, max_puntos=6):
    """
    Extrae los puntos de venta más relevantes de la descripción.
    Prioriza: cantidades, medidas, especificaciones, beneficios.
    Optimizado: trunca la entrada a _MAX_DESC_CHARS y usa patrones precompilados.
    """
    if not descripcion or not descripcion.strip():
        return []

    # ── Truncar entrada para evitar procesamiento O(n) en textos muy largos ──
    texto = descripcion[:_MAX_DESC_CHARS]

    fragmentos = _SEP.split(texto)

    puntos_valor   = []
    puntos_normales = []

    for frag in fragmentos:
        frag = frag.strip().rstrip('.')
        if len(frag) < 8:
            continue
        if _PATS_VALOR.search(frag):
            puntos_valor.append(frag)
        else:
            puntos_normales.append(frag)

        # Corte temprano: si ya tenemos suficientes puntos de valor, no seguimos
        if len(puntos_valor) >= max_puntos:
            break

    todos = puntos_valor + puntos_normales
    return todos[:max_puntos]


# ─── Título ML ───────────────────────────────────────────────────
def generar_titulo(nombre, marca="", descripcion=""):
    """
    Genera título optimizado para ML: máx 60 caracteres.
    Usa nombre + marca + las palabras más relevantes de la descripción.
    """
    specs_titulo = []
    if descripcion:
        # Truncar y usar patrón compilado
        texto = descripcion[:_MAX_DESC_CHARS]
        for match in _PATS_TITULO.finditer(texto):
            specs_titulo.append(match.group(0).strip())
            if len(specs_titulo) >= 2:
                break

    partes = [nombre]
    if marca and marca.upper() not in nombre.upper():
        partes.append(marca)
    partes.extend(specs_titulo)
    texto = " ".join(partes).upper()

    # Eliminar duplicados manteniendo orden
    vistas, palabras_unicas = set(), []
    for palabra in texto.split():
        if palabra not in vistas:
            vistas.add(palabra)
            palabras_unicas.append(palabra)

    # Filtrar prohibidas
    palabras = [p for p in palabras_unicas if p not in PALABRAS_PROHIBIDAS_ML]
    titulo = " ".join(palabras)

    # Recortar a 60 caracteres sin cortar palabras
    if len(titulo) > 60:
        recorte = titulo[:60]
        ultimo_espacio = recorte.rfind(" ")
        titulo = recorte[:ultimo_espacio] if ultimo_espacio != -1 else recorte

    # Title case respetando siglas cortas
    palabras_final = []
    for palabra in titulo.split():
        if len(palabra) <= 4 and palabra.isalpha():
            palabras_final.append(palabra.upper())
        else:
            palabras_final.append(palabra.capitalize())

    return " ".join(palabras_final)


# ─── Descripción ML ──────────────────────────────────────────────
def generar_descripcion(titulo, precio, descripcion="", marca=""):
    """
    Genera descripción estructurada para ML a partir de la descripción original.
    """
    puntos = extraer_puntos_clave(descripcion, max_puntos=6)

    if puntos:
        ficha = "\n".join(f"• {p.capitalize()}" for p in puntos)
    else:
        ficha = f"• {titulo.upper()}\n• PRODUCTO NUEVO Y ORIGINAL 100%\n• IMPORTADO DIRECTAMENTE DE USA"

    desc = f"""✨ {titulo.upper()} ✨

Producto importado directamente de USA. Original y garantizado.

=========================================
📝 CARACTERÍSTICAS:
=========================================

{ficha}

=========================================
💰 PRECIO: ${precio:.2f}
=========================================

⚠️ Consultar disponibilidad antes de ofertar.
Respondemos a la brevedad posible.

=========================================
📍 ENTREGA Y ENVÍOS:
=========================================

Entrega personal en Caracas (San Bernardino).
Envíos nacionales vía MRW / ZOOM.
📦 El costo de envío corre por cuenta del comprador.

=========================================
💳 MÉTODOS DE PAGO:
=========================================

- Efectivo (USD / Bs)
- Pago Móvil / Transferencia
- Binance (USDT)
- PayPal

=========================================
🛡️ GARANTÍA:
=========================================

3 días por defectos de fábrica.
"""
    return desc


# ─── Copy Instagram / WhatsApp ───────────────────────────────────
def generar_copy_instagram(titulo, precio, descripcion=""):
    """
    Genera copy corto para Instagram/WhatsApp con los mejores puntos de venta.
    """
    puntos = extraer_puntos_clave(descripcion, max_puntos=3)
    bullets = "\n".join(f"✅ {p.capitalize()}" for p in puntos) if puntos else "✅ Original importado\n✅ Disponible en Caracas\n✅ Envíos a todo el país"

    copy = f"""🔥 {titulo} 🔥

{bullets}

💰 Precio: ${precio:.2f}

📍 Caracas · Envíos nacionales
📩 Escríbenos para apartar el tuyo

#ADALIMPORT #Venezuela #Caracas #ImportadoUSA"""
    return copy


# ─── PRUEBA ──────────────────────────────────────────────────────
if __name__ == "__main__":
    desc = """Pilas AA Energizer recargables, paquete de 4 unidades, 2000mAh.
    Vienen pre-cargadas listas para usar. Se recargan hasta 1000 veces.
    Mantienen carga por hasta 12 meses sin uso. Originales importadas de USA.
    Para controles, juguetes, cámaras y más."""

    titulo = generar_titulo("Pilas AA Energizer", "Energizer", desc)
    print(f"Título ({len(titulo)} chars): {titulo}")
    print("\n--- Descripción ML ---")
    print(generar_descripcion(titulo, 16.75, desc))
    print("\n--- Copy IG ---")
    print(generar_copy_instagram(titulo, 16.75, desc))
