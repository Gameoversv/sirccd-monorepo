"""
Ejemplos de uso de JWT y RBAC (B-03)

Este script muestra cómo usar el sistema de autenticación en diferentes escenarios.

NOTA: Este archivo contiene ejemplos de código. Para ejecutarlo desde Python, debe estar en el contexto correcto.
Los ejemplos están diseñados para ser copiados y usados en tus propios endpoints.
"""

import sys
import os

# Agregar backend al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

try:
    from api.deps import (
        CurrentUser,
        ActiveUser,
        VerifiedUser,
        AdminUser,
        SupervisorUser,
        require_role
    )
    from models.user import User, UserRole
except ImportError:
    print("  Imports no disponibles - este archivo contiene ejemplos de referencia")
    print("    Copiar y pegar los ejemplos en tus propios archivos de rutas")
    sys.exit(0)


# ==============================================================================
# EJEMPLO 1: Endpoint Público (sin autenticación)
# ==============================================================================

def example_public_endpoint():
    """Endpoint accesible sin autenticación"""
    
    from fastapi import APIRouter
    router = APIRouter()
    
    @router.get("/public/stats")
    async def get_public_stats():
        """Cualquiera puede acceder - sin token requerido"""
        return {
            "total_reports": 1234,
            "active_incidents": 56,
            "resolved_incidents": 890
        }
    
    return router


# ==============================================================================
# EJEMPLO 2: Endpoint con Autenticación Básica
# ==============================================================================

def example_authenticated_endpoint():
    """Endpoint que requiere autenticación"""
    
    from fastapi import APIRouter
    router = APIRouter()
    
    @router.get("/reports/my")
    async def get_my_reports(user: CurrentUser):
        """
        Obtener reportes del usuario autenticado.
        
        - Requiere: Token JWT válido
        - Acceso: Cualquier usuario autenticado
        """
        # user.id, user.username, user.role están disponibles
        return {
            "user_id": user.id,
            "username": user.username,
            "role": user.role.value,
            "reports": [
                {"id": 1, "type": "bache", "status": "pending"},
                {"id": 2, "type": "grieta", "status": "resolved"}
            ]
        }
    
    return router


# ==============================================================================
# EJEMPLO 3: Endpoint que Requiere Usuario Activo
# ==============================================================================

def example_active_user_endpoint():
    """Endpoint para usuarios activos"""
    
    from fastapi import APIRouter
    router = APIRouter()
    
    @router.post("/reports")
    async def create_report(user: ActiveUser):
        """
        Crear un nuevo reporte.
        
        - Requiere: Token JWT válido
        - Requiere: Usuario activo (is_active=True)
        - Acceso: Usuarios no bloqueados
        """
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo"
            )
        
        return {
            "message": "Reporte creado",
            "user_id": user.id,
            "timestamp": "2026-03-02T15:30:00"
        }
    
    return router


# ==============================================================================
# EJEMPLO 4: Endpoint que Requiere Usuario Verificado
# ==============================================================================

def example_verified_user_endpoint():
    """Endpoint para usuarios verificados"""
    
    from fastapi import APIRouter
    router = APIRouter()
    
    @router.post("/reports/priority")
    async def create_priority_report(user: VerifiedUser):
        """
        Crear un reporte prioritario.
        
        - Requiere: Token JWT válido
        - Requiere: Usuario verificado (is_verified=True)
        - Acceso: Solo usuarios que confirmaron su email
        """
        return {
            "message": "Reporte prioritario creado",
            "user_id": user.id,
            "verified": user.is_verified
        }
    
    return router


# ==============================================================================
# EJEMPLO 5: Endpoint Solo para Administradores
# ==============================================================================

