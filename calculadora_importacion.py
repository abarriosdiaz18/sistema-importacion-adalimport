from config_envios import (TARIFA_AEREA_LIBRA, MINIMO_AEREO, TARIFA_MARITIMA_FT3,
                           MINIMO_MARITIMO, COMISION_ML, SALES_TAX_TIENDAS,
                           ENVIO_INTERNO_TIENDAS, MARGEN_SEGURIDAD, MARGEN_GANANCIA)
import config_envios as _cfg

# ─── Validación de productos ─────────────────────────────────────
def validar_producto(p):
    """
    Valida los datos de un producto antes de calcular.
    Retorna dict con: valido (bool), errores (list), advertencias (list), modo (str)
    
    Modos de cálculo:
        "completo"    — tiene todo, cálculo exacto
        "sin_dims"    — falta largo/ancho/alto, usa solo peso real (puede subestimar)
        "invalido"    — faltan datos críticos, no se puede calcular
    """
    errores     = []
    advertencias = []
    modo        = "completo"

    nombre = p.get("nombre", "Producto")

    # ── Críticos: sin estos no hay cálculo ──
    if not p.get("nombre", "").strip():
        errores.append("Falta el nombre del producto.")

    costo = p.get("costo", 0)
    if not costo or float(costo) <= 0:
        errores.append("El costo del producto debe ser mayor a $0.")

    peso = p.get("peso_real", 0)
    if not peso or float(peso) <= 0:
        errores.append(f"Falta el peso real (lb) — sin esto no se puede calcular el courier.")

    # ── Dimensiones: opcionales pero importantes ──
    # Limpieza robusta: strip() si es string, luego conversión a float
    def _parse_dim(val):
        """Convierte a float de forma segura. Soporta int, float y string."""
        try:
            if isinstance(val, str):
                val = val.strip()
            return float(val) if val not in (None, "", 0, "0") else 0.0
        except (ValueError, TypeError):
            return 0.0

    largo = _parse_dim(p.get("largo", 0))
    ancho = _parse_dim(p.get("ancho", 0))
    alto  = _parse_dim(p.get("alto", 0))

    # Una dimensión es válida si su valor float es estrictamente mayor a 0
    tiene_dims = (largo > 0.0) and (ancho > 0.0) and (alto > 0.0)

    # Normalizar el dict con los valores float ya limpios (prioridad de datos del usuario)
    if tiene_dims:
        p["largo"] = largo
        p["ancho"] = ancho
        p["alto"]  = alto

    if not tiene_dims:
        if peso and float(peso) > 0:
            advertencias.append(
                f"Faltan dimensiones (largo/ancho/alto). "
                f"Se usará solo el peso real ({peso} lb). "
                f"Si el paquete es grande y liviano, el courier podría cobrar más."
            )
            # Asignar dimensiones mínimas solo cuando realmente faltan
            p.setdefault("largo", 1.0)
            p.setdefault("ancho", 1.0)
            p.setdefault("alto",  1.0)
            modo = "sin_dims"
        else:
            errores.append("Faltan dimensiones Y peso real. No se puede calcular.")

    # ── Cantidad ──
    cant = p.get("cantidad", 0)
    if not cant or int(cant) <= 0:
        advertencias.append("Cantidad no especificada, se asume 1 unidad.")
        p["cantidad"] = 1

    # ── Tienda ──
    tienda = p.get("tienda", "")
    if not tienda:
        advertencias.append("Tienda no especificada, se usará tax default (7%).")
        p["tienda"] = "Otro"

    valido = len(errores) == 0
    if valido and not advertencias:
        modo = "completo"

    return {
        "valido":       valido,
        "errores":      errores,
        "advertencias": advertencias,
        "modo":         modo,
    }


def validar_lote(productos):
    """
    Valida todos los productos del lote.
    Retorna resumen con productos válidos, inválidos y advertencias.
    """
    resumen = {
        "todos_validos":   True,
        "productos_ok":    [],
        "productos_error": [],
        "hay_advertencias": False,
    }

    for p in productos:
        resultado = validar_producto(p)
        p["_validacion"] = resultado

        if resultado["valido"]:
            resumen["productos_ok"].append(p)
            if resultado["advertencias"]:
                resumen["hay_advertencias"] = True
        else:
            resumen["productos_error"].append({
                "nombre":  p.get("nombre", "Sin nombre"),
                "errores": resultado["errores"],
            })
            resumen["todos_validos"] = False

    return resumen



# ═══════════════════════════════════════════════════════════════
#  ADALIMPORT — Calculadora de importación
#  Estructura de costo real por producto:
#
#  costo_origen       = precio en tienda
#  + sales_tax        = % según tienda/estado (configurable)
#  + envio_interno    = tienda → warehouse courier (configurable)
#  ─────────────────────────────────────────────────────────────
#  costo_en_warehouse = subtotal antes de courier
#  + envio_courier    = warehouse → Venezuela (proporcional al lote)
#  + margen_seguridad = 3% sobre costo total
#  ─────────────────────────────────────────────────────────────
#  costo_real_unitario = todo lo anterior
#  precio_ml           = costo_real / (1 - comision_ml)
#  ganancia_neta       = precio_ml - costo_real
# ═══════════════════════════════════════════════════════════════


