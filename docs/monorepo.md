# Monorepo SIRCCD

## 1. Proposito general

SIRCCD (Sistema Inteligente Urbano para Reporte y Priorizacion de Danos Viales) integra en un solo repositorio todo el sistema de reporte y gestion de danos viales urbanos:

- **Captura ciudadana**: reportes con foto, ubicacion y descripcion desde campo.
- **Procesamiento ML**: clasificacion automatica de tipo y severidad de dano.
- **Deduplicacion inteligente**: deteccion multimodal de reportes duplicados.
- **Priorizacion automatica**: scoring basado en severidad, frecuencia, ubicacion y contexto urbano.
- **Operacion municipal**: dashboard web con mapas, tablas, KPIs y flujos de trabajo.
- **Infraestructura**: orquestacion Docker, CI/CD y despliegue.
- **App movil**: aplicacion ciudadana para reportes en campo (planificada).

## 2. Arquitectura por modulos

### 2.1 Modulos de producto

| Modulo | Directorio | Proposito | Estado |
|--------|-----------|-----------|--------|
| Backend | `backend/` | API REST, logica de negocio, procesamiento asincrono, persistencia | Maduro |
| Frontend | `frontend/` | Dashboard web de operacion municipal | Maduro |
| ML | `ml/` | Entrenamiento, datasets, inferencia y artefactos de modelos | Activo |

### 2.2 Modulos de plataforma

| Modulo | Directorio | Proposito | Estado |
|--------|-----------|-----------|--------|
| Infra | `infra/` | CI/CD, compose por entorno, Dockerfiles reutilizables | Scaffold |
| Mobile | `mobile/` | App ciudadana Flutter | Scaffold |

### 2.3 Documentacion

| Modulo | Directorio | Proposito |
|--------|-----------|-----------|
| Docs | `docs/` | Fuente unica de documentacion centralizada por modulo |

## 3. Diagrama de arquitectura

```
                    +-------------------+
                    |   App Movil       |
                    |   (Flutter)       |
                    +--------+----------+
                             |
                             | REST API
                             v
+-------------------+   +-------------------+   +-------------------+
|   Frontend        |   |   Backend         |   |   ML Pipeline     |
|   (Next.js 14)    |<->|   (FastAPI)       |<--|   (PyTorch/YOLO)  |
|   Dashboard Web   |   |   API + Workers   |   |   Training        |
+-------------------+   +--------+----------+   +-------------------+
                             |       |
                    +--------+--+  +-+----------+
                    |           |  |             |
               +----v---+ +----v--+-+ +--------v--+
               |PostgreSQL| | Redis  | |   MinIO   |
               |+PostGIS | | + RQ   | |  Storage  |
               +---------+ +--------+ +-----------+
```

### 3.1 Flujo de datos

```
Ciudadano → [Reporte: foto + GPS + texto]
    → Backend (validacion, almacenamiento)
        → Worker RQ (procesamiento asincrono)
            → ML Service (clasificacion YOLO)
            → Anonymizer (anonimizacion de imagen)
            → Dedup Service (embeddings + FAISS + geo + texto)
            → Priority Service (scoring)
        → Resultado: reporte clasificado, deduplicado, priorizado
    → Frontend (dashboard operativo)
        → Operador municipal (gestion y resolucion)
```

## 4. Flujo funcional transversal

### 4.1 Ciclo completo de un reporte

1. **Captura**: ciudadano envia reporte con imagen, ubicacion GPS y descripcion opcional.
2. **Recepcion**: backend valida payload, almacena imagen en MinIO, crea registro en PostgreSQL.
3. **Encolamiento**: backend encola tarea de procesamiento en Redis RQ.
4. **Procesamiento ML**: worker ejecuta inferencia YOLO para clasificar tipo de dano y estimar severidad.
5. **Anonimizacion**: si la imagen contiene rostros o placas, se aplica difuminado automatico.
6. **Embeddings**: se extraen vectores visuales (ResNet50/CLIP) de la imagen.
7. **Deduplicacion**: se buscan candidatos similares en indice FAISS, se calcula score fusionado (visual + geo + texto).
8. **Asociacion**: si es duplicado, se asocia a incidente existente; si es nuevo, se crea incidente.
9. **Priorizacion**: se recalcula prioridad del incidente segun severidad, frecuencia, ubicacion y POIs cercanos.
10. **Visualizacion**: frontend muestra resultados en mapa, tablas y KPIs para operacion municipal.

### 4.2 Estados del sistema

#### Reporte
```
pending → processing → classified → [duplicate | resolved]
```

#### Incidente
```
open → in_progress → resolved → closed
```

## 5. Mapa de raiz del repositorio

