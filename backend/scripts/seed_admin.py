"""
Crea (o repara) el usuario ADMIN inicial.

Hasta ahora el primer admin se hacia a mano: registrar un ciudadano por el API
y despues un UPDATE a mano sobre la tabla users, como describe
docs/GUIA_PRUEBAS_FLUJO_COMPLETO.md. Esto lo reemplaza.

La contrasena NO se hardcodea: se toma del entorno y el script falla si falta.
Es idempotente — si el usuario ya existe, no lo pisa; solo corrige rol/estado
si quedaron mal, y unicamente cambia la clave si se pide explicitamente.

Uso:
    ADMIN_USERNAME=admin ADMIN_EMAIL=admin@sirccd.com ADMIN_PASSWORD='...' \
        python -m scripts.seed_admin

En Railway:
    railway run --service backend python -m scripts.seed_admin

El login de la web es por username + password (auth.py acepta tambien el email
como identificador, pero el username es el camino previsto).
"""

import os
import sys

# Permite ejecutarlo como `python scripts/seed_admin.py` ademas de `-m`
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.security import get_password_hash  # noqa: E402
from db.session import SessionLocal  # noqa: E402
from models.user import User, UserRole  # noqa: E402

_MIN_PASSWORD_LENGTH = 12


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        sys.exit(
            f"ERROR: falta la variable de entorno {name}.\n"
            "Uso: ADMIN_USERNAME=admin ADMIN_EMAIL=admin@sirccd.com "
            "ADMIN_PASSWORD='...' python -m scripts.seed_admin"
        )
    return value


def seed_admin() -> int:
    username = _require_env("ADMIN_USERNAME")
    email = _require_env("ADMIN_EMAIL")
    password = _require_env("ADMIN_PASSWORD")
    force_password = os.environ.get("ADMIN_FORCE_PASSWORD", "").lower() in {"1", "true", "yes"}

    if len(password) < _MIN_PASSWORD_LENGTH:
        sys.exit(
            f"ERROR: ADMIN_PASSWORD debe tener al menos {_MIN_PASSWORD_LENGTH} caracteres."
        )

    db = SessionLocal()
    try:
        existing = (
            db.query(User)
            .filter((User.username == username) | (User.email == email))
            .first()
        )

        if existing:
            changes = []
            if existing.role != UserRole.ADMIN:
                existing.role = UserRole.ADMIN
                changes.append("rol -> admin")
            if not existing.is_active:
                existing.is_active = True
                changes.append("activado")
            if not existing.is_verified:
                existing.is_verified = True
                changes.append("verificado")
            if force_password:
                existing.hashed_password = get_password_hash(password)
                changes.append("password actualizada")

            if changes:
                db.commit()
                print(f"Usuario '{existing.username}' ya existia: {', '.join(changes)}.")
            else:
                print(
                    f"Usuario '{existing.username}' ya es admin y esta activo. Sin cambios.\n"
                    "Para reescribir la clave: ADMIN_FORCE_PASSWORD=true"
                )
            return existing.id

        admin = User(
            username=username,
            email=email,
            full_name=os.environ.get("ADMIN_FULL_NAME", "Administrador SIRCCD"),
            hashed_password=get_password_hash(password),
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print(f"Admin '{username}' creado (id={admin.id}). Login web: {username} + password.")
        return admin.id

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