# ─── Helpers de peso ────────────────────────────────────────────
def _peso_volumetrico_aereo(largo, ancho, alto):
    """Divisor 166 estándar para aéreo (pulgadas)."""
    return (largo * ancho * alto) / 166

def _peso_volumetrico_maritimo(largo, ancho, alto):
    """Convierte pulgadas a ft³ para marítimo."""
    return (largo * ancho * alto) / 1728  # 12³ = 1728 in³ por ft³

def _peso_cobrable_aereo(peso_real, largo, ancho, alto):
    return max(peso_real, _peso_volumetrico_aereo(largo, ancho, alto))


# ─── Costo en origen por producto ───────────────────────────────
def calcular_costo_origen(precio, tienda="Amazon", tax_manual=None, envio_interno_manual=None):
    """
    Calcula el costo real del producto puesto en el warehouse del courier.

    Parámetros:
        precio              : precio pagado en la tienda ($)
        tienda              : "Amazon", "eBay", "Walmart", "AliExpress", "Otro"
        tax_manual          : si se conoce el tax exacto, sobreescribe el default (ej: 0.08)
        envio_interno_manual: si se conoce el envío interno exacto ($), sobreescribe default
    """
    tax_rate     = tax_manual     if tax_manual     is not None else SALES_TAX_TIENDAS.get(tienda, 0.07)
    envio_int    = envio_interno_manual if envio_interno_manual is not None else ENVIO_INTERNO_TIENDAS.get(tienda, 5.0)

    sales_tax    = round(precio * tax_rate, 2)
    costo_origen = round(precio + sales_tax + envio_int, 2)

    return {
        "precio_tienda":  precio,
        "tienda":         tienda,
        "tax_rate":       tax_rate,
        "sales_tax":      sales_tax,
        "envio_interno":  envio_int,
        "costo_origen":   costo_origen,   # puesto en warehouse
    }


# ─── Envío del lote completo ────────────────────────────────────
def calcular_envio_lote(productos, modo="aereo", courier=None, origen="us"):
    """
    Calcula el costo de envío courier del lote completo.
    modo   : "aereo" | "maritimo"
    courier: nombre del courier (None = usar COURIER_ACTIVO del config)
    origen : "us" | "cn"
    """
    import config_envios as _cfg
    courier = courier or getattr(_cfg, "COURIER_ACTIVO", "Un Solo Dolar")
    all_couriers = _cfg.COURIERS
    tarifas_courier = all_couriers.get(courier, all_couriers["Un Solo Dolar"])

    if modo == "aereo":
        cfg_aereo = tarifas_courier["aereo"][origen]
        tarifa_lb  = cfg_aereo["tarifa_lb"]
        min_lb     = cfg_aereo["minimo_lb"]    # mínimo en libras (ej: 5 lb)
        min_usd    = cfg_aereo["minimo_usd"]   # mínimo en dólares

        peso_real_total = 0
        volumen_total   = 0
        for p in productos:
            cant = p.get("cantidad", 1)
            peso_real_total += p["peso_real"] * cant
            volumen_total   += _peso_volumetrico_aereo(p["largo"], p["ancho"], p["alto"]) * cant

        peso_cobrable   = max(peso_real_total, volumen_total)
        # Aplicar mínimo en libras si aplica (ej: CP cobra mínimo 5 lb)
        peso_cobrable   = max(peso_cobrable, min_lb)
        costo_calculado = round(peso_cobrable * tarifa_lb, 2)
        # Aplicar mínimo en dólares
        costo_envio     = max(costo_calculado, min_usd)
        return round(costo_envio, 2), round(peso_cobrable, 2), "lb"

    else:  # maritimo
        cfg_mar   = tarifas_courier["maritimo"][origen]
        tarifa_ft3 = cfg_mar["tarifa_ft3"]
        min_ft3    = cfg_mar["minimo_ft3"]     # mínimo en ft³
        min_usd    = cfg_mar["minimo_usd"]

        volumen_total_ft3 = 0
        for p in productos:
            cant = p.get("cantidad", 1)
            volumen_total_ft3 += _peso_volumetrico_maritimo(p["largo"], p["ancho"], p["alto"]) * cant

        # Aplicar mínimo en ft³
        volumen_cobrable  = max(volumen_total_ft3, min_ft3)
        costo_calculado   = round(volumen_cobrable * tarifa_ft3, 2)
        costo_envio       = max(costo_calculado, min_usd)
        return round(costo_envio, 2), round(volumen_total_ft3, 3), "ft³"