def example_admin_only_endpoint():
    """Endpoint exclusivo para administradores"""
    
    from fastapi import APIRouter
    router = APIRouter()
    
    @router.delete("/users/{user_id}")
    async def delete_user(user_id: int, admin: AdminUser):
        """
        Eliminar un usuario (solo ADMIN).
        
        - Requiere: Token JWT válido
        - Requiere: Rol ADMIN
        - Acceso: Solo administradores del sistema
        """
        # admin.role == UserRole.ADMIN (garantizado por la dependencia)
        return {
            "message": f"Usuario {user_id} eliminado",
            "deleted_by": admin.username,
            "admin_id": admin.id
        }
    
    @router.post("/users/{user_id}/toggle-active")
    async def toggle_user_active(user_id: int, admin: AdminUser):
        """Activar/desactivar usuario (solo ADMIN)"""
        return {
            "message": f"Estado del usuario {user_id} cambiado",
            "admin": admin.username
        }
    
    return router


# ==============================================================================
# EJEMPLO 6: Endpoint para Supervisores y Admins
# ==============================================================================

def example_supervisor_endpoint():
    """Endpoint para supervisores y administradores"""
    
    from fastapi import APIRouter
    router = APIRouter()
    
    @router.get("/reports/pending")
    async def get_pending_reports(supervisor: SupervisorUser):
        """
        Ver reportes pendientes (SUPERVISOR o ADMIN).
        
        - Requiere: Token JWT válido
        - Requiere: Rol SUPERVISOR o ADMIN
        - Acceso: Supervisores y administradores
        """
        # supervisor.role in [UserRole.SUPERVISOR, UserRole.ADMIN]
        return {
            "pending_reports": [
                {"id": 1, "location": "Calle 1", "priority": "high"},
                {"id": 2, "location": "Calle 2", "priority": "medium"}
            ],
            "retrieved_by": supervisor.username,
            "role": supervisor.role.value
        }
    
    return router


# ==============================================================================
# EJEMPLO 7: Endpoint con Múltiples Roles Personalizados
# ==============================================================================

def example_custom_roles_endpoint():
    """Endpoint con roles personalizados específicos"""
    
    from fastapi import APIRouter, Depends
    from typing import Annotated
    
    router = APIRouter()
    
    @router.get("/analytics/advanced")
    async def get_advanced_analytics(
        user: Annotated[User, Depends(require_role(UserRole.ADMIN, UserRole.SUPERVISOR))]
    ):
        """
        Analíticas avanzadas (solo ADMIN o SUPERVISOR).
        
        - Requiere: Token JWT válido
        - Requiere: Rol ADMIN o SUPERVISOR exactamente
        - Acceso: Gestores del sistema
        """
        return {
            "analytics": {
                "total_incidents": 1000,
                "average_resolution_time": "24h",
                "team_efficiency": 0.88
            },
            "generated_by": user.username,
            "role": user.role.value
        }
    
    return router


# ==============================================================================
# EJEMPLO 9: Endpoint con Verificación de Rol Condicional
# ==============================================================================

def example_conditional_access():
    """Acceso condicional basado en rol y propiedades"""
    
    from fastapi import APIRouter, HTTPException, status
    router = APIRouter()
    
    @router.get("/reports/{report_id}")
    async def get_report_details(report_id: int, user: CurrentUser):
        """
        Ver detalles de un reporte.
        
        - Ciudadanos: Solo sus propios reportes
        - Brigadas/Supervisores: Reportes asignados a ellos
        - Admins: Todos los reportes
        """
        # Simulación de obtener reporte
        report_owner_id = 123  # Simular que viene de BD
        
        # Admin puede ver todo
        if user.role == UserRole.ADMIN:
            return {"report_id": report_id, "details": "...", "access": "admin"}
        
        # Supervisor/Brigada puede ver sus asignaciones
        if user.role == UserRole.SUPERVISOR:
            # Aquí verificarías si el reporte está asignado al usuario
            return {"report_id": report_id, "details": "...", "access": "assigned"}
        
        # Ciudadano solo puede ver sus propios reportes
        if user.role == UserRole.CIUDADANO:
            if report_owner_id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permiso para ver este reporte"
                )
            return {"report_id": report_id, "details": "...", "access": "owner"}
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado"
        )
    
    return router


