# ═══════════════════════════════════════════════════════════════
#  ADALIMPORT — Configuración de costos y tarifas
# ═══════════════════════════════════════════════════════════════

# ─── COURIERS DISPONIBLES ───────────────────────────────────────
COURIERS = {
    "Un Solo Dolar": {
        "origenes":  ["us"],          # Solo opera desde USA
        "consolidado_dias": 21,       # Consolida por 21 días desde primer artículo
        "aereo": {
            "us": {"tarifa_lb": 6.99,  "minimo_lb": 0, "minimo_usd": 39.95},
        },
        "maritimo": {
            "us": {"tarifa_ft3": 34.99, "minimo_ft3": 0, "minimo_usd": 54.99},
        },
    },
    "Me lo trae CP": {
        "origenes":  ["us", "cn"],    # Opera desde USA y China
        "consolidado_dias": None,
        "aereo": {
            "us": {"tarifa_lb": 5.99,  "minimo_lb": 5, "minimo_usd": 29.95},
            "cn": {"tarifa_lb": 15.00, "minimo_lb": 5, "minimo_usd": 75.00},
        },
        "maritimo": {
            "us": {"tarifa_ft3": 35.00, "minimo_ft3": 1, "minimo_usd": 35.00},
            "cn": {"tarifa_ft3": 27.00, "minimo_ft3": 1, "minimo_usd": 27.00},
        },
    },
}

# ─── DEFAULTS ACTIVOS (se sobreescriben desde sidebar) ──────────
COURIER_ACTIVO      = "Un Solo Dolar"
TARIFA_AEREA_LIBRA  = 6.99
MINIMO_AEREO        = 39.95
TARIFA_MARITIMA_FT3 = 34.99
MINIMO_MARITIMO     = 54.99

# ─── MERCADOLIBRE VENEZUELA ─────────────────────────────────────
COMISION_ML = 0.11            # 11% comisión ML Venezuela

# ─── CARGOS EN ORIGEN (USA / China) ─────────────────────────────
# Sales Tax por tienda — ajustable desde el sidebar de la app
SALES_TAX_TIENDAS = {
    "Amazon":     0.07,   # ~7% promedio (varía por estado)
    "eBay":       0.07,
    "Walmart":    0.07,
    "AliExpress": 0.00,   # China directo: sin sales tax USA
    "Otro":       0.07,
}

# Envío interno USA (tienda → warehouse courier)
# Amazon Prime: gratis la mayoría de veces, puede cobrar
ENVIO_INTERNO_TIENDAS = {
    "Amazon":     0.00,   # Prime generalmente gratis
    "eBay":       5.00,   # promedio estimado
    "Walmart":    0.00,   # Walmart+ / free shipping
    "AliExpress": 0.00,   # incluido en precio
    "Otro":       0.00,   # desconocido — usuario debe especificarlo si aplica
}

# ─── MARGEN DE SEGURIDAD ────────────────────────────────────────
MARGEN_SEGURIDAD = 0.03       # 3% sobre costo total (imprevistos)

# ─── MARGEN DE GANANCIA DESEADO ─────────────────────────────────
# % sobre el precio de venta ML (no sobre el costo)
# Ejemplo: 35% significa que de cada $100 vendidos, $35 es ganancia neta
# precio_objetivo = costo_real / (1 - COMISION_ML - MARGEN_GANANCIA)
MARGEN_GANANCIA = 0.35        # 35% ganancia sobre precio de venta
