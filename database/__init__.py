# ═══════════════════════════════════════════════════════════════
# ADALIMPORT · database/__init__.py
# Marca la carpeta `database` como paquete Python.
# Expone las funciones principales de db_manager directamente
# desde `database` para imports más cortos si se desea.
# ═══════════════════════════════════════════════════════════════
from .db_manager import (
    inicializar_db,
    guardar_lote_aprobado,
    obtener_todos_los_lotes,
    obtener_lote_por_id,
    obtener_items_de_lote,
    obtener_estadisticas_globales,
    lote_id_existe,
    obtener_ruta_db,
    obtener_version_schema,
)

__all__ = [
    "inicializar_db",
    "guardar_lote_aprobado",
    "obtener_todos_los_lotes",
    "obtener_lote_por_id",
    "obtener_items_de_lote",
    "obtener_estadisticas_globales",
    "lote_id_existe",
    "obtener_ruta_db",
    "obtener_version_schema",
]