# ==============================================================================
# EJEMPLO 10: Endpoint con Lógica de Negocio Compleja
# ==============================================================================

def example_complex_business_logic():
    """Endpoint con lógica de negocio compleja"""
    
    from fastapi import APIRouter, HTTPException, status
    from datetime import datetime, timedelta
    
    router = APIRouter()
    
    @router.post("/incidents/{incident_id}/complete")
    async def complete_incident(incident_id: int, user: CurrentUser):
        """
        Marcar incidente como completado.
        
        Reglas de negocio:
        - Supervisores: Pueden completar cualquier incidente de su zona
        - Admins: Pueden completar cualquier incidente
        - Ciudadanos: No pueden completar incidentes
        """
        # Verificar que ciudadanos no puedan completar
        if user.role == UserRole.CIUDADANO:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Los ciudadanos no pueden completar incidentes"
            )
        
        # Simulación de datos del incidente
        incident = {
            "id": incident_id,
            "zone": "norte",
            "status": "in_progress"
        }
        
        # Supervisores: Verificar zona
        if user.role == UserRole.SUPERVISOR:
            user_zone = "norte"  # Simular obtención de BD
            if incident["zone"] != user_zone:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Este incidente está fuera de tu zona"
                )
        
        # Admin puede completar cualquiera (sin restricciones)
        
        return {
            "message": f"Incidente {incident_id} marcado como completado",
            "completed_by": user.username,
            "role": user.role.value,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    return router


# ==============================================================================
# EJEMPLO DE USO EN MAIN.PY
# ==============================================================================

def integrate_examples_in_app():
    """Cómo integrar estos ejemplos en main.py"""
    
    example_code = """
from fastapi import FastAPI
from api.routes import auth, reports, incidents

app = FastAPI(title="SIRCCD API")

# Incluir routers de autenticación
app.include_router(auth.router, prefix="/api/v1", tags=["Autenticación"])

# Incluir routers con diferentes niveles de protección
app.include_router(reports.router, prefix="/api/v1", tags=["Reportes"])
app.include_router(incidents.router, prefix="/api/v1", tags=["Incidentes"])

# Ejemplos de este archivo se incluirían así:
from examples_b03_usage import (
    example_authenticated_endpoint,
    example_admin_only_endpoint,
    example_supervisor_endpoint
)

app.include_router(example_authenticated_endpoint(), prefix="/api/v1")
app.include_router(example_admin_only_endpoint(), prefix="/api/v1/admin")
app.include_router(example_supervisor_endpoint(), prefix="/api/v1/supervisor")
"""
    
    print(example_code)


# ==============================================================================
# MAIN - MOSTRAR TODOS LOS EJEMPLOS
# ==============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("EJEMPLOS DE USO - B-03: JWT y RBAC")
    print("=" * 80)
    
    examples = [
        ("Endpoint Público", example_public_endpoint),
        ("Endpoint Autenticado", example_authenticated_endpoint),
        ("Usuario Activo", example_active_user_endpoint),
        ("Usuario Verificado", example_verified_user_endpoint),
        ("Solo Administradores", example_admin_only_endpoint),
        ("Supervisores y Admins", example_supervisor_endpoint),
        ("Roles Personalizados", example_custom_roles_endpoint),
        ("Acceso Condicional", example_conditional_access),
        ("Lógica Compleja", example_complex_business_logic)
    ]
    
    for i, (name, func) in enumerate(examples, 1):
        print(f"\n{i}. {name}")
        print(f"   Función: {func.__name__}")
        print(f"   Descripción: {func.__doc__.strip()}")
    
    print("\n" + "=" * 80)
    print(" 10 ejemplos de uso disponibles")
    print("=" * 80)
    
    print("\n Ver código fuente de cada ejemplo para detalles de implementación")
    print(" Documentación completa en: backend/docs/B-03_AUTHENTICATION.md")
