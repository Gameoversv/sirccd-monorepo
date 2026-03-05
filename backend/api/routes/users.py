"""
API de Gestión de Usuarios (W-08)

Endpoints CRUD para administración de usuarios:
- Listar usuarios paginados con filtros (SUPERVISOR+)
- Obtener usuario por ID (SUPERVISOR+)
- Crear usuario con rol (ADMIN)
- Actualizar datos / rol / estado (ADMIN)
- Desactivar usuario - soft-delete (ADMIN)
- Perfil propio (cualquier rol autenticado)
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import asc
from sqlalchemy.exc import IntegrityError

from db.session import get_db
from api.deps import get_current_active_user, require_admin, require_supervisor
from models.user import User, UserRole
from schemas.user import UserResponse, UserCreate, UserUpdate, UserListItem
from core.security import get_password_hash


router = APIRouter()


# ── Me ────────────────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_active_user)):
    """Retorna el perfil del usuario autenticado (cualquier rol)."""
    return current_user


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("/", response_model=dict)
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supervisor),
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(20, ge=1, le=100, description="Usuarios por página"),
    role: Optional[str] = Query(None, description="Filtrar por rol"),
    is_active: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    search: Optional[str] = Query(None, description="Buscar por nombre, email o username"),
):
    """
    Lista usuarios con paginación y filtros. Requiere SUPERVISOR o ADMIN.
    """
    q = db.query(User)

    if role:
        try:
            q = q.filter(User.role == UserRole(role))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rol inválido: {role}. Opciones: {[r.value for r in UserRole]}"
            )

    if is_active is not None:
        q = q.filter(User.is_active == is_active)

    if search:
        like = f"%{search}%"
        q = q.filter(
            (User.username.ilike(like)) |
            (User.email.ilike(like)) |
            (User.full_name.ilike(like))
        )

    total = q.count()
    users = (
        q.order_by(asc(User.id))
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, (total + per_page - 1) // per_page),
        "users": [UserListItem.model_validate(u) for u in users],
    }


# ── Read one ──────────────────────────────────────────────────────────────────

@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supervisor),
):
    """Obtiene un usuario por ID. Requiere SUPERVISOR o ADMIN."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario {user_id} no encontrado"
        )
    return user


# ── Create ────────────────────────────────────────────────────────────────────

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Crea un nuevo usuario con el rol indicado. Solo ADMIN."""
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está en uso"
        )

    user = User(
        email=data.email,
        username=data.username,
        full_name=data.full_name,
        phone=data.phone,
        role=data.role,
        hashed_password=get_password_hash(data.password),
        is_active=True,
        is_verified=True,  # Usuarios creados por admin no necesitan verificar email
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ── Update ────────────────────────────────────────────────────────────────────

@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Actualiza datos, rol o estado de un usuario. Solo ADMIN."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario {user_id} no encontrado"
        )

    # Proteger al admin de bajarse el rol o desactivarse a sí mismo
    if user.id == current_user.id:
        if data.role is not None and data.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes cambiar tu propio rol"
            )
        if data.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes desactivarte a ti mismo"
            )

    if data.email is not None:
        existing = db.query(User).filter(
            User.email == data.email, User.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está en uso por otro usuario"
            )

    if data.username is not None:
        existing = db.query(User).filter(
            User.username == data.username, User.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El username ya está en uso por otro usuario"
            )

    update_fields = data.model_dump(exclude_unset=True)
    if "password" in update_fields:
        update_fields["hashed_password"] = get_password_hash(update_fields.pop("password"))

    for field, value in update_fields.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


# ── Deactivate (soft-delete) ──────────────────────────────────────────────────

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Desactiva un usuario (soft-delete). Solo ADMIN."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario {user_id} no encontrado"
        )
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes desactivarte a ti mismo"
        )

    user.is_active = False
    db.commit()


# ── Hard delete ───────────────────────────────────────────────────────────────

@router.delete("/{user_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_permanent(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Elimina permanentemente un usuario. Solo ADMIN."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario {user_id} no encontrado"
        )
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminarte a ti mismo"
        )
    try:
        db.delete(user)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar: el usuario tiene registros asociados. Desactívelo en su lugar."
        )
