# ══════════════════════════════════════════════════════════════════════════════
# ADALIMPORT · publicador_imagenes.py  ·  v2.0 — Módulo Backend (Supabase Storage)
# ══════════════════════════════════════════════════════════════════════════════
# Responsabilidad única: Subir imágenes (bytes PNG) al bucket de Supabase
# Storage y retornar la URL pública resultante.
#
# REGLA DE ARQUITECTURA: Este módulo es puramente transaccional.
# No contiene UI, estilos CSS ni lógica de negocio de ADALIMPORT.
#
# Credenciales requeridas en .streamlit/secrets.toml:
#
#   [supabase]
#   url = "https://<tu-proyecto>.supabase.co"
#   key = "<tu-anon-o-service-role-key>"
#
# BUCKET FIJO: "adalimport_catalogo_temp" (hardcoded por diseño de arquitectura)
#
# ── CAMBIOS v2.0 ─────────────────────────────────────────────────────────────
# · Fix: lectura de secrets via st.secrets["supabase"]["url"] / ["key"]
#   (compatible con .streamlit/secrets.toml — resuelve StreamlitSecretNotFoundError)
# · Bucket fijo: "adalimport_catalogo_temp" (ya no se lee de secrets.toml)
# · La función retorna SIEMPRE la URL pública como str (o "" si falla)
# ══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations

import streamlit as st
from supabase import create_client, Client

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTE DE ARQUITECTURA
# El bucket es fijo por diseño: toda la infraestructura de ADALIMPORT usa
# "adalimport_catalogo_temp" como destino de imágenes procesadas.
# ─────────────────────────────────────────────────────────────────────────────
_BUCKET_ADALIMPORT: str = "adalimport_catalogo_temp"


# ─────────────────────────────────────────────────────────────────────────────
# INICIALIZACIÓN EN CACHÉ
# Se ejecuta una sola vez por sesión gracias a @st.cache_resource.
# Lee las credenciales directamente de st.secrets para evitar
# StreamlitSecretNotFoundError (el patrón correcto para secrets.toml).
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_resource
def _get_supabase_client() -> Client:
    """
    Inicializa y cachea el cliente de Supabase para toda la sesión.
    Lee las credenciales desde st.secrets["supabase"].

    El bloque esperado en .streamlit/secrets.toml es:

        [supabase]
        url = "https://<proyecto>.supabase.co"
        key = "<anon-key-o-service-role-key>"

    Returns:
        Client: Instancia autenticada del cliente Supabase.

    Raises:
        KeyError: Si las claves 'url' o 'key' no existen en secrets.toml.
        StreamlitSecretNotFoundError: Si la sección [supabase] no existe.
    """
    url: str = st.secrets["supabase"]["url"]
    key: str = st.secrets["supabase"]["key"]
    return create_client(url, key)


# ─────────────────────────────────────────────────────────────────────────────
# FUNCIÓN PRINCIPAL DE PUBLICACIÓN
# ─────────────────────────────────────────────────────────────────────────────

def subir_imagen_a_supabase(datos_imagen: bytes, nombre_archivo: str) -> str:
    """
    Sube una imagen en bytes al bucket "adalimport_catalogo_temp" de Supabase
    Storage y retorna su URL pública.

    Comportamiento:
    - El bucket de destino es SIEMPRE "adalimport_catalogo_temp" (fijo).
    - Si el archivo ya existe en el bucket, lo sobreescribe (upsert=true).
    - Si ocurre cualquier error durante la subida, retorna "" y muestra aviso.

    Args:
        datos_imagen (bytes): Contenido binario de la imagen (formato PNG).
        nombre_archivo (str): Ruta/nombre de destino dentro del bucket.
                              Ej: "catalogos/lote_AER-001/freidora_ml.png"

    Returns:
        str: URL pública completa de la imagen subida.
             Retorna "" si la operación falla.
    """
    # ── Guard: payload vacío ──────────────────────────────────────────────────
    if not datos_imagen:
        st.warning(
            "⚠️ publicador_imagenes: Se recibió un payload de imagen vacío. "
            "Operación cancelada."
        )
        return ""

    # ── Guard: nombre de archivo vacío ───────────────────────────────────────
    if not nombre_archivo or not nombre_archivo.strip():
        st.warning(
            "⚠️ publicador_imagenes: El nombre de archivo no puede estar vacío. "
            "Operación cancelada."
        )
        return ""

    # ── Obtener cliente cacheado ──────────────────────────────────────────────
    try:
        cliente: Client = _get_supabase_client()
    except Exception as e_init:
        st.error(
            f"🔑 Error de credenciales Supabase: `{e_init}`\n\n"
            f"Verifica que `.streamlit/secrets.toml` contenga:\n\n"
            f"```toml\n[supabase]\nurl = \"https://...\"\nkey = \"...\"\n```"
        )
        return ""

    # ── Subir imagen al bucket fijo ───────────────────────────────────────────
    try:
        cliente.storage.from_(_BUCKET_ADALIMPORT).upload(
            file=datos_imagen,
            path=nombre_archivo,
            file_options={
                "content-type": "image/png",
                "x-upsert":     "true",   # Sobrescribe si el archivo ya existe
            },
        )
    except Exception as e_upload:
        # Captura StorageException y cualquier error de red o autenticación
        print(
            f"[ADALIMPORT][publicador_imagenes] ERROR al subir "
            f"'{nombre_archivo}' → bucket '{_BUCKET_ADALIMPORT}': {e_upload}"
        )
        st.warning(
            f"⚠️ No se pudo subir `{nombre_archivo}` a Supabase Storage "
            f"(bucket: `{_BUCKET_ADALIMPORT}`). Detalle: `{e_upload}`"
        )
        return ""

    # ── Subida exitosa: obtener y retornar URL pública ────────────────────────
    url_publica: str = cliente.storage.from_(_BUCKET_ADALIMPORT).get_public_url(
        nombre_archivo
    )
    return url_publica
