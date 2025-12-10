# SIRCCD Monorepo  
### Sistema Inteligente Urbano para Reporte y Priorización de Daños Viales mediante Geolocalización y Visión por Computadora

El **SIRCCD** es un sistema urbano diseñado para digitalizar y optimizar la gestión de daños viales en zonas urbanas mediante:

- Reportes ciudadanos y de brigadas con foto + GPS.  
- Clasificación automática de daños (bache, grieta, hundimiento) usando IA.  
- Estimación de severidad mediante segmentación.  
- Eliminación de reportes duplicados mediante análisis visual y geográfico.  
- Priorización multicriterio basada en severidad, riesgo, antigüedad y densidad.  
- Panel municipal GIS con KPIs, rutas sugeridas y estados operativos.  
- Protección de privacidad mediante difuminado automático de rostros y placas.

Este repositorio funciona como **monorepo**, integrando frontend, backend, app móvil, modelos ML, infraestructura y documentación técnica.

---

## 🧱 Arquitectura del Monorepo

```
sirccd-monorepo/
│
├── backend/     → API (FastAPI + PostgreSQL/PostGIS + Celery/RQ)
├── frontend/    → Panel municipal web (React/Next.js)
├── mobile/      → App móvil ciudadana (Flutter)
├── ml/          → Modelos ML, entrenamiento, inferencia, deduplicación
├── infra/       → Docker, docker-compose, CI/CD
├── docs/        → Diagramas, actas, documentación técnica
└── data/        → Datos auxiliares, POIs, imágenes de prueba
```

---

## 🎯 Objetivos del Sistema

- Modernizar y centralizar la gestión vial urbana.  
- Reducir duplicados en reportes mediante análisis visual + geográfico.  
- Ofrecer un sistema inteligente de priorización de incidentes.  
- Mejorar la eficiencia municipal y los tiempos de respuesta.  
- Garantizar transparencia mediante KPIs (F1, TTR, SLA, deduplicación).  
- Proteger datos personales cumpliendo principios de privacidad.

---

## 🔧 Requisitos Generales

- Git  
- Docker / Docker Compose  
- Python 3.10+  
- Node.js 18+  
- Flutter 3.x  
- PostgreSQL + PostGIS  
- MinIO/S3 (opcional pero recomendado)

---

## ⚙️ Instalación General

```bash
git clone https://github.com/usuario/sirccd-monorepo.git
cd sirccd-monorepo
```

### 🖥️ Backend (FastAPI)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### 🌐 Frontend Web (React / Next.js)

```bash
cd frontend
npm install
npm run dev
```

Acceder en: http://localhost:3000/

### 📱 App Móvil (Flutter)

```bash
cd mobile
flutter pub get
flutter run
```

Incluye captura de reportes, fotos con metadatos, historial y sincronización offline-first.

### 🤖 Modelos de ML

Incluye:

- YOLOv8-seg para detección y segmentación.
- Estimación de severidad (área/longitud segmentada).
- Embeddings visuales (CLIP/ResNet).
- Deduplicación (FAISS/Annoy + DBSCAN/Haversine).
- Exportación ONNX/TFLite.

Ejemplo:

```bash
cd ml
pip install -r requirements.txt
python train_baseline.py
```

---

## 🌿 Flujo de Ramas (Git Branching)

**Ramas principales:**

- `main` → versión estable
- `dev` → integración continua

**Ramas de desarrollo:**

- `feat/*` → nuevas funcionalidades
- `fix/*` → correcciones
- `doc/*` → documentación
- `test/*` → pruebas
- `chore/*` → mantenimiento

**Ejemplos:**

- `feat/ml-deduplicacion`
- `feat/frontend-filtros-mapa`
- `fix/backend-endpoint-kpi`
- `doc/diagrama-arquitectura`

---

## 📝 Convención de Commits

**Formato:**

```
tipo: descripción breve
```

**Tipos permitidos:**

- `feat:` nueva funcionalidad
- `fix:` corrección de bugs
- `docs:` documentación
- `style:` formato/estilo
- `refactor:` reorganización interna
- `test:` pruebas
- `chore:` mantenimiento

**Ejemplos:**

- `feat: agregar mapa de incidentes por barrio`
- `fix: corregir cálculo de severidad`
- `docs: agregar documento de arquitectura`
- `refactor: aislar módulo de inferencia ml`

---

## 📁 Estructura General del Proyecto

```
sirccd-monorepo
│
├── backend
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── services/
│   └── tests/
│
├── frontend
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── store/
│   │   └── pages/
│   └── public/
│
├── mobile
│   ├── lib/
│   └── assets/
│
├── ml
│   ├── train/
│   ├── inference/
│   ├── embeddings/
│   ├── deduplication/
│   └── utils/
│
├── infra
│   ├── docker/
│   ├── compose/
│   └── ci-cd/
│
└── docs
    ├── arquitectura/
    ├── procesos/
    ├── acta/
    └── analisis/
```

---

## 📆 Roadmap del Proyecto (Fases)

| Fase | Entregable |
|------|-----------|
| Fase 0 | Gestión, repos, convenciones |
| Fase 1 | Estudio preliminar |
| Fase 2 | Requerimientos y diseño |
| Fase 3 | Datasets y procesamiento |
| Fase 4 | Entrenamiento ML |
| Fase 5 | Backend & APIs |
| Fase 6 | Frontend Web |
| Fase 7 | App móvil |
| Fase 8 | Panel municipal + GIS |
| Fase 9 | Seguridad y privacidad |
| Fase 10 | QA y pruebas |
| Fase 11 | Despliegue & operación |

---

## ⚖️ Licencia

MIT License

---

## 🚀 Proyecto listo para desarrollo

Este README establece la estructura completa del monorepo para desarrollo colaborativo, revisión académica, despliegue y mantenimiento profesional.
