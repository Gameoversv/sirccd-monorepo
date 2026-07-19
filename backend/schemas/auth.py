"""
Schemas de Autenticación (Pydantic)
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from models.user import UserRole


# Schema para login (credenciales)
class LoginRequest(BaseModel):
    """Schema para solicitud de login"""
    username: str = Field(..., description="Username o email")
    password: str = Field(..., description="Contraseña")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "juanperez",
                "password": "securePassword123!"
            }
        }
    )


# Schema para respuesta de token
class Token(BaseModel):
    """Schema de respuesta con token JWT"""
    access_token: str = Field(..., description="Token de acceso JWT")
    token_type: str = Field(default="bearer", description="Tipo de token")
    expires_in: int = Field(..., description="Tiempo de expiración en segundos")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800
            }
        }
    )


# Schema para respuesta de login completa
class LoginResponse(Token):
    """Schema de respuesta de login incluyendo datos del usuario"""
    refresh_token: str = Field(..., description="Refresh token JWT (válido 7 días)")
    user_id: int = Field(..., description="ID del usuario")
    username: str = Field(..., description="Nombre de usuario")
    email: EmailStr = Field(..., description="Email del usuario")
    role: UserRole = Field(..., description="Rol del usuario")
    full_name: Optional[str] = Field(None, description="Nombre completo")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "user_id": 1,
                "username": "juanperez",
                "email": "juan.perez@example.com",
                "role": "ciudadano",
                "full_name": "Juan Pérez"
            }
        }
    )


# Schema para refresh token
class RefreshTokenRequest(BaseModel):
    """Schema para solicitar un nuevo access token con refresh token"""
    refresh_token: str = Field(..., description="Refresh token JWT")


# Schema para datos del token decodificado (payload)
class TokenPayload(BaseModel):
    """Schema del payload del token JWT"""
    sub: str = Field(..., description="Subject (user_id)")
    exp: int = Field(..., description="Expiration timestamp")
    iat: int = Field(..., description="Issued at timestamp")
    type: str = Field(default="access", description="Tipo de token (access/refresh)")


# Schema para registro de nuevo usuario
class RegisterRequest(BaseModel):
    """Schema para solicitud de registro de usuario"""
    email: EmailStr = Field(..., description="Email único del usuario")
    username: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Nombre de usuario único"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Contraseña (mínimo 8 caracteres)"
    )
    full_name: Optional[str] = Field(None, max_length=255, description="Nombre completo")
    phone: Optional[str] = Field(None, max_length=20, description="Teléfono")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "maria.garcia@example.com",
                "username": "mariagarcia",
                "password": "securePassword456!",
                "full_name": "María García",
                "phone": "+1809-555-9876"
            }
        }
    )


# Schema para respuesta de registro exitoso
class RegisterResponse(BaseModel):
    """Schema de respuesta de registro"""
    message: str = Field(..., description="Mensaje de confirmación")
    user_id: int = Field(..., description="ID del usuario creado")
    username: str = Field(..., description="Nombre de usuario")
    email: EmailStr = Field(..., description="Email del usuario")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Usuario registrado exitosamente",
                "user_id": 2,
                "username": "mariagarcia",
                "email": "maria.garcia@example.com"
            }
        }
    )


# Schema para verificación de token
class TokenVerification(BaseModel):
    """Schema para respuesta de verificación de token"""
    valid: bool = Field(..., description="Si el token es válido")
    user_id: Optional[int] = Field(None, description="ID del usuario si es válido")
    role: Optional[UserRole] = Field(None, description="Rol del usuario si es válido")
    expires_at: Optional[int] = Field(None, description="Timestamp de expiración")
