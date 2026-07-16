do# SIRCCD Monorepo

Sistema Inteligente Urbano para Reporte y Priorizacion de Danos Viales.

## Estado

Desarrollo activo.

## Modulos del repositorio

- backend: API y reglas de negocio (FastAPI + PostGIS + Redis + MinIO)
- frontend: dashboard web operativo (Next.js + TypeScript)
- ml: entrenamiento, datasets y soporte de inferencia
- infra: base de infraestructura y despliegue
- mobile: espacio reservado para app ciudadana

## Estructura base

```text
sirccd-monorepo/
|- backend/
|- frontend/
|- ml/
|- infra/
|- mobile/
|- docs/
|- dev.ps1
|- dev-stop.ps1
|- docker-compose.yml
|- docker-compose.minio.yml
```

## Inicio rapido

### Backend

```powershell
cd backend
..\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

### Script raiz

```powershell
powershell -ExecutionPolicy Bypass -File dev.ps1
```

## Documentacion

La carpeta docs fue reiniciada y ahora esta separada por modulo.

- [Indice de documentacion](docs/README.md)
- [Arquitectura de monorepo](docs/monorepo.md)
- [Modulo Backend](docs/backend.md)
- [Modulo Frontend](docs/frontend.md)
- [Modulo ML](docs/ml.md)
- [Modulo Infra](docs/infra.md)
- [Modulo Mobile](docs/mobile.md)

## Notas tecnicas

- Deduplicacion backend: embeddings multimodelo (ResNet/CLIP) + FAISS + score fusionado.
- Para pruebas dedup en Windows puede requerirse variable temporal KMP_DUPLICATE_LIB_OK=TRUE.

## Organizacion aplicada

- La documentacion historica dispersa se consolido en docs/ por modulo.
- backend/docs fue vaciado para evitar duplicacion documental.
- Scripts sueltos de verificacion y mantenimiento en backend se movieron a:
	- backend/scripts/verification/
	- backend/scripts/maintenance/
- Pruebas manuales sueltas se movieron a backend/tests/manual/ y sus imagenes a backend/tests/manual/fixtures/.
