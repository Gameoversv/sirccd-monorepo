"""
S-03 — Cifrado de campos sensibles en base de datos.

Usa Fernet (AES-128-CBC + HMAC-SHA256) de la librería `cryptography`.
Se aplica como SQLAlchemy TypeDecorator para cifrado/descifrado transparente.

Configuración: FIELD_ENCRYPTION_KEY en .env
Generar clave: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

Comportamiento sin clave configurada:
- Dev: datos se almacenan en texto plano con WARNING al arrancar.
- Producción: FIELD_ENCRYPTION_KEY debe estar presente (validar en startup).
"""

import logging
from typing import Optional

from sqlalchemy import String
from sqlalchemy.types import TypeDecorator

from core.config import settings

logger = logging.getLogger(__name__)

_fernet_instance = None
_encryption_warned = False


def _get_fernet():
    """Lazy singleton del cifrador Fernet. Retorna None si no hay clave."""
    global _fernet_instance, _encryption_warned

    if _fernet_instance is not None:
        return _fernet_instance

    key = settings.FIELD_ENCRYPTION_KEY
    if not key:
        if not _encryption_warned:
            logger.warning(
                "[S-03] FIELD_ENCRYPTION_KEY no configurada. "
                "Campos sensibles se almacenan SIN cifrar. "
                "Configurar en producción."
            )
            _encryption_warned = True
        return None

    try:
        from cryptography.fernet import Fernet, InvalidToken
        _fernet_instance = Fernet(key.encode() if isinstance(key, str) else key)
        logger.info("[S-03] Cifrado de campos activo (Fernet AES-128-CBC).")
        return _fernet_instance
    except Exception as e:
        logger.error("[S-03] FIELD_ENCRYPTION_KEY inválida: %s. Campos sin cifrar.", e)
        return None


def encrypt_value(value: str) -> str:
    """Cifra un string con Fernet. Retorna texto plano si no hay clave."""
    f = _get_fernet()
    if f is None:
        return value
    return f.encrypt(value.encode()).decode()


def decrypt_value(value: str) -> str:
    """Descifra un string con Fernet. Retorna el valor tal cual si no hay clave o falla."""
    f = _get_fernet()
    if f is None:
        return value
    try:
        from cryptography.fernet import InvalidToken
        return f.decrypt(value.encode()).decode()
    except (InvalidToken, Exception):
        # Dato puede estar en texto plano (migración gradual)
        logger.debug("[S-03] No se pudo descifrar valor; se retorna sin descifrar.")
        return value


class EncryptedString(TypeDecorator):
    """
    Tipo SQLAlchemy que cifra con Fernet en escritura y descifra en lectura.

    Uso:
        phone = Column(EncryptedString(50), nullable=True)

    El cifrado es transparente: el código de negocio siempre trabaja
    con texto plano; el cifrado ocurre solo al interactuar con la BD.
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Cifra antes de INSERT/UPDATE."""
        if value is None:
            return None
        return encrypt_value(str(value))

    def process_result_value(self, value, dialect):
        """Descifra después de SELECT."""
        if value is None:
            return None
        return decrypt_value(value)
