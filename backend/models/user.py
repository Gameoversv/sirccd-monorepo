"""
Modelo de Usuario
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from db.base import Base
from core.field_encryption import EncryptedString


class UserRole(str, enum.Enum):
    """Roles de usuario"""
    ADMIN = "admin"
    CIUDADANO = "ciudadano"
    SUPERVISOR = "supervisor"


class User(Base):
    """
    Modelo de Usuario
    
    Representa a los usuarios del sistema: ciudadanos, brigadistas, supervisores y administradores.
    """
    __tablename__ = "users"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Información básica
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    phone = Column(EncryptedString(200), nullable=True)  # S-03: cifrado en BD
    
    # Autenticación
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Rol
    role = Column(SQLEnum(UserRole), default=UserRole.CIUDADANO, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relaciones
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="reported_by_user", foreign_keys="Incident.reported_by")
    
    def __repr__(self):
        return f"<User {self.username} ({self.role})>"
