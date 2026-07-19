# Configuración

[← Volver al índice](README.md)

Descripción de los archivos de configuración presentes en el repositorio y su propósito. Para el detalle variable por variable, ver [ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md).

## Raíz del repositorio

| Archivo | Propósito |
|---|---|
| `.env` | Variables de entorno reales para desarrollo local. **No versionado** (ver `.gitignore`). |
| `.env.example` | Plantilla de variables de entorno de producción (dominio, credenciales de Postgres/Redis/MinIO, secretos JWT/cifrado, API de Roboflow). Valores ficticios, con instrucciones de generación (`openssl rand ...`). |
| `docker-compose.yml` | Orquestación de desarrollo local: Postgres+PostGIS, Redis, MinIO, backend, frontend. Incluye valores de entorno por defecto embebidos (no requiere `.env` completo para levantar el stack local). |
| `docker-compose.prod.yml` | Orquestación de producción. Usa variables externas (`${VAR}`) en vez de valores hardcodeados — depende de que el entorno de despliegue las provea. |
| `.gitattributes` | Normalización de line endings y atributos de git. |
| `.gitignore` | Excluye artefactos de build, entornos virtuales, `.env`, cachés (`__pycache__`, `.pytest_cache`, `node_modules`, `.next`, etc.). |

## Backend (`backend/`)

| Archivo | Propósito |
|---|---|
| `core/config.py` | Clase `Settings` (Pydantic `BaseSettings`) — punto único de lectura de variables de entorno del backend. Define defaults para desarrollo local; en producción todas deben sobreescribirse vía entorno. |
| `alembic.ini` + `alembic/env.py` | Configuración de migraciones de base de datos. |
| `pytest.ini` | Marcadores de pruebas (`unit`, `integration`, `contract`, `slow`, `auth`, `reports`, `incidents`, `ml`) y `testpaths`. |
| `.coveragerc` | Exclusiones de cobertura (migraciones, `worker*.py`, scripts de verificación). |
| `Dockerfile` | Imagen de producción: Python 3.11-slim, instala `torch`/`torchvision` desde el índice CPU-only de PyTorch (evita ~2.5 GB de dependencias CUDA innecesarias), corre `alembic upgrade head` antes de iniciar `uvicorn`. |

## Frontend (`frontend/`)

| Archivo | Propósito |
|---|---|
| `next.config.js` | Configuración de Next.js: `reactStrictMode`, defaults embebidos para variables `NEXT_PUBLIC_*`, dominios de imágenes remotas permitidos (host de MinIO), override de webpack para Leaflet (`canvas` externo). |
| `.env.example` | Variables públicas del frontend: URL del backend, centro/zoom por defecto del mapa, nombre/versión de la app. |
| `tailwind.config.js` | Tema de diseño (colores, sombras, animaciones) y rutas de contenido para el purge de CSS. |
| `postcss.config.js` | Pipeline de PostCSS (Tailwind + Autoprefixer). |
| `tsconfig.json` | Configuración de TypeScript. |
| `playwright.config.ts` | Configuración de pruebas E2E (directorio `tests/`, `baseURL http://localhost:3001`, navegador Chromium). |
| `Dockerfile` | Imagen `node:20-alpine`; recibe `NEXT_PUBLIC_API_URL` como build arg — las variables `NEXT_PUBLIC_*` quedan **inlineadas en el build**, no son configurables en runtime tras compilar la imagen. |

## Infraestructura (`infra/`)

| Archivo | Propósito |
|---|---|
| `infra/compose/docker-compose.minio.yml` | MinIO como servicio independiente para desarrollo (alternativa a levantarlo desde el `docker-compose.yml` raíz). |
| `infra/nginx/nginx.conf` | Configuración de reverse proxy. |
| `infra/nginx/generate-dev-certs.sh` | Generación de certificados TLS autofirmados para desarrollo. |

## Mobile (`mobile/`)

| Archivo | Propósito |
|---|---|
| `pubspec.yaml` | Dependencias Flutter/Dart y metadatos del paquete. |
| `analysis_options.yaml` | Reglas de lint de Dart. |
| `lib/core/network/backend_url.dart` | Punto de configuración de la URL del backend consumida por la app. |

## CI

| Archivo | Propósito |
|---|---|
| `.github/workflows/backend-tests.yml` | Único pipeline de CI del repositorio. Ejecuta pruebas unitarias, de integración y de contrato del backend contra servicios de Postgres/Redis en contenedores, más un chequeo de calidad de código. No cubre frontend, mobile ni `ml/`. |
