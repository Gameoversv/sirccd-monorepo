"""
FastAPI Application - SIRCCD Backend
Sistema Inteligente de Reporte Ciudadano de Calles Dañadas
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import health, auth, reports, deduplication, incidents, export
from core.config import settings
from core.metrics import PrometheusMiddleware

# Crear instancia de FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar middleware de métricas Prometheus (B-10)
app.add_middleware(PrometheusMiddleware)

# Registrar rutas
app.include_router(health.router, prefix=settings.API_V1_STR, tags=["Health"])
app.include_router(auth.router, prefix=settings.API_V1_STR, tags=["Autenticación"])
app.include_router(reports.router, prefix=settings.API_V1_STR, tags=["Reportes"])
app.include_router(deduplication.router, prefix=settings.API_V1_STR, tags=["Deduplicación"])
app.include_router(incidents.router, prefix=f"{settings.API_V1_STR}/incidents", tags=["Incidentes"])
app.include_router(export.router, prefix=f"{settings.API_V1_STR}/export", tags=["Exportaciones"])


@app.on_event("startup")
async def startup_event():
    """Evento de inicio de la aplicación"""
    print(f"🚀 {settings.PROJECT_NAME} v{settings.VERSION} iniciando...")
    print(f"📚 Documentación: http://{settings.HOST}:{settings.PORT}{settings.API_V1_STR}/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Evento de cierre de la aplicación"""
    print(f"🛑 {settings.PROJECT_NAME} cerrando...")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
