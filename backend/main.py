"""
FastAPI Application - SIRCCD Backend
Sistema Inteligente de Reporte Ciudadano de Calles Dañadas
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes import health, auth, reports, deduplication, incidents, export, users, pois, settings as settings_routes, zones
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
app.include_router(pois.router, prefix=f"{settings.API_V1_STR}/pois", tags=["POIs"])
app.include_router(export.router, prefix=f"{settings.API_V1_STR}/export", tags=["Exportaciones"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["Usuarios"])
app.include_router(settings_routes.router, prefix=settings.API_V1_STR, tags=["Ajustes"])
app.include_router(zones.router, prefix=f"{settings.API_V1_STR}/zones", tags=["Zonas"])

# Montar archivos estáticos (imágenes subidas)
app.mount("/storage", StaticFiles(directory="storage"), name="storage")


@app.on_event("startup")
async def startup_event():
    """Evento de inicio de la aplicación"""
    print(f"[START] {settings.PROJECT_NAME} v{settings.VERSION} iniciando...")
    print(f"[DOCS] Documentacion: http://{settings.HOST}:{settings.PORT}{settings.API_V1_STR}/docs")
    # Obtener métricas del modelo Roboflow al iniciar
    try:
        from services.ml_service import ml_service
        ml_service._fetch_model_metrics()
    except Exception as e:
        print(f"[WARN] No se pudieron cargar métricas del modelo: {e}")

    # Pre-cargar el servicio de deduplicación completo (ResNet50 + CLIP) en background
    # para evitar que la primera request bloquee descargando modelos
    try:
        import threading
        def _preload_dedup():
            try:
                import numpy as np
                from PIL import Image as _PIL
                from db.session import SessionLocal
                from services.deduplication_service import get_deduplication_service

                db = SessionLocal()
                try:
                    svc = get_deduplication_service(db)
                    # Warm up todos los embedders con una imagen dummy
                    dummy = _PIL.fromarray(np.zeros((64, 64, 3), dtype=np.uint8))
                    for name, emb in svc.embedders.items():
                        emb.embed(dummy)
                        print(f"[START] Modelo {name} pre-cargado en memoria")
                finally:
                    db.close()
            except Exception as ex:
                print(f"[WARN] Pre-carga dedup falló: {ex}")
        threading.Thread(target=_preload_dedup, daemon=True).start()
    except Exception as e:
        print(f"[WARN] No se pudo iniciar pre-carga del servicio de dedup: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Evento de cierre de la aplicación"""
    print(f"[STOP] {settings.PROJECT_NAME} cerrando...")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