# ─── Análisis completo del lote ─────────────────────────────────
def analizar_lote(productos, modo="aereo", margen_ganancia=None, courier=None, origen="us"):
    """
    Analiza rentabilidad de un lote completo con Consolidado Proporcional Real.

    ═══════════════════════════════════════════════════════════════
    CONSOLIDADO PROPORCIONAL — cómo funciona:

    PASO 1 — SUMATORIA FÍSICA DEL LOTE:
        Aéreo   → Σ(peso_cobrable_unitario × cantidad)  [lb totales del lote]
        Marítimo→ Σ(vol_ft3_unitario × cantidad)        [ft³ totales del lote]

    PASO 2 — FLETE TOTAL DEL LOTE (comparando acumulado vs mínimos del courier):
        carga_cobrable  = max(carga_real_total, mínimo_lb o mínimo_ft3)
        flete_calculado = carga_cobrable × tarifa
        flete_total     = max(flete_calculado, mínimo_usd)

    PASO 3 — FACTOR DE FLETE (tarifa efectiva real):
        factor_flete = flete_total / carga_total_real
        ($/lb o $/ft³ efectivo considerando el mínimo distribuido)

    PASO 4 — PRORRATEO EXACTO POR ÍTEM:
        flete_proporcional_u = factor_flete × magnitud_unitaria_item
        → Garantiza: Σ(flete_proporcional_u × cantidad) = flete_total exacto

    PASO 5 — COSTO FINAL UNITARIO:
        costo_real = Precio_Tienda + Sales_Tax + Envío_Interno
                     + Flete_Proporcional + Margen_Seguridad(3%)
    ═══════════════════════════════════════════════════════════════

    Retorna (resultados, costo_envio_total, carga_total, unidad, costo_total_lote)
    con claves adicionales en cada resultado:
        peso_cobrable_item  : magnitud física del ítem por unidad (lb o ft³)
        vol_ft3_item        : volumen ft³ por unidad (siempre disponible)
        prop_fisica         : fracción del ítem sobre carga total del lote (0..1)
        flete_proporcional  : flete asignado a este ítem ($/u)
        factor_flete        : $/lb o $/ft³ efectivo del lote
        unidad_fisica       : "lb" | "ft³"
        carga_total_lote    : Σ(magnitud × cantidad) del lote en la unidad del modo
        carga_minimo_courier: mínimo lb o ft³ del courier activo
        faltante_minimo     : cuánto falta para alcanzar el mínimo (0 si ya lo supera)
        optimo              : bool — la carga del lote supera el mínimo del courier
    """
    import copy as _copy

    # ── LIMPIEZA DE ESTADO INTERNO ────────────────────────────────────────────
    # Deep copy garantiza independencia total entre llamadas sucesivas.
    # Elimina claves internas calculadas en simulaciones previas para evitar
    # que _origen de modo="aereo" contamine modo="maritimo" y viceversa.
    # Sin esto, dict(p) superficial hereda _origen ya calculado → precios idénticos.
    productos = [_copy.deepcopy(p) for p in productos]
    for p in productos:
        p.pop("_origen",     None)
        p.pop("_validacion", None)

    margen = margen_ganancia if margen_ganancia is not None else MARGEN_GANANCIA

    # ── Resolver config del courier ──────────────────────────────────────────
    import config_envios as _cfg
    courier_nombre = courier or getattr(_cfg, "COURIER_ACTIVO", "Un Solo Dolar")
    all_couriers   = _cfg.COURIERS
    tarifas_c      = all_couriers.get(courier_nombre, all_couriers["Un Solo Dolar"])

    if modo == "aereo":
        cfg_modo      = tarifas_c["aereo"][origen]
        tarifa_unit   = cfg_modo["tarifa_lb"]
        minimo_carga  = cfg_modo["minimo_lb"]    # mínimo en lb
        minimo_usd    = cfg_modo["minimo_usd"]
    else:
        cfg_modo      = tarifas_c["maritimo"][origen]
        tarifa_unit   = cfg_modo["tarifa_ft3"]
        minimo_carga  = cfg_modo["minimo_ft3"]   # mínimo en ft³
        minimo_usd    = cfg_modo["minimo_usd"]

    # 1. Costo en origen de cada producto
    for p in productos:
        tienda  = p.get("tienda", "Amazon")
        tax_man = p.get("tax_manual", None)
        env_int = p.get("envio_interno", None)

        if p.get("tax_incluido", False):
            res_origen = calcular_costo_origen(p["costo"], tienda, tax_manual=0.0, envio_interno_manual=env_int or 0.0)
        else:
            res_origen = calcular_costo_origen(p["costo"], tienda, tax_man, env_int)

        p["_origen"] = res_origen

    # 2. Asegurar dimensiones mínimas para productos sin dims (evitar None)
    for p in productos:
        if not p.get("largo") or float(p.get("largo") or 0) <= 0:
            p["largo"] = 1
        if not p.get("ancho") or float(p.get("ancho") or 0) <= 0:
            p["ancho"] = 1
        if not p.get("alto") or float(p.get("alto") or 0) <= 0:
            p["alto"] = 1

    # ────────────────────────────────────────────────────────────────────────
    # PASO 1 — SUMATORIA FÍSICA REAL DEL LOTE
    # Calcula la magnitud unitaria de cada ítem y acumula el total del lote.
    # ────────────────────────────────────────────────────────────────────────
    _fisico_items = []    # (magnitud_por_unidad, cantidad, vol_ft3_unitario)
    for p in productos:
        cant  = p.get("cantidad", 1)
        largo = float(p["largo"])
        ancho = float(p["ancho"])
        alto  = float(p["alto"])
        peso  = float(p.get("peso_real", 0))
        vol_u = _peso_volumetrico_maritimo(largo, ancho, alto)  # ft³ siempre

        if modo == "aereo":
            pvol  = _peso_volumetrico_aereo(largo, ancho, alto)
            mag_u = max(peso, pvol)    # peso cobrable aéreo por unidad
        else:
            mag_u = vol_u              # ft³ por unidad para marítimo

        _fisico_items.append((mag_u, cant, vol_u))

    # Carga real total del lote (en la unidad del modo)
    carga_real_total = sum(m * c for m, c, _ in _fisico_items)

    # ────────────────────────────────────────────────────────────────────────
    # PASO 2 — FLETE TOTAL DEL LOTE  [LÓGICA ELÁSTICA]
    #
    #   ÍTEM SOLO (n=1): el flete NO se prorratea. Se asigna directamente el
    #     mínimo del courier (minimo_usd). El ítem absorbe el costo completo.
    #     Esto expone correctamente el costo real cuando no hay consolidado.
    #
    #   LOTE (n>1): prorrateo proporcional exacto. El flete se distribuye
    #     según el peso/volumen de cada ítem dentro del total del lote.
    #     La suma de todos los fletes individuales = flete_total del courier.
    # ────────────────────────────────────────────────────────────────────────
    n_items_lote_calc = len(productos)   # cantidad de SKUs distintos en el lote
    es_lote_consolidado_calc = n_items_lote_calc > 1

    carga_cobrable    = max(carga_real_total, minimo_carga)
    flete_calculado   = round(carga_cobrable * tarifa_unit, 4)
    costo_envio_total = round(max(flete_calculado, minimo_usd), 2)

    # Carga base para prorrateo (siempre la real para que la suma cuadre)
    carga_base_prorrateo = max(carga_real_total, minimo_carga)

    # ────────────────────────────────────────────────────────────────────────
    # PASO 3 — FACTOR DE FLETE (tarifa efectiva real = flete_total / carga_REAL)
    #
    #   Ítem solo: factor no aplica — el flete completo se asigna directamente.
    #   Lote:      Σ(factor × mag_u × cant) = costo_envio_total exacto.
    #   El mínimo USD queda incorporado: si el lote es pequeño, el factor
    #   sube (más caro/lb), reflejando que se paga el mínimo distribuido.
    # ────────────────────────────────────────────────────────────────────────
    if carga_real_total > 0:
        factor_flete = costo_envio_total / carga_real_total
        _usar_fisico = True
    else:
        factor_flete = 0.0
        _usar_fisico = False

    # Valores para la UI del Monitor de Eficiencia
    unidad          = "lb" if modo == "aereo" else "ft³"
    peso_o_vol      = round(carga_real_total, 3)   # carga REAL (sin mínimo)
    faltante_min    = round(max(0.0, minimo_carga - carga_real_total), 3)
    lote_optimo     = carga_real_total >= minimo_carga and costo_envio_total > minimo_usd

    # ────────────────────────────────────────────────────────────────────────
    # PASO 4 — PRORRATEO EXACTO: flete_proporcional_u = factor_flete × mag_u
    #   Garantía matemática: Σ(flete_prop_u × cant) = costo_envio_total
    #   Si no hay datos físicos válidos → fallback proporcional a costo-warehouse
    # ────────────────────────────────────────────────────────────────────────
    costo_warehouse_total = sum(
        p["_origen"]["costo_origen"] * p.get("cantidad", 1) for p in productos
    )
    costo_total_lote = costo_warehouse_total + costo_envio_total

    # Protección: si carga_real_total ≈ 0 (todo 1×1×1 sin peso), fallback a costo-warehouse
    if not _usar_fisico or carga_base_prorrateo <= 0:
        _usar_fisico = False

    resultados = []
    for i, p in enumerate(productos):
        cant             = p.get("cantidad", 1)
        orig             = p["_origen"]
        costo_wh         = orig["costo_origen"]
        mag_u, _, vol_u  = _fisico_items[i]

        # ── PASO 4: Asignación de Flete [LÓGICA ELÁSTICA] ────────────────
        #
        #   ÍTEM SOLO (es_lote_consolidado_calc = False):
        #     El flete completo se asigna directamente al único ítem.
        #     envio_asignado = costo_envio_total / cantidad
        #     Esto expone el verdadero costo del mínimo del courier sin dilución.
        #
        #   LOTE CONSOLIDADO (es_lote_consolidado_calc = True):
        #     Prorrateo proporcional exacto por peso/volumen.
        #     Σ(envio_asignado × cantidad) = costo_envio_total  [garantía matemática]
        # ─────────────────────────────────────────────────────────────────────
        if not es_lote_consolidado_calc:
            # Ítem solo: absorbe el flete mínimo completo distribuido entre sus unidades
            envio_asignado = round(costo_envio_total / max(cant, 1), 4)
            prop_fisica    = 1.0   # el ítem ES el 100% del lote
        elif _usar_fisico:
            # Lote: flete por unidad = Factor de Flete × magnitud unitaria del ítem
            envio_asignado = round(factor_flete * mag_u, 4)
            prop_fisica    = round((mag_u * cant) / carga_real_total, 6) if carga_real_total > 0 else 0
        else:
            # Fallback: distribuir por valor de warehouse (sin datos físicos)
            proporcion_wh  = (costo_wh * cant) / costo_warehouse_total if costo_warehouse_total > 0 else 0
            envio_asignado = round((costo_envio_total * proporcion_wh) / max(cant, 1), 4)
            prop_fisica    = round(proporcion_wh, 6)

        # Margen seguridad 3%
        costo_pre_margen = costo_wh + envio_asignado
        margen_seg       = round(costo_pre_margen * MARGEN_SEGURIDAD, 2)

        # Costo real final
        costo_real = round(costo_pre_margen + margen_seg, 2)

        # ── PRECIO MÍNIMO: solo cubre costos + comisión ML ───────────
        divisor_minimo = 1 - COMISION_ML
        precio_ml_min  = round(costo_real / divisor_minimo, 2)
        ganancia_min   = round(precio_ml_min - costo_real, 2)
        margen_min_pct = round((ganancia_min / precio_ml_min) * 100, 1)

        # ── PRECIO OBJETIVO: cubre costos + comisión + ganancia deseada
        divisor_obj = 1 - COMISION_ML - margen
        if divisor_obj <= 0:
            divisor_obj = 0.10
        precio_ml_obj  = round(costo_real / divisor_obj, 2)
        ganancia_obj   = round(precio_ml_obj * margen, 2)
        margen_obj_pct = round(margen * 100, 1)

        comision_ml_valor = round(precio_ml_obj * COMISION_ML, 2)

        # ── Aptitud de Vía — datos de volumen real (siempre disponibles) ─────
        peso_real_u = float(p.get("peso_real", 0))
        vol_real_u  = _peso_volumetrico_maritimo(
            float(p.get("largo", 1)),
            float(p.get("ancho", 1)),
            float(p.get("alto",  1))
        )

        # ── Número de ítems distintos en el lote (contexto: solo vs consolidado)
        n_items_lote        = n_items_lote_calc
        es_lote_consolidado = es_lote_consolidado_calc

        # Margen neto real sobre precio de venta objetivo
        margen_neto_pct = round((ganancia_obj / precio_ml_obj) * 100, 1) if precio_ml_obj > 0 else 0.0

        # ── UMBRALES DE DECISIÓN ─────────────────────────────────────────────
        UMBRAL_MARGEN_SALUDABLE  = 20.0   # % ≥ 20 → ✅ COMPRAR
        UMBRAL_MARGEN_MINIMO     = 5.0    # % < 5  → ❌ NO COMPRAR
        UMBRAL_FILLER_EFICIENTE  = 0.10   # flete ≤ 10% costo_wh en lote → filler ok

        # Ratio flete/costo para lógica de filler
        courier_vs_producto   = envio_asignado / costo_wh    if costo_wh    > 0 else 0
        courier_vs_costo_real = envio_asignado / costo_real  if costo_real  > 0 else 0

        # Texto de contexto de flete para mensajes
        if es_lote_consolidado:
            _ctx_flete = f"prorrateado del lote (${envio_asignado:.2f})"
            _es_filler = courier_vs_producto <= UMBRAL_FILLER_EFICIENTE
        else:
            _ctx_flete = f"individual — mínimo courier asignado: ${costo_envio_total:.2f}"
            _es_filler = False

        # ══════════════════════════════════════════════════════════════════════
        # ÁRBOL DE DECISIÓN — JERARQUÍA DE SEGURIDAD LOGÍSTICA (v3)
        #
        # PRIORIDAD 1 🟠 CAMBIAR A MARÍTIMO
        #   Vía aérea + peso individual > 5 lb.
        #   Ítems pesados inflan el factor-flete del lote completo.
        #
        # PRIORIDAD 2 🔴 INVIABLE AIRE
        #   DOBLE CONDICIÓN (ambas deben cumplirse):
        #     a) Peso Volumétrico > 2× Peso Real  (ratio > 100%)
        #     b) Peso Volumétrico absoluto > 0.5 lb  ← NUEVO UMBRAL (v3)
        #
        #   EXCEPCIÓN "FILLER PEQUEÑO": si pvol_u ≤ 0.5 lb el producto
        #   ocupa tan poco espacio aéreo que su impacto en el lote es
        #   despreciable (< ~$0.30 de flete). Se evalúa solo por margen.
        #
        #   Ejemplos:
        #     Botella Ciclismo  pvol=7.28 lb, ratio=22× → 🔴 BLOQUEADO
        #     Pilas Energizer   pvol=0.12 lb, ratio=2×  → ✅ evalúa margen
        #     Pasta Térmica MX4 pvol=0.09 lb, ratio=3×  → ✅ evalúa margen
        #
        # PRIORIDAD 3 🔴 NO COMPRAR
        #   Margen de ganancia < 5% tras aplicar el flete.
        #
        # PRIORIDAD 4 ⚠️ REVISAR
        #   Margen entre 5% y 20% — rentable pero ajustado.
        #
        # PRIORIDAD 5 ✅ COMPRAR
        #   Producto apto para la vía y margen ≥ 20%.
        # ══════════════════════════════════════════════════════════════════════

        # ── Pre-cálculo de peso volumétrico para ratio ────────────────────
        pvol_u        = _peso_volumetrico_aereo(
            float(p.get("largo", 1)), float(p.get("ancho", 1)), float(p.get("alto", 1))
        )
        peso_real_u   = float(p.get("peso_real", 0))

        # Ratio: cuántas veces el volumétrico supera al peso real
        # Ej botella: pvol_u=7.28, peso_real_u=0.33 → ratio=22.06
        ratio_vol_real = (pvol_u / peso_real_u) if peso_real_u > 0 else 0.0

        # El flete volumétrico destruye el margen cuando la ganancia es negativa
        # y el volumétrico domina sobre el peso real
        vol_destruye_margen = (modo == "aereo") and (ganancia_obj < 0) and (pvol_u > peso_real_u)

        # PRIORIDAD 1 — Cambiar a Marítimo (aéreo + peso REAL > 5 lb por unidad)
        PESO_LIMITE_AEREO  = 5.0   # lb por unidad
        VOL_CRITICO_AEREO  = 2.0   # ft³ por unidad (umbral de volumen físico)

        excede_peso_aereo = (modo == "aereo") and (peso_real_u > PESO_LIMITE_AEREO)
        excede_vol_aereo  = (modo == "aereo") and (vol_real_u  > VOL_CRITICO_AEREO)
        inapto_para_aereo = excede_peso_aereo or excede_vol_aereo

        _motivos_inaptitud = []
        if excede_peso_aereo:
            _motivos_inaptitud.append(f"peso {peso_real_u:.2f} lb/u > {PESO_LIMITE_AEREO} lb")
        if excede_vol_aereo:
            _motivos_inaptitud.append(f"volumen {vol_real_u:.4f} ft³/u > {VOL_CRITICO_AEREO} ft³")

        # PRIORIDAD 2 — Inviable Aire  [v3: DOBLE CONDICIÓN con umbral absoluto]
        #
        # REGLA BASE : Peso_Vol > Peso_Real × 2  (volumétrico > 2× el peso real)
        # EXCEPCIÓN  : si pvol_u ≤ 0.5 lb, el producto es "filler pequeño" y su
        #              impacto en el flete del lote es despreciable. NO se bloquea;
        #              pasa directo al árbol de margen para ser evaluado por rentabilidad.
        #
        # Lógica completa de excede_ratio_vol (las 3 deben cumplirse):
        #   1. Modo aéreo
        #   2. pvol_u  > peso_real_u × RATIO_VOL_INVIABLE   (ratio > 100%)
        #   3. pvol_u  > UMBRAL_VOL_ABS_INVIABLE             (> 0.5 lb absoluto)  ← NUEVO v3
        #
        # Ejemplos de validación:
        #   Pilas AA Energizer  pvol=0.12 lb, peso_real=0.06 lb → ratio=2× PERO pvol≤0.5 → NO bloquea
        #   Pasta Térmica MX-4  pvol=0.09 lb, peso_real=0.03 lb → ratio=3× PERO pvol≤0.5 → NO bloquea
        #   Botella de Ciclismo pvol=7.28 lb, peso_real=0.33 lb → ratio=22× Y pvol>0.5  → 🔴 BLOQUEA
        RATIO_VOL_INVIABLE      = 2.0   # el vol debe ser > 2× el peso real (100%)
        UMBRAL_VOL_ABS_INVIABLE = 0.5   # lb — por debajo de este absoluto, es "filler"
                                         # y su impacto en el lote es despreciable
        excede_ratio_vol = (
            (modo == "aereo")
            and (pvol_u > peso_real_u * RATIO_VOL_INVIABLE)   # vol > 2× peso real
            and (pvol_u > peso_real_u)                          # confirma que vol domina
            and (pvol_u > UMBRAL_VOL_ABS_INVIABLE)             # ← NUEVO v3: umbral absoluto
        )                                                        #   evita bloquear fillers pequeños
        inviable_aire = (not inapto_para_aereo) and (excede_ratio_vol or vol_destruye_margen)

        # ── Alerta logística (semáforo corto para UI) ─────────────────────
        if inapto_para_aereo:
            alerta_logistica = "🟠 Usar Marítimo"
        elif excede_ratio_vol and not inapto_para_aereo:
            alerta_logistica = "🔴 Demasiado aire"
        elif vol_destruye_margen:
            alerta_logistica = "🔴 Flete > ganancia"
        elif margen_neto_pct < UMBRAL_MARGEN_MINIMO:
            alerta_logistica = "🔴 Margen bajo"
        elif margen_neto_pct < UMBRAL_MARGEN_SALUDABLE:
            alerta_logistica = "⚠️ Revisar margen"
        else:
            alerta_logistica = "✅"

        # ── Rama de decisión (jerarquía estricta) ────────────────────────
        if inapto_para_aereo:
            # PRIORIDAD 1 🟠 USAR MARÍTIMO
            decision = "🟠 USAR MARÍTIMO"
            decision_razon = (
                f"Peso/volumen excesivo para avión. "
                f"Flete asignado: ${envio_asignado:.2f} · Margen: {margen_neto_pct:.1f}%."
            )

        elif inviable_aire:
            # PRIORIDAD 2 🔴 INVIABLE
            decision = "🔴 INVIABLE"
            decision_razon = (
                f"Paga demasiado 'aire' por vía aérea. "
                f"Peso vol: {pvol_u:.2f} lb ({ratio_vol_real:.1f}× el real). "
                f"Margen: {margen_neto_pct:.1f}%."
            )

        elif margen_neto_pct < UMBRAL_MARGEN_MINIMO:
            # PRIORIDAD 3 🔴 INVIABLE (margen)
            decision = "🔴 INVIABLE"
            decision_razon = (
                f"Margen {margen_neto_pct:.1f}% — bajo el mínimo del {UMBRAL_MARGEN_MINIMO}%. "
                f"Flete {_ctx_flete}."
            )

        elif margen_neto_pct < UMBRAL_MARGEN_SALUDABLE:
            # PRIORIDAD 4 ⚠️ REVISAR
            decision = "⚠️ REVISAR"
            decision_razon = (
                f"Margen {margen_neto_pct:.1f}% — rentable pero ajustado. "
                f"Flete {_ctx_flete}."
            )

        else:
            # PRIORIDAD 5 ✅ COMPRAR
            decision = "✅ COMPRAR"
            decision_razon = (
                f"Margen {margen_neto_pct:.1f}% · Flete {_ctx_flete}."
            )

        resultados.append({
            "nombre":             p["nombre"],
            "descripcion":        p.get("descripcion", ""),
            "categoria":          p.get("categoria", "Sin Categoría"),
            "tienda":             orig["tienda"],
            "cantidad":           cant,
            # Desglose origen
            "precio_tienda":      orig["precio_tienda"],
            "sales_tax":          orig["sales_tax"],
            "tax_rate":           orig["tax_rate"],
            "envio_interno":      orig["envio_interno"],
            "costo_warehouse":    costo_wh,
            "peso_cobrable_item": round(mag_u, 4) if modo == "aereo"    else 0.0,
            "vol_ft3_item":       round(vol_u, 6),
            "prop_fisica":        prop_fisica,
            "flete_proporcional": round(envio_asignado, 2),
            "unidad_fisica":      "lb" if modo == "aereo" else "ft³",
            "tarifa_efectiva":    round(factor_flete, 4),
            "factor_flete":       round(factor_flete, 4),
            # ── Monitor de Eficiencia
            "carga_total_lote":     round(carga_real_total, 3),
            "carga_minimo_courier": round(minimo_carga, 3),
            "carga_minimo_usd":     minimo_usd,
            "faltante_minimo":      round(faltante_min, 3),
            "lote_optimo":          lote_optimo,
            # ── Desglose courier
            "envio_courier":      round(envio_asignado, 2),
            "margen_seguridad":   margen_seg,
            "costo_real":         costo_real,
            "comision_ml":        comision_ml_valor,
            # Precio mínimo
            "precio_ml_minimo":   precio_ml_min,
            "ganancia_minima":    ganancia_min,
            "margen_min_pct":     margen_min_pct,
            # Precio objetivo
            "precio_ml":          precio_ml_obj,
            "precio_ml_objetivo": precio_ml_obj,
            "ganancia_neta":      ganancia_obj,
            "ganancia_objetivo":  ganancia_obj,
            "margen_pct":         margen_obj_pct,
            "margen_ganancia":    margen,
            "decision":             decision,
            "decision_razon":       decision_razon,
            "es_lote_consolidado":  es_lote_consolidado,
            "n_items_lote":         n_items_lote,
            "margen_neto_pct":      margen_neto_pct,
            # ── Filtros de Seguridad Logística ──────────────────────────────
            "inapto_para_aereo":    inapto_para_aereo,     # Prioridad 1: peso > 5lb o vol > 2ft³
            "inviable_aire":        inviable_aire,          # Prioridad 2: vol > 2× peso real (100%)
            "excede_peso_aereo":    excede_peso_aereo,      # True si peso > 5.0 lb
            "excede_vol_aereo":     excede_vol_aereo,       # True si vol > 2.0 ft³
            "excede_ratio_vol":     excede_ratio_vol,       # True si vol > 2× peso real
            "ratio_vol_real":       round(ratio_vol_real, 2),
            "peso_real_unitario":   round(peso_real_u, 3),
            "vol_real_unitario":    round(vol_real_u, 5),
            "courier_vs_producto":  round(courier_vs_producto, 2),
            "courier_vs_costo":     round(courier_vs_costo_real, 2),
            "alerta_logistica":     alerta_logistica,       # Texto corto para columna UI
            "modo_envio":           modo,
            "_validacion":          p.get("_validacion", {}),
        })

    return resultados, costo_envio_total, round(peso_o_vol, 3), unidad, costo_total_lote