```
sirccd-monorepo/
├── backend/                 # API REST + logica de negocio + workers
├── frontend/                # Dashboard web Next.js
├── ml/                      # Pipeline ML: entrenamiento, inferencia, embeddings
├── infra/                   # Infraestructura: CI/CD, compose, docker (scaffold)
├── mobile/                  # App ciudadana Flutter (scaffold)
├── docs/                    # Documentacion centralizada
├── docker-compose.yml       # Orquestacion principal de servicios
├── docker-compose.minio.yml # Compose standalone de MinIO
├── dev.ps1                  # Script PowerShell de arranque local
├── dev-stop.ps1             # Script PowerShell de detencion local
├── .github/                 # GitHub Actions y workflows
├── .gitignore               # Exclusiones de git
└── runs/                    # Salidas de entrenamiento ML
```

## 6. Stack tecnologico global

| Capa | Tecnologia | Version |
|------|------------|---------|
| Frontend | Next.js + React + TypeScript | 14.1 / 18.2 / 5.3 |
| Estilos | Tailwind CSS | 3.4 |
| Estado frontend | Zustand | 4.5 |
| Mapas | React Leaflet | 4.2 |
| Graficos | Recharts | 3.7 |
| i18n | i18next | 25.8 |
| Backend | FastAPI | 0.115 |
| ORM | SQLAlchemy + Alembic | 2.0 |
| Base de datos | PostgreSQL + PostGIS | 16+ |
| Cola de tareas | Redis + RQ | 7 / 5 |
| Almacenamiento | MinIO | 7.2 |
| ML | PyTorch + Ultralytics YOLO | 2.1+ / 8.0+ |
| Busqueda vectorial | FAISS | 1.7.4 |
| Contenedores | Docker + Docker Compose | - |
| Mobile (planificado) | Flutter | - |

## 7. Convencion de ubicacion de archivos

| Tipo de archivo | Ubicacion |
|----------------|-----------|
| Codigo de producto | Dentro del modulo correspondiente |
| Pruebas automaticas | `modulo/tests/` |
| Pruebas manuales/smoke | `modulo/tests/manual/` |
| Fixtures de pruebas | `modulo/tests/manual/fixtures/` o `modulo/tests/fixtures/` |
| Scripts operativos | `modulo/scripts/` |
| Documentacion centralizada | `docs/` |
| Documentacion operativa ML | `ml/docs/` |
| Configuracion Docker | Raiz (transitorio) → `infra/compose/` (destino) |

## 8. Comandos operativos rapidos

### Levantar entorno local completo

```powershell
powershell -ExecutionPolicy Bypass -File dev.ps1
```

### Detener entorno local

```powershell
powershell -ExecutionPolicy Bypass -File dev-stop.ps1
```

### Levantar con Docker Compose

```bash
docker compose up -d
```

### Solo backend + dependencias

```powershell
cd backend
docker compose -f docker-compose.db.yml up -d
..\.venv\Scripts\Activate.ps1
uvicorn main:app --reload --port 8000
```

### Solo frontend

```powershell
cd frontend
npm install
npm run dev
```

### Ver cambios locales

```bash
git status --short
```

## 9. Puntos de integracion entre modulos

| Origen | Destino | Mecanismo | Datos |
|--------|---------|-----------|-------|
| Frontend | Backend | REST API + JWT | Reportes, incidentes, auth, metricas |
| Backend | PostgreSQL | SQLAlchemy ORM | Persistencia de entidades |
| Backend | Redis | RQ (cola) | Tareas de procesamiento ML |
| Backend | MinIO | SDK MinIO | Imagenes de reportes |
| ML | Backend | Artefactos (pesos, configs) | Modelos entrenados |
| Mobile | Backend | REST API + JWT | Reportes ciudadanos (futuro) |
| Infra | Todos | Docker Compose | Orquestacion de servicios |

## 10. Decisiones de organizacion aplicadas

1. Se elimino documentacion historica fragmentada en `docs/`.
2. Se centralizo documentacion por modulo en `docs/*.md`.
3. Se vacio `backend/docs/` para evitar duplicidad con documentacion central.
4. En backend se separo codigo fuente de scripts y tests manuales:
   - `backend/tests/manual/` para pruebas manuales.
   - `backend/tests/manual/fixtures/` para recursos de prueba.
   - `backend/scripts/verification/` para scripts de verificacion.
   - `backend/scripts/maintenance/` para scripts de mantenimiento.
5. Se removieron artefactos generados (logs, caches, coverage) de raices de modulo.
6. Se agrego `DOCUMENTACION_COMPLETA.md` como referencia unificada extensiva.
