"""
Schemas de Usuario (Pydantic)
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from models.user import UserRole


# Schema base con campos comunes
class UserBase(BaseModel):
    """Schema base de usuario"""
    email: EmailStr = Field(..., description="Email único del usuario")
    username: str = Field(..., min_length=3, max_length=100, description="Nombre de usuario único")
    full_name: Optional[str] = Field(None, max_length=255, description="Nombre completo")
    phone: Optional[str] = Field(None, max_length=20, description="Teléfono")
    role: UserRole = Field(default=UserRole.CIUDADANO, description="Rol del usuario")


# Schema para creación de usuario (incluye password)
class UserCreate(UserBase):
    """Schema para crear un usuario nuevo"""
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Contraseña (mínimo 8 caracteres)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "juan.perez@example.com",
                "username": "juanperez",
                "full_name": "Juan Pérez",
                "phone": "+1809-555-0123",
                "role": "ciudadano",
                "password": "securePassword123!"
            }
        }
    )


# Schema para actualización de usuario (todos los campos opcionales)
class UserUpdate(BaseModel):
    """Schema para actualizar un usuario existente"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


# Schema para respuesta de usuario (lo que se devuelve en la API)
class UserResponse(UserBase):
    """Schema de respuesta con datos del usuario (sin password)"""
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "email": "juan.perez@example.com",
                "username": "juanperez",
                "full_name": "Juan Pérez",
                "phone": "+1809-555-0123",
                "role": "ciudadano",
                "is_active": True,
                "is_verified": True,
                "created_at": "2026-02-26T10:30:00",
                "updated_at": "2026-02-26T10:30:00",
                "last_login": "2026-02-26T15:45:00"
            }
        }
    )


# Schema simplificado para listados
class UserListItem(BaseModel):
    """Schema simplificado para listados de usuarios"""
    id: int
    username: str
    email: EmailStr
    full_name: Optional[str]
    role: UserRole
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)


# Schema para cambio de contraseña
class PasswordChange(BaseModel):
    """Schema para cambiar contraseña"""
    current_password: str = Field(..., description="Contraseña actual")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Nueva contraseña (mínimo 8 caracteres)"
    )
    confirm_password: str = Field(..., description="Confirmación de nueva contraseña")
    
    def passwords_match(self) -> bool:
        """Verificar que las contraseñas coincidan"""
        return self.new_password == self.confirm_password
