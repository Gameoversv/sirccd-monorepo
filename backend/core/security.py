"""
Utilidades de seguridad: JWT, password hashing, etc.
"""

from datetime import datetime, timedelta
from typing import Optional, Any
from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import settings


# Configuración de Passlib para bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verificar que una contraseña en texto plano coincida con el hash.
    
    Args:
        plain_password: Contraseña en texto plano
        hashed_password: Hash almacenado en la base de datos
        
    Returns:
        True si coinciden, False en caso contrario
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Generar hash bcrypt de una contraseña.
    
    Args:
        password: Contraseña en texto plano
        
    Returns:
        Hash bcrypt de la contraseña
    """
    return pwd_context.hash(password)


def create_access_token(
    subject: str | int,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[dict[str, Any]] = None
) -> str:
    """
    Crear un token JWT de acceso.
    
    Args:
        subject: Identificador del usuario (generalmente user_id)
        expires_delta: Tiempo de expiración (por defecto usa configured value)
        additional_claims: Claims adicionales para incluir en el token
        
    Returns:
        Token JWT firmado
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    # Payload del token
    to_encode = {
        "exp": expire,
        "sub": str(subject),  # Subject debe ser string según JWT spec
        "iat": datetime.utcnow(),  # Issued at
    }
    
    # Agregar claims adicionales si existen
    if additional_claims:
        to_encode.update(additional_claims)
    
    # Firmar y codificar el token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    """
    Decodificar y validar un token JWT.
    
    Args:
        token: Token JWT a decodificar
        
    Returns:
        Payload del token si es válido, None si es inválido o expirado
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def create_refresh_token(subject: str | int, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crear un refresh token JWT (con mayor duración).
    
    Args:
        subject: Identificador del usuario
        expires_delta: Tiempo de expiración (por defecto 7 días)
        
    Returns:
        Refresh token JWT firmado
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Refresh tokens duran más (7 días por defecto)
        expire = datetime.utcnow() + timedelta(days=7)
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "iat": datetime.utcnow(),
        "type": "refresh",  # Marcar como refresh token
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def validate_token_type(token: str, expected_type: str = "access") -> bool:
    """
    Validar que un token sea del tipo esperado.
    
    Args:
        token: Token JWT
        expected_type: Tipo esperado ("access" o "refresh")
        
    Returns:
        True si el token es del tipo esperado
    """
    payload = decode_access_token(token)
    if not payload:
        return False
    
    token_type = payload.get("type", "access")  # Por defecto es access
    return token_type == expected_type