if __name__ == "__main__":
    # ══════════════════════════════════════════════════════════════════════════
    # TEST SUITE — Validación del parche v3: Umbral de Tolerancia INVIABLE AIRE
    #
    # Casos esperados:
    #   ✅ Pilas AA Energizer  → COMPRAR   (pvol=0.29 lb ≤ 0.5 lb → filler, no bloquear)
    #   ✅ Pasta Térmica MX-4  → COMPRAR   (pvol=0.09 lb ≤ 0.5 lb → filler, no bloquear)
    #   ✅ Cable USB            → COMPRAR   (pvol=0.19 lb ≤ 0.5 lb → filler, no bloquear)
    #   🔴 Botella Ciclismo    → INVIABLE  (pvol=7.28 lb > 0.5 lb Y ratio=22× → BLOQUEA)
    # ══════════════════════════════════════════════════════════════════════════

    SEP  = "=" * 68
    SEP2 = "-" * 68

    def _pvol(largo, ancho, alto):
        return round((largo * ancho * alto) / 166, 3)

    print(f"\n{SEP}")
    print(f"  ADALIMPORT — TEST v3: Umbral Tolerancia INVIABLE AIRE (0.5 lb)")
    print(f"{SEP}")

    # ── LOTE A: Fillers pequeños (deberían pasar) ────────────────────────
    lote_fillers = [
        {
            "nombre": "Pilas AA Energizer 4pk", "costo": 9.26, "tienda": "Amazon",
            "peso_real": 0.50, "largo": 6, "ancho": 4, "alto": 2, "cantidad": 3,
        },
        {
            "nombre": "Pasta Termica MX-4", "costo": 5.99, "tienda": "Amazon",
            "peso_real": 0.10, "largo": 5, "ancho": 3, "alto": 1, "cantidad": 5,
        },
        {
            "nombre": "Cable USB AliExpress", "costo": 3.50, "tienda": "AliExpress",
            "peso_real": 0.20, "largo": 8, "ancho": 4, "alto": 1, "cantidad": 4,
            "tax_incluido": True,
        },
    ]

    # ── LOTE B: Botella de Ciclismo (debe seguir bloqueada) ──────────────
    lote_botella = [
        {
            "nombre": "Botella Ciclismo 1L", "costo": 12.00, "tienda": "Amazon",
            "peso_real": 0.33, "largo": 12, "ancho": 4, "alto": 4, "cantidad": 1,
        },
    ]

    print(f"\n{'─'*68}")
    print(f"  LOTE A — Fillers pequeños en consolidado aéreo")
    print(f"  Esperado: todos deben pasar al árbol de margen (no INVIABLE AIRE)")
    print(f"{'─'*68}")

    res_a, env_a, peso_a, unid_a, costo_a = analizar_lote(lote_fillers, modo="aereo")
    print(f"  Flete total lote: ${env_a}  |  Carga: {peso_a} {unid_a}  |  Costo lote: ${costo_a:.2f}\n")

    PASA = "✅ OK"
    FALLA = "❌ FALLA"

    for r in res_a:
        pvol = _pvol(
            next(p for p in lote_fillers if p["nombre"] == r["nombre"])["largo"],
            next(p for p in lote_fillers if p["nombre"] == r["nombre"])["ancho"],
            next(p for p in lote_fillers if p["nombre"] == r["nombre"])["alto"],
        )
        es_inviable = "INVIABLE" in r["decision"]
        resultado   = FALLA if es_inviable else PASA
        print(f"  📦 {r['nombre']}")
        print(f"     pvol_u     : {pvol} lb  |  peso_real: {r['peso_real_unitario']} lb")
        print(f"     ratio vol  : {r['ratio_vol_real']}×  |  excede_ratio: {r['excede_ratio_vol']}")
        print(f"     inviable   : {r['inviable_aire']}   → {resultado}")
        print(f"     Decisión   : {r['decision']}")
        print(f"     Margen neto: {r['margen_neto_pct']}%  |  flete asignado: ${r['envio_courier']:.2f}")
        print()

    print(f"{'─'*68}")
    print(f"  LOTE B — Botella de Ciclismo (control negativo)")
    print(f"  Esperado: 🔴 INVIABLE AIRE  (pvol=7.28 lb > 0.5 lb Y ratio=22×)")
    print(f"{'─'*68}")

    res_b, env_b, peso_b, unid_b, costo_b = analizar_lote(lote_botella, modo="aereo")
    print(f"  Flete total lote: ${env_b}  |  Carga: {peso_b} {unid_b}  |  Costo lote: ${costo_b:.2f}\n")

    for r in res_b:
        es_inviable = "INVIABLE" in r["decision"]
        resultado   = PASA if es_inviable else FALLA   # aquí queremos que SÍ sea inviable
        print(f"  📦 {r['nombre']}")
        print(f"     pvol_u     : {_pvol(12,4,4)} lb  |  peso_real: {r['peso_real_unitario']} lb")
        print(f"     ratio vol  : {r['ratio_vol_real']}×  |  excede_ratio: {r['excede_ratio_vol']}")
        print(f"     inviable   : {r['inviable_aire']}   → {resultado}")
        print(f"     Decisión   : {r['decision']}")
        print()

    print(SEP)
    print(f"  RESUMEN DEL TEST")
    print(SEP)
    fallas = 0
    for r in res_a:
        ok = "INVIABLE" not in r["decision"]
        estado = PASA if ok else FALLA
        print(f"  {estado}  {r['nombre']:<35} → {r['decision']}")
        if not ok:
            fallas += 1
    for r in res_b:
        ok = "INVIABLE" in r["decision"]
        estado = PASA if ok else FALLA
        print(f"  {estado}  {r['nombre']:<35} → {r['decision']}")
        if not ok:
            fallas += 1

    print(f"\n  {'🎉 TODOS LOS TESTS PASARON' if fallas == 0 else f'⚠️  {fallas} TEST(S) FALLARON'}")
    print(SEP)

