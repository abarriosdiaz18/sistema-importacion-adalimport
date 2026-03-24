"""
ADALIMPORT · db_supabase.py
════════════════════════════════════════════════════════════════════════════════
Módulo Core — Gestor de Base de Datos Supabase (PostgreSQL)

Firma pública IDÉNTICA a db_manager.py — las páginas no requieren ningún cambio.
El switch entre SQLite y Supabase se controla desde app.py via USE_SUPABASE.

Credenciales: se leen desde st.secrets["supabase"] con fallback a os.getenv()
  · secrets.toml (local/dev):    [supabase] url = "..." / key = "..."
  · Streamlit Cloud (producción): configurar en el panel Secrets del proyecto

Tablas en Supabase (schema public, prefijo import_):
  · import_lotes              — resumen del lote (1 fila por aprobación)
  · import_items_lote         — detalle de ítems (N filas por lote)
  · import_configuracion      — configuración maestra del sistema

NOTA: El prefijo "import_" aísla estas tablas del frontend Astro en el mismo
      proyecto Supabase. NO usar nombres sin prefijo.
════════════════════════════════════════════════════════════════════════════════
"""

import os
import json
from datetime import date, datetime
from typing import List, Dict, Any, Optional, Tuple

# ── Nombres canónicos de tablas ────────────────────────────────────────────────
# Definidos aquí para que un cambio futuro de prefijo sea en 1 sola línea.
_T_LOTES   = "import_lotes"
_T_ITEMS   = "import_items_lote"
_T_CONFIG  = "import_configuracion"


# ── Credenciales: st.secrets con fallback a os.getenv ────────────────────────
def _get_credentials() -> tuple:
    """
    Lee SUPABASE_URL y SUPABASE_KEY con esta prioridad:
      1. st.secrets["supabase"] (Streamlit Cloud / secrets.toml local)
      2. os.getenv() (entornos CI/CD o .env manual)
    """
    try:
        import streamlit as st
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return url, key
    except Exception:
        pass

    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_KEY", "")
    return url, key


def _get_client():
    """Devuelve un cliente Supabase autenticado."""
    from supabase import create_client
    url, key = _get_credentials()
    if not url or not key:
        raise RuntimeError(
            "ADALIMPORT: Credenciales Supabase no encontradas.\n"
            "Configura [supabase] url y key en secrets.toml o variables de entorno."
        )
    return create_client(url, key)


# ════════════════════════════════════════════════════════════════════════════════
# INICIALIZACIÓN
# ════════════════════════════════════════════════════════════════════════════════

def inicializar_db() -> None:
    """
    Verifica conectividad con Supabase.
    Las tablas se crean en el dashboard de Supabase — esta función es un no-op
    si la conexión es exitosa. Idempotente — se puede llamar en cada arranque.
    """
    try:
        client = _get_client()
        client.table(_T_LOTES).select("id").limit(1).execute()
    except Exception as e:
        import warnings
        warnings.warn(f"ADALIMPORT Supabase: No se pudo verificar conexión → {e}")


def get_connection():
    """Alias de compatibilidad — devuelve el cliente Supabase."""
    return _get_client()


# ════════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN MAESTRA
# ════════════════════════════════════════════════════════════════════════════════

def guardar_configuracion(config_dict: dict) -> bool:
    """Guarda el diccionario de configuración en import_configuracion (upsert)."""
    try:
        client = _get_client()
        client.table(_T_CONFIG).upsert({
            "id":             1,
            "datos_json":     json.dumps(config_dict),
            "actualizado_en": datetime.utcnow().isoformat(),
        }).execute()
        return True
    except Exception as e:
        import warnings
        warnings.warn(f"Error guardando configuración en Supabase: {e}")
        return False


def cargar_configuracion() -> dict:
    """Carga y devuelve el diccionario de configuración desde import_configuracion."""
    try:
        client = _get_client()
        resp   = client.table(_T_CONFIG).select("datos_json").eq("id", 1).execute()
        rows   = resp.data
        if rows and rows[0].get("datos_json"):
            return json.loads(rows[0]["datos_json"])
        return {}
    except Exception as e:
        import warnings
        warnings.warn(f"Error cargando configuración desde Supabase: {e}")
        return {}


# ════════════════════════════════════════════════════════════════════════════════
# ESCRITURA — GUARDAR LOTE APROBADO (TRANSACCIÓN ATÓMICA)
# ════════════════════════════════════════════════════════════════════════════════

