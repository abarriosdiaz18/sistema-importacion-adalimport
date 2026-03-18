"""
ADALIMPORT · database/db_manager.py
════════════════════════════════════════════════════════════════════════════════
Módulo Core — Gestor de Base de Datos SQLite
Responsabilidad única: toda la lógica de persistencia de lotes aprobados y configuración.

Tablas:
  · lotes                 — resumen del lote (1 fila por aprobación)
  · items_lote            — detalle de ítems (N filas por lote, FK → lotes)
  · configuracion_sistema — variables dinámicas del negocio (comisiones, tarifas)
════════════════════════════════════════════════════════════════════════════════
"""

import sqlite3
import os
import json
from datetime import date, datetime
from typing import List, Dict, Any, Optional, Tuple


# ── Ruta canónica de la BD ────────────────────────────────────────────────────
_BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))
DB_PATH   = os.path.join(_BASE_DIR, "adalimport.db")


# ════════════════════════════════════════════════════════════════════════════════
# INICIALIZACIÓN
# ════════════════════════════════════════════════════════════════════════════════

def _ensure_db_dir() -> None:
    """Crea la carpeta /database si no existe."""
    os.makedirs(_BASE_DIR, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    """
    Devuelve una conexión SQLite con:
      · Row factory activada (acceso por nombre de columna)
      · WAL journal para mayor concurrencia
      · Foreign keys habilitadas
    """
    _ensure_db_dir()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def inicializar_db() -> None:
    """
    Crea las tablas si no existen.
    Idempotente — se puede llamar en cada arranque de la app sin riesgo.
    """
    _ensure_db_dir()
    conn = get_connection()
    try:
        conn.executescript("""
            -- ── Tabla principal: resumen de lotes ────────────────────────────
            CREATE TABLE IF NOT EXISTS lotes (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                lote_id_text    TEXT    NOT NULL,          -- "AER-001", "MAR-002", etc.
                fecha           TEXT    NOT NULL,          -- ISO-8601: "2024-11-15"
                courier         TEXT,                      -- nombre del courier
                modo            TEXT    NOT NULL           -- "Aéreo" | "Marítimo"
                                    CHECK(modo IN ('Aéreo','Marítimo')),
                origen          TEXT,                      -- "us" | "cn"
                costo_flete     REAL    NOT NULL DEFAULT 0,
                inversion_total REAL    NOT NULL DEFAULT 0,
                ganancia_total  REAL    NOT NULL DEFAULT 0,
                roi             REAL    NOT NULL DEFAULT 0,
                notas           TEXT,
                creado_en       TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
            );

            -- ── Tabla de detalle: ítems por lote ─────────────────────────────
            CREATE TABLE IF NOT EXISTS items_lote (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                lote_id_ref     INTEGER NOT NULL
                                    REFERENCES lotes(id) ON DELETE CASCADE,
                nombre          TEXT    NOT NULL,
                cantidad        INTEGER NOT NULL DEFAULT 1,
                tienda          TEXT,
                costo_unitario  REAL    NOT NULL DEFAULT 0,  -- precio en tienda
                flete_individual REAL   NOT NULL DEFAULT 0,  -- flete prorrateado
                costo_real      REAL    NOT NULL DEFAULT 0,  -- costo_unitario + flete + seg.
                precio_venta    REAL    NOT NULL DEFAULT 0,  -- precio_ml_objetivo
                ganancia_neta   REAL    NOT NULL DEFAULT 0,  -- ganancia_objetivo
                margen_pct      REAL    NOT NULL DEFAULT 0
            );

            -- ── Tabla de Configuración: variables de negocio (Fila única) ────
            CREATE TABLE IF NOT EXISTS configuracion_sistema (
                id              INTEGER PRIMARY KEY CHECK (id = 1),
                datos_json      TEXT NOT NULL,
                actualizado_en  TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            );

            -- ── Índices de búsqueda frecuente ────────────────────────────────
            CREATE INDEX IF NOT EXISTS idx_lotes_lote_id_text
                ON lotes(lote_id_text);

            CREATE INDEX IF NOT EXISTS idx_items_lote_ref
                ON items_lote(lote_id_ref);
        """)
        conn.commit()
    finally:
        conn.close()


# ════════════════════════════════════════════════════════════════════════════════
# PERSISTENCIA DE CONFIGURACIÓN MAESTRA
# ════════════════════════════════════════════════════════════════════════════════

def guardar_configuracion(config_dict: dict) -> bool:
    """Guarda el diccionario de configuración en la BD como JSON."""
    conn = get_connection()
    try:
        datos_str = json.dumps(config_dict)
        conn.execute("""
            INSERT INTO configuracion_sistema (id, datos_json, actualizado_en)
            VALUES (1, ?, datetime('now','localtime'))
            ON CONFLICT(id) DO UPDATE SET
                datos_json = excluded.datos_json,
                actualizado_en = excluded.actualizado_en;
        """, (datos_str,))
        conn.commit()
        return True
    except Exception as e:
        import warnings
        warnings.warn(f"Error guardando configuración en DB: {e}")
        return False
    finally:
        conn.close()

def cargar_configuracion() -> dict:
    """Carga y devuelve el diccionario de configuración desde la BD."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT datos_json FROM configuracion_sistema WHERE id = 1").fetchone()
        if row and row["datos_json"]:
            return json.loads(row["datos_json"])
        return {}
    except Exception as e:
        import warnings
        warnings.warn(f"Error cargando configuración desde DB: {e}")
        return {}
    finally:
        conn.close()


# ════════════════════════════════════════════════════════════════════════════════
# ESCRITURA — GUARDAR LOTE APROBADO (TRANSACCIÓN ATÓMICA)
# ════════════════════════════════════════════════════════════════════════════════

def guardar_lote_aprobado(
    lote_id_text:    str,
    fecha:           date,
    courier:         str,
    modo:            str,          # "aereo" | "maritimo"  (se normaliza internamente)
    origen:          str,          # "us" | "cn"
    costo_flete:     float,
    inversion_total: float,
    ganancia_total:  float,
    roi:             float,
    notas:           str,
    resultados:      List[Dict[str, Any]],
) -> Tuple[bool, str]:
    """
    Guarda el lote completo en SQLite usando una transacción atómica.
    """
    modo_norm = "Aéreo" if modo.lower() in ("aereo", "aéreo", "aero") else "Marítimo"

    roi_calc = roi if roi is not None else (
        round((ganancia_total / inversion_total * 100), 2)
        if inversion_total and inversion_total > 0 else 0.0
    )

    conn = get_connection()
    try:
        conn.execute("BEGIN")

        cursor = conn.execute(
            """
            INSERT INTO lotes
                (lote_id_text, fecha, courier, modo, origen,
                 costo_flete, inversion_total, ganancia_total, roi, notas)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lote_id_text,
                fecha.isoformat() if isinstance(fecha, date) else str(fecha),
                courier or "",
                modo_norm,
                origen or "",
                round(float(costo_flete),     2),
                round(float(inversion_total), 2),
                round(float(ganancia_total),  2),
                round(float(roi_calc),        2),
                notas or "",
            )
        )
        lote_pk = cursor.lastrowid

        for item in resultados:
            _nombre   = str(item.get("nombre", "")).strip()
            _cantidad = int(item.get("cantidad", 1))
            _tienda   = str(item.get("tienda", ""))

            _costo_u  = float(
                item.get("precio_tienda") or
                item.get("costo_warehouse") or
                item.get("costo_unitario") or 0
            )
            _flete_i  = float(item.get("envio_courier") or item.get("flete_individual") or 0)
            _costo_r  = float(item.get("costo_real", 0))
            _p_venta  = float(item.get("precio_ml_objetivo") or item.get("precio_venta") or 0)
            _gan_neta = float(item.get("ganancia_objetivo") or item.get("ganancia_neta") or 0)
            _margen   = float(item.get("margen_pct", 0))

            conn.execute(
                """
                INSERT INTO items_lote
                    (lote_id_ref, nombre, cantidad, tienda,
                     costo_unitario, flete_individual, costo_real,
                     precio_venta, ganancia_neta, margen_pct)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lote_pk,
                    _nombre,
                    _cantidad,
                    _tienda,
                    round(_costo_u,  2),
                    round(_flete_i,  2),
                    round(_costo_r,  2),
                    round(_p_venta,  2),
                    round(_gan_neta, 2),
                    round(_margen,   2),
                )
            )

        conn.commit()
        return True, lote_id_text

    except Exception as exc:
        conn.rollback()
        return False, f"[DB ERROR] {type(exc).__name__}: {exc}"

    finally:
        conn.close()


# ════════════════════════════════════════════════════════════════════════════════
# LECTURA — CONSULTAS PARA HISTORIAL / DASHBOARD
# ════════════════════════════════════════════════════════════════════════════════

def obtener_todos_los_lotes() -> List[Dict]:
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT
                l.*,
                COUNT(i.id) AS total_items
            FROM lotes l
            LEFT JOIN items_lote i ON i.lote_id_ref = l.id
            GROUP BY l.id
            ORDER BY l.fecha DESC, l.creado_en DESC
        """).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def obtener_lote_por_id(lote_id_text: str) -> Optional[Dict]:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM lotes WHERE lote_id_text = ? ORDER BY id DESC LIMIT 1",
            (lote_id_text,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def obtener_items_de_lote(lote_id_text: str) -> List[Dict]:
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT i.*
            FROM items_lote i
            INNER JOIN lotes l ON l.id = i.lote_id_ref
            WHERE l.lote_id_text = ?
            ORDER BY i.id
        """, (lote_id_text,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def obtener_estadisticas_globales() -> Dict:
    conn = get_connection()
    try:
        agg = conn.execute("""
            SELECT
                COUNT(*)                   AS total_lotes,
                SUM(inversion_total)       AS inversion_acumulada,
                SUM(ganancia_total)        AS ganancia_acumulada,
                AVG(roi)                   AS roi_promedio,
                SUM(CASE WHEN modo='Aéreo'    THEN 1 ELSE 0 END) AS lotes_aereo,
                SUM(CASE WHEN modo='Marítimo' THEN 1 ELSE 0 END) AS lotes_maritimo
            FROM lotes
        """).fetchone()

        items_total = conn.execute(
            "SELECT COALESCE(SUM(cantidad), 0) FROM items_lote"
        ).fetchone()[0]

        return {
            "total_lotes":        agg["total_lotes"] or 0,
            "total_items":        items_total or 0,
            "inversion_acumulada": round(float(agg["inversion_acumulada"] or 0), 2),
            "ganancia_acumulada":  round(float(agg["ganancia_acumulada"]  or 0), 2),
            "roi_promedio":        round(float(agg["roi_promedio"]        or 0), 2),
            "lotes_aereo":        agg["lotes_aereo"]    or 0,
            "lotes_maritimo":     agg["lotes_maritimo"] or 0,
        }
    finally:
        conn.close()


def obtener_items_por_lote(lote_id_text: str) -> List[Dict]:
    items_raw = obtener_items_de_lote(lote_id_text)
    resultado = []
    for it in items_raw:
        resultado.append({
            "nombre":           it.get("nombre", ""),
            "cantidad":         it.get("cantidad", 1),
            "tienda":           it.get("tienda", ""),
            "costo_unitario":   it.get("costo_unitario", 0),
            "flete_individual": it.get("flete_individual", 0),
            "costo_real":       it.get("costo_real", 0),
            "precio_venta":     it.get("precio_venta", 0),
            "ganancia_neta":    it.get("ganancia_neta", 0),
            "margen_pct":       it.get("margen_pct", 0),
            "precio_tienda":    it.get("costo_unitario", 0),
            "envio_courier":    it.get("flete_individual", 0),
            "precio_ml_objetivo": it.get("precio_venta", 0),
            "precio_ml":        it.get("precio_venta", 0),
            "ganancia_objetivo": it.get("ganancia_neta", 0),
        })
    return resultado


def lote_id_existe(lote_id_text: str) -> bool:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT 1 FROM lotes WHERE lote_id_text = ? LIMIT 1",
            (lote_id_text,)
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def obtener_siguiente_id_lote(prefijo: str) -> str:
    patron = f"{prefijo.upper().strip()}-"
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT lote_id_text FROM lotes WHERE lote_id_text LIKE ?",
            (f"{patron}%",)
        ).fetchall()
    finally:
        conn.close()

    maximo = 0
    for row in rows:
        sufijo = str(row["lote_id_text"])[len(patron):]
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
    return os.path.abspath(DB_PATH)

def obtener_version_schema() -> str:
    conn = get_connection()
    try:
        v = conn.execute("PRAGMA user_version;").fetchone()[0]
        return str(v)
    finally:
        conn.close()

try:
    inicializar_db()
except Exception as _init_exc:
    import warnings
    warnings.warn(f"ADALIMPORT DB: No se pudo inicializar la BD → {_init_exc}")