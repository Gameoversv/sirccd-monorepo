"""
Firma HMAC para las URLs de imagenes servidas por el proxy del backend.

El bucket de MinIO es privado: las imagenes se sirven por
`/{scope}/{id}/image`, que valida una firma de corta duracion. Asi el
navegador puede usarlas en `<img src>` (donde no se puede mandar el header
Authorization) sin exponer MinIO a internet.
"""

import base64
import hashlib
import hmac
import time
from typing import Optional

from core.config import settings

DEFAULT_TTL_SECONDS = 3600


def _digest(scope: str, obj_id: int, variant: str, exp: int) -> str:
    message = f"{scope}:{obj_id}:{variant}:{exp}".encode()
    mac = hmac.new(settings.SECRET_KEY.encode(), message, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(mac).decode().rstrip("=")


def sign_image_url(
    scope: str,
    obj_id: int,
    variant: str,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> str:
    """
    Construye la URL firmada del proxy de imagenes.

    Args:
        scope: Prefijo del router ('reportes' o 'incidentes')
        obj_id: ID del reporte o incidente
        variant: Variante de la imagen ('original', 'annotated', 'before', 'after')
        ttl_seconds: Vigencia de la firma

    Returns:
        Ruta relativa, ej: /api/v1/reportes/12/image?variant=original&exp=...&sig=...
    """
    exp = int(time.time()) + ttl_seconds
    sig = _digest(scope, obj_id, variant, exp)
    return (
        f"{settings.API_V1_STR}/{scope}/{obj_id}/image"
        f"?variant={variant}&exp={exp}&sig={sig}"
    )


def verify_image_signature(
    scope: str,
    obj_id: int,
    variant: str,
    exp: Optional[int],
    sig: Optional[str],
) -> bool:
    """Valida firma y vigencia. Devuelve False ante cualquier inconsistencia."""
    if exp is None or not sig:
        return False
    if exp < int(time.time()):
        return False
    return hmac.compare_digest(_digest(scope, obj_id, variant, exp), sig)
