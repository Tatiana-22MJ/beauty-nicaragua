# =============================================================================
# supabase_storage.py — Comprobantes de pago en Supabase Storage
# =============================================================================
#
# Estrategia senior: la app funciona con o sin Supabase.
#   - Si SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY están definidos → Storage.
#   - Si no → disco local (instance/uploads), ideal para desarrollo.
# La clave service_role se usa SOLO server-side; nunca exponerla al frontend.

import logging

from flask import current_app

logger = logging.getLogger("beauty.supabase")

_client = None  # Cliente supabase-py inicializado lazy (uno por proceso).


def get_client():
    """Cliente admin de Supabase o None si no está configurado."""
    url = current_app.config.get("SUPABASE_URL") or ""
    key = current_app.config.get("SUPABASE_SERVICE_ROLE_KEY") or ""
    if not url or not key:
        return None

    global _client
    if _client is None:
        try:
            from supabase import create_client

            _client = create_client(url, key)
        except Exception:
            logger.exception("No se pudo inicializar el cliente de Supabase")
            return None
    return _client


def _ensure_bucket(client, bucket: str) -> bool:
    """Crea el bucket privado si no existe (idempotente, tolerante a fallos)."""
    try:
        buckets = client.storage.list_buckets() or []
        if any(getattr(b, "name", None) == bucket for b in buckets):
            return True
        client.storage.create_bucket(bucket)
        logger.info("Bucket de Supabase Storage creado: %s", bucket)
        return True
    except Exception:
        # Si la creación falla porque ya existe (carrera), la subi\u00f3 igual puede funcionar.
        logger.warning("No se pudo verificar/crear el bucket %s; se intentará subir igual.", bucket)
        return True


def upload_proof(data: bytes, filename: str, content_type: str = "application/octet-stream") -> str | None:
    """Sube un comprobante al bucket privado. Devuelve el path o None si falló.

    En caso de fallo el llamante debe hacer fallback a disco local.
    """
    client = get_client()
    if client is None:
        return None

    bucket = current_app.config.get("SUPABASE_BUCKET_PROOFS", "payment-proofs")
    path = f"comprobantes/{filename}"
    try:
        _ensure_bucket(client, bucket)
        client.storage.from_(bucket).upload(path, data, {"content-type": content_type})
        logger.info("Comprobante subido a Supabase Storage: %s", path)
        return path
    except Exception:
        logger.exception("Fallo subiendo comprobante a Supabase; se usará disco local")
        return None


def proof_signed_url(path: str, expires_in: int = 3600) -> str | None:
    """URL firmada (temporal) para que el admin visualice el comprobante."""
    client = get_client()
    if client is None:
        return None

    bucket = current_app.config.get("SUPABASE_BUCKET_PROOFS", "payment-proofs")
    try:
        result = client.storage.from_(bucket).create_signed_url(path, expires_in)
        url = None
        if isinstance(result, dict):
            url = result.get("signedURL") or result.get("signedUrl")
        if url and not url.startswith("http"):
            url = f"{client.storage_url.rstrip('/')}/{url.lstrip('/')}"
        return url
    except Exception:
        logger.exception("Fallo generando URL firmada para %s", path)
        return None