def guardar_lote_aprobado(
    lote_id_text:    str,
    fecha:           date,
    courier:         str,
    modo:            str,
    origen:          str,
    costo_flete:     float,
    inversion_total: float,
    ganancia_total:  float,
    roi:             float,
    notas:           str,
    resultados:      List[Dict[str, Any]],
) -> Tuple[bool, str]:
    """
    Guarda el lote completo en Supabase.
    Inserta primero en import_lotes y luego los ítems en import_items_lote.
    """
    modo_norm = "Aéreo" if modo.lower() in ("aereo", "aéreo", "aero") else "Marítimo"
    roi_calc  = roi if roi is not None else (
        round((ganancia_total / inversion_total * 100), 2)
        if inversion_total and inversion_total > 0 else 0.0
    )

    try:
        client = _get_client()

        # ── 1. Insertar cabecera del lote ──────────────────────────────────────
        resp_lote = client.table(_T_LOTES).insert({
            "lote_id_text":    lote_id_text,
            "fecha":           fecha.isoformat() if isinstance(fecha, date) else str(fecha),
            "courier":         courier or "",
            "modo":            modo_norm,
            "origen":          origen or "",
            "costo_flete":     round(float(costo_flete),     2),
            "inversion_total": round(float(inversion_total), 2),
            "ganancia_total":  round(float(ganancia_total),  2),
            "roi":             round(float(roi_calc),        2),
            "notas":           notas or "",
            "creado_en":       datetime.utcnow().isoformat(),
        }).execute()

        lote_pk = resp_lote.data[0]["id"]

        # ── 2. Insertar ítems ──────────────────────────────────────────────────
        items_payload = []
        for item in resultados:
            items_payload.append({
                "lote_id_ref":      lote_pk,
                "nombre":           str(item.get("nombre", "")).strip(),
                "cantidad":         int(item.get("cantidad", 1)),
                "tienda":           str(item.get("tienda", "")),
                "costo_unitario":   round(float(item.get("precio_tienda")    or item.get("costo_unitario",  0)), 2),
                "flete_individual": round(float(item.get("envio_courier")    or item.get("flete_individual", 0)), 2),
                "costo_real":       round(float(item.get("costo_real",       0)), 2),
                "precio_venta":     round(float(item.get("precio_ml_objetivo") or item.get("precio_venta",  0)), 2),
                "ganancia_neta":    round(float(item.get("ganancia_objetivo") or item.get("ganancia_neta",  0)), 2),
                "margen_pct":       round(float(item.get("margen_pct",        0)), 2),
            })

        if items_payload:
            client.table(_T_ITEMS).insert(items_payload).execute()

        return True, lote_id_text

    except Exception as exc:
        return False, f"[SUPABASE ERROR] {type(exc).__name__}: {exc}"


# ════════════════════════════════════════════════════════════════════════════════
# LECTURA — HISTORIAL Y DASHBOARD
# ════════════════════════════════════════════════════════════════════════════════

def obtener_todos_los_lotes() -> List[Dict]:
    """Devuelve todos los lotes de import_lotes con conteo de ítems, orden desc."""
    try:
        client = _get_client()
        resp   = client.table(_T_LOTES).select("*").order("fecha", desc=True).execute()
        lotes  = resp.data or []

        for lote in lotes:
            resp_cnt = (
                client.table(_T_ITEMS)
                .select("id", count="exact")
                .eq("lote_id_ref", lote["id"])
                .execute()
            )
            lote["total_items"] = resp_cnt.count or 0

        return lotes
    except Exception as e:
        import warnings
        warnings.warn(f"Error obteniendo lotes desde Supabase: {e}")
        return []


def obtener_lote_por_id(lote_id_text: str) -> Optional[Dict]:
    """Devuelve el header del lote desde import_lotes por su lote_id_text."""
    try:
        client = _get_client()
        resp   = (
            client.table(_T_LOTES)
            .select("*")
            .eq("lote_id_text", lote_id_text)
            .order("id", desc=True)
            .limit(1)
            .execute()
        )
        rows = resp.data
        return rows[0] if rows else None
    except Exception as e:
        import warnings
        warnings.warn(f"Error obteniendo lote {lote_id_text} desde Supabase: {e}")
        return None


def obtener_items_de_lote(lote_id_text: str) -> List[Dict]:
    """Devuelve los ítems desde import_items_lote buscando por lote_id_text."""
    try:
        client    = _get_client()
        lote_data = obtener_lote_por_id(lote_id_text)
        if not lote_data:
            return []
        lote_pk = lote_data["id"]
        resp    = (
            client.table(_T_ITEMS)
            .select("*")
            .eq("lote_id_ref", lote_pk)
            .order("id")
            .execute()
        )
        return resp.data or []
    except Exception as e:
        import warnings
        warnings.warn(f"Error obteniendo ítems de {lote_id_text} desde Supabase: {e}")
        return []


