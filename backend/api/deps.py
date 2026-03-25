"""
Dependencias de FastAPI para autenticación y autorización
"""

from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from db.session import get_db
from core.security import decode_access_token
from models.user import User, UserRole
from schemas.auth import TokenPayload


# OAuth2 scheme para extraer el token del header Authorization
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    scheme_name="JWT"
)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db)
) -> User:
    """
    Dependencia para obtener el usuario actual desde el token JWT.
    
    Args:
        token: Token JWT del header Authorization
        db: Sesión de base de datos
        
    Returns:
        Usuario autenticado
        
    Raises:
        HTTPException 401: Si el token es inválido o el usuario no existe
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Decodificar el token
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    # Extraer el user_id del subject
    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    # Buscar el usuario en la base de datos
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    
    # Verificar que el usuario esté activo
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Dependencia para obtener el usuario actual y verificar que esté activo.
    
    Args:
        current_user: Usuario obtenido del token
        
    Returns:
        Usuario activo
        
    Raises:
        HTTPException 403: Si el usuario está inactivo
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    return current_user


async def get_current_verified_user(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    """
    Dependencia para obtener el usuario actual y verificar que esté verificado.
    
    Args:
        current_user: Usuario activo
        
    Returns:
        Usuario verificado
        
    Raises:
        HTTPException 403: Si el usuario no está verificado
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario no verificado. Por favor verifica tu email."
        )
    return current_user


# Dependencias para verificar roles específicos

def require_role(*allowed_roles: UserRole):
    """
    Factory para crear dependencias que requieren roles específicos.
    
    Args:
        *allowed_roles: Roles permitidos para acceder al endpoint
        
    Returns:
        Dependencia de FastAPI que verifica el rol
        
    Example:
        @router.get("/admin-only", dependencies=[Depends(require_role(UserRole.ADMIN))])
        async def admin_endpoint():
            return {"message": "Solo admins"}
    """
    async def role_checker(
        current_user: Annotated[User, Depends(get_current_active_user)]
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tienes permiso. Roles requeridos: {[r.value for r in allowed_roles]}"
            )
        return current_user
    
    return role_checker


# Dependencias de rol predefinidas para uso común

async def require_admin(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    """
    Dependencia que requiere rol ADMIN.
    
    Args:
        current_user: Usuario autenticado
        
    Returns:
        Usuario con rol ADMIN
        
    Raises:
        HTTPException 403: Si el usuario no es admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol de administrador"
        )
    return current_user


async def require_supervisor(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    """
    Dependencia que requiere rol SUPERVISOR o superior (ADMIN).
    
    Args:
        current_user: Usuario autenticado
        
    Returns:
        Usuario con rol SUPERVISOR o ADMIN
        
    Raises:
        HTTPException 403: Si el usuario no es supervisor o admin
    """
    if current_user.role not in [UserRole.SUPERVISOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol de supervisor o administrador"
        )
    return current_user


# Tipos anotados para uso conveniente en endpoints

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
ActiveUser = Annotated[User, Depends(get_current_active_user)]
VerifiedUser = Annotated[User, Depends(get_current_verified_user)]
AdminUser = Annotated[User, Depends(require_admin)]
SupervisorUser = Annotated[User, Depends(require_supervisor)]
