"""
Rutas de autenticación: registro, login, logout, etc.
"""

from datetime import datetime, timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from db.session import get_db
from core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    validate_token_type
)
from core.config import settings
from models.user import User, UserRole
from schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    Token,
    TokenVerification,
    RefreshTokenRequest
)
from schemas.user import UserResponse
from api.deps import get_current_user, CurrentUser


router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: RegisterRequest,
    db: Session = Depends(get_db)
) -> RegisterResponse:
    """
    Registrar un nuevo usuario en el sistema.
    
    - **email**: Email único del usuario
    - **username**: Nombre de usuario único (3-100 caracteres)
    - **password**: Contraseña (mínimo 8 caracteres)
    - **full_name**: Nombre completo (opcional)
    - **phone**: Teléfono (opcional)
    
    El usuario se crea con rol CIUDADANO por defecto y debe verificar su email.
    """
    # Verificar si el email ya existe
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )
    
    # Verificar si el username ya existe
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está en uso"
        )
    
    # Crear el nuevo usuario
    try:
        new_user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            phone=user_data.phone,
            hashed_password=get_password_hash(user_data.password),
            role=UserRole.CIUDADANO,  # Por defecto todos son ciudadanos
            is_active=True,
            is_verified=False  # Requerirá verificación de email
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return RegisterResponse(
            message="Usuario registrado exitosamente. Por favor verifica tu email.",
            user_id=new_user.id,
            username=new_user.username,
            email=new_user.email
        )
        
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al crear usuario. Verifica que el email y username sean únicos."
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
) -> LoginResponse:
    """
    Iniciar sesión con credenciales de usuario.
    
    - **username**: Username o email del usuario
    - **password**: Contraseña
    
    Retorna un token JWT de acceso válido por 30 minutos.
    """
    # Buscar usuario por username o email
    user = db.query(User).filter(
        (User.username == login_data.username) | (User.email == login_data.username)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar contraseña
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar que el usuario esté activo
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo. Contacta al administrador."
        )
    
    # Actualizar last_login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Crear token de acceso
    access_token = create_access_token(
        subject=user.id,
        additional_claims={
            "role": user.role.value,
            "username": user.username
        }
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convertir a segundos
        user_id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        full_name=user.full_name
    )


@router.post("/login/oauth2", response_model=Token)
async def login_oauth2(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
) -> Token:
    """
    Endpoint de login compatible con OAuth2 (para herramientas automáticas).
    
    Utiliza el formato estándar OAuth2PasswordRequestForm.
    """
    # Buscar usuario
    user = db.query(User).filter(
        (User.username == form_data.username) | (User.email == form_data.username)
    ).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    
    # Actualizar last_login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Crear token
    access_token = create_access_token(
        subject=user.id,
        additional_claims={"role": user.role.value, "username": user.username}
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: CurrentUser
) -> UserResponse:
    """
    Obtener información del usuario autenticado actual.
    
    Requiere token JWT válido en el header Authorization.
    """
    return UserResponse.model_validate(current_user)


@router.post("/verify-token", response_model=TokenVerification)
async def verify_token(
    token: str,
    db: Session = Depends(get_db)
) -> TokenVerification:
    """
    Verificar si un token JWT es válido.
    
    - **token**: Token JWT a verificar
    
    Retorna información sobre la validez del token y datos del usuario.
    """
    payload = decode_access_token(token)
    
    if payload is None:
        return TokenVerification(valid=False)
    
    user_id = payload.get("sub")
    if not user_id:
        return TokenVerification(valid=False)
    
    # Verificar que el usuario existe y está activo
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        return TokenVerification(valid=False)
    
    return TokenVerification(
        valid=True,
        user_id=user.id,
        role=user.role,
        expires_at=payload.get("exp")
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
) -> Token:
    """
    Obtener un nuevo access token usando un refresh token.
    
    - **refresh_token**: Refresh token JWT válido
    
    Retorna un nuevo access token.
    """
    # Validar que sea un refresh token
    if not validate_token_type(refresh_data.refresh_token, "refresh"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o no es un refresh token"
        )
    
    # Decodificar el refresh token
    payload = decode_access_token(refresh_data.refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
    
    # Verificar usuario
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo"
        )
    
    # Crear nuevo access token
    access_token = create_access_token(
        subject=user.id,
        additional_claims={"role": user.role.value, "username": user.username}
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout")
async def logout(
    current_user: CurrentUser
) -> dict:
    """
    Cerrar sesión (logout).
    
    Nota: Con JWT stateless, el logout se maneja en el cliente eliminando el token.
    Este endpoint existe para conformidad con el flujo esperado y podría usarse
    para invalidar tokens en una blacklist futura.
    """
    # En una implementación futura, aquí se podría:
    # - Agregar el token a una blacklist en Redis
    # - Registrar el evento de logout en logs
    # - Limpiar sesiones relacionadas
    
    return {
        "message": "Sesión cerrada exitosamente",
        "username": current_user.username
    }