def obtener_items_por_lote(lote_id_text: str) -> List[Dict]:
    """
    Alias enriquecido de obtener_items_de_lote.
    Devuelve ítems con claves duales para compatibilidad con _publicaciones.py
    y el resto de páginas que usan nombres distintos para los mismos campos.
    """
    items_raw = obtener_items_de_lote(lote_id_text)
    resultado = []
    for it in items_raw:
        resultado.append({
            "nombre":             it.get("nombre", ""),
            "cantidad":           it.get("cantidad", 1),
            "tienda":             it.get("tienda", ""),
            "costo_unitario":     it.get("costo_unitario", 0),
            "flete_individual":   it.get("flete_individual", 0),
            "costo_real":         it.get("costo_real", 0),
            "precio_venta":       it.get("precio_venta", 0),
            "ganancia_neta":      it.get("ganancia_neta", 0),
            "margen_pct":         it.get("margen_pct", 0),
            # Claves duales para compatibilidad
            "precio_tienda":      it.get("costo_unitario", 0),
            "envio_courier":      it.get("flete_individual", 0),
            "precio_ml_objetivo": it.get("precio_venta", 0),
            "precio_ml":          it.get("precio_venta", 0),
            "ganancia_objetivo":  it.get("ganancia_neta", 0),
        })
    return resultado


def obtener_estadisticas_globales() -> Dict:
    """Calcula KPIs agregados desde import_lotes e import_items_lote."""
    try:
        client = _get_client()

        resp  = client.table(_T_LOTES).select(
            "inversion_total, ganancia_total, roi, modo"
        ).execute()
        lotes = resp.data or []

        total_lotes    = len(lotes)
        inversion_acum = sum(float(l.get("inversion_total", 0)) for l in lotes)
        ganancia_acum  = sum(float(l.get("ganancia_total",  0)) for l in lotes)
        roi_vals       = [float(l.get("roi", 0)) for l in lotes if l.get("roi")]
        roi_promedio   = round(sum(roi_vals) / len(roi_vals), 2) if roi_vals else 0.0
        lotes_aereo    = sum(1 for l in lotes if l.get("modo") == "Aéreo")
        lotes_maritimo = sum(1 for l in lotes if l.get("modo") == "Marítimo")

        resp_items = client.table(_T_ITEMS).select("cantidad").execute()
        total_items = sum(int(i.get("cantidad", 0)) for i in (resp_items.data or []))

        return {
            "total_lotes":         total_lotes,
            "total_items":         total_items,
            "inversion_acumulada": round(inversion_acum, 2),
            "ganancia_acumulada":  round(ganancia_acum,  2),
            "roi_promedio":        roi_promedio,
            "lotes_aereo":         lotes_aereo,
            "lotes_maritimo":      lotes_maritimo,
        }
    except Exception as e:
        import warnings
        warnings.warn(f"Error obteniendo estadísticas desde Supabase: {e}")
        return {
            "total_lotes": 0, "total_items": 0,
            "inversion_acumulada": 0.0, "ganancia_acumulada": 0.0,
            "roi_promedio": 0.0, "lotes_aereo": 0, "lotes_maritimo": 0,
        }


# ════════════════════════════════════════════════════════════════════════════════
# VALIDACIONES
# ════════════════════════════════════════════════════════════════════════════════

def lote_id_existe(lote_id_text: str) -> bool:
    """Verifica si un lote_id_text ya existe en import_lotes."""
    try:
        client = _get_client()
        resp   = (
            client.table(_T_LOTES)
            .select("id", count="exact")
            .eq("lote_id_text", lote_id_text)
            .limit(1)
            .execute()
        )
        return (resp.count or 0) > 0
    except Exception:
        return False


def obtener_siguiente_id_lote(prefijo: str) -> str:
    """
    Calcula el siguiente número correlativo para un prefijo dado.
    Ej: prefijo='AER' → busca AER-001, AER-002... → retorna '003'
    """
    patron = f"{prefijo.upper().strip()}-"
    try:
        client = _get_client()
        resp   = (
            client.table(_T_LOTES)
            .select("lote_id_text")
            .like("lote_id_text", f"{patron}%")
            .execute()
        )
        rows = resp.data or []
    except Exception:
        rows = []

    maximo = 0
    for row in rows:
        sufijo = str(row.get("lote_id_text", ""))[len(patron):]
        try:
            num = int(sufijo)
            if num > maximo:
                maximo = num
        except ValueError:
            continue

    return f"{maximo + 1:03d}"


# ════════════════════════════════════════════════════════════════════════════════
# UTILIDADES
# ════════════════════════════════════════════════════════════════════════════════

def obtener_ruta_db() -> str:
    """En Supabase devuelve la URL del proyecto en lugar de una ruta de archivo."""
    url, _ = _get_credentials()
    return url or "Supabase (URL no configurada)"


def obtener_version_schema() -> str:
    """Versión del schema — en Supabase se devuelve un valor fijo."""
    return "supabase-v1"


# ── Auto-verificación de conectividad al importar ────────────────────────────
try:
    inicializar_db()
except Exception as _init_exc:
    import warnings
    warnings.warn(f"ADALIMPORT Supabase: No se pudo verificar conexión → {_init_exc}")
