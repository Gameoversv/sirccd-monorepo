# Variables de entorno

[← Volver al índice](README.md)

> Ninguna de las tablas siguientes contiene valores reales de credenciales. Los "valores de ejemplo" son siempre ficticios o son los defaults de desarrollo local ya presentes en `docker-compose.yml` (no secretos de producción).

## Backend

Fuente: `backend/core/config.py` (clase `Settings`).

| Variable | Descripción | Obligatoria | Valor de ejemplo | Entorno | Consecuencia si falta |
|---|---|---|---|---|---|
| `HOST` | Host de escucha de uvicorn | No (default `0.0.0.0`) | `0.0.0.0` | Todos | Usa default |
| `PORT` | Puerto de escucha | No (default `8000`) | `8000` | Todos | Usa default |
| `DEBUG` | Habilita `reload` y logs detallados | No (default `False`) | `False` | Dev/Prod | Producción debe mantenerlo en `False` |
| `ALLOWED_ORIGINS` | Lista JSON de orígenes permitidos por CORS | Sí en producción | `["https://sirccd.example.com"]` | Todos | Sin el origen correcto, el frontend no puede llamar al API por CORS |
| `POSTGRES_HOST` | Host de PostgreSQL | Sí | `postgres` (Docker) / `localhost` | Todos | El backend no puede conectar a la base de datos |
| `POSTGRES_PORT` | Puerto de PostgreSQL | No (default `5432`) | `5432` | Todos | Usa default |
| `POSTGRES_USER` | Usuario de PostgreSQL | Sí | `sirccd_user` | Todos | Falla la conexión a BD |
| `POSTGRES_PASSWORD` | Contraseña de PostgreSQL | Sí | `CAMBIAR_PASSWORD_FUERTE_AQUI` | Todos | Falla la conexión a BD |
| `POSTGRES_DB` | Nombre de la base de datos | Sí | `sirccd_db` | Todos | Falla la conexión a BD |
| `REDIS_HOST` | Host de Redis | Sí | `redis` (Docker) / `localhost` | Todos | Falla la cola de tareas (RQ) |
| `REDIS_PORT` | Puerto de Redis | No (default `6379`) | `6379` | Todos | Usa default |
| `REDIS_DB` | Índice de base lógica de Redis | No (default `0`) | `0` | Todos | Usa default |
| `REDIS_PASSWORD` | Contraseña de Redis | Sí en producción | `CAMBIAR_REDIS_PASSWORD_AQUI` | Prod | Redis sin auth en producción es un riesgo de seguridad |
| `MINIO_ENDPOINT` | Host:puerto de MinIO | Sí | `minio:9000` (Docker) | Todos | Falla el almacenamiento de imágenes (cae a disco local si aplica el fallback) |
| `MINIO_ACCESS_KEY` | Access key de MinIO | Sí | `sirccd_admin` | Todos | Falla la autenticación con MinIO |
| `MINIO_SECRET_KEY` | Secret key de MinIO | Sí | `CAMBIAR_MINIO_SECRET_AQUI` | Todos | Falla la autenticación con MinIO |
| `MINIO_SECURE` | Usar TLS al conectar a MinIO | No (default `False`) | `False` (dev) / `True` (prod) | Todos | En producción debe ser `True` |
| `MINIO_BUCKET_IMAGES` | Bucket de imágenes de reportes | No (default `sirccd-images`) | `sirccd-images` | Todos | Usa default |
| `MINIO_BUCKET_MODELS` | Bucket de modelos ML | No (default `sirccd-models`) | `sirccd-models` | Todos | Usa default |
| `MINIO_SSE_ENABLED` | Cifrado server-side (SSE-S3) en MinIO | No | `False` | Prod (recomendado) | Sin cifrado en reposo de objetos |
| `ROBOFLOW_API_KEY` | API key del servicio de detección de daños | No, pero recomendada | `CAMBIAR_ROBOFLOW_KEY_AQUI` | Todos | Sin key, el backend usa un **detector simulado (mock)** — los reportes no se clasifican realmente |
| `ROBOFLOW_MODEL_ID` | Identificador del modelo en Roboflow | No (default `rd-roaddataset/5`) | `rd-roaddataset/5` | Todos | Usa default |
| `CONFIDENCE_THRESHOLD` | Umbral de confianza mínima de detección | No (default `0.4`) | `0.4` | Todos | Usa default |
| `IOU_THRESHOLD` | Umbral de IoU para supresión de duplicados en detección | No (default `0.4`) | `0.4` | Todos | Usa default |
| `FAISS_INDEX_PATH` | Ruta del índice FAISS para deduplicación visual | No (default `storage/faiss_index.bin`) | `storage/faiss_index.bin` | Todos | Usa default local |
| `DEDUPLICATION_VISUAL_MODEL` | Modelo primario de embeddings visuales | No (default `resnet50`) | `resnet50` | Todos | Usa default |
| `DEDUPLICATION_SECONDARY_MODEL` | Modelo secundario de embeddings (fusión) | No (default `clip-vit-base-patch32`) | `clip-vit-base-patch32` | Todos | Usa default |
| `DEDUPLICATION_ALLOW_HISTOGRAM_FALLBACK` | Permite fallback a histograma de color si los modelos fallan | No (default `True`) | `True` | Todos | Usa default |
| `VISUAL_SIMILARITY_THRESHOLD` | Distancia L2 máxima para considerar duplicado visual | No (default `0.15`) | `0.15` | Todos | Usa default |
| `GEO_DISTANCE_THRESHOLD` | Distancia máxima (m) para considerar duplicado geográfico | No (default `50.0`) | `50.0` | Todos | Usa default |
| `DEDUP_TIME_WINDOW_DAYS` | Ventana de tiempo (días) para deduplicación | No (default `30`) | `30` | Todos | Usa default |
| `DEDUP_VISUAL_GATE_THRESHOLD` | Umbral de corte previo a comparación visual completa | No (default `0.82`) | `0.82` | Todos | Usa default |
| `DEDUPLICATION_SCORE_THRESHOLD` | Score fusionado mínimo para marcar como duplicado | No (default `0.72`) | `0.72` | Todos | Usa default |
| `DEDUPLICATION_VISUAL_WEIGHT_PRIMARY` / `_SECONDARY` | Peso de cada modelo visual en el score fusionado | No (default `0.45` / `0.25`) | — | Todos | Usa defaults |
| `DEDUPLICATION_GEO_WEIGHT` | Peso de la señal geográfica en el score fusionado | No (default `0.20`) | `0.20` | Todos | Usa default |
| `DEDUPLICATION_TEXT_WEIGHT` | Peso de la señal textual (descripción) en el score fusionado | No (default `0.10`) | `0.10` | Todos | Usa default |
| `PRIORITY_POI_RADIUS_METERS` | Radio (m) para buscar POIs cercanos al calcular prioridad | No (default `500`) | `500` | Todos | Usa default |
| `PRIORITY_DUPLICATE_RADIUS_METERS` | Radio (m) para buscar duplicados al calcular prioridad | No (default `100`) | `100` | Todos | Usa default |
| `PRIORITY_DUPLICATE_TIME_WINDOW_DAYS` | Ventana temporal (días) para duplicados en el cálculo de prioridad | No (default `30`) | `30` | Todos | Usa default |
| `FIELD_ENCRYPTION_KEY` | Clave Fernet para cifrado de campos sensibles en BD (ej. teléfono) | Sí en producción | `CAMBIAR_FERNET_KEY_AQUI` (generar con `Fernet.generate_key()`) | Prod | Datos sensibles quedan sin cifrar en BD |
| `SECRET_KEY` | Clave de firma JWT | **Sí, crítico** | `CAMBIAR_JWT_SECRET_AQUI` (generar con `openssl rand -hex 32`) | Todos | **`core/config.py` trae un valor por defecto hardcodeado — debe confirmarse que producción lo sobreescribe** (ver [SECURITY.md](SECURITY.md)) |
| `ALGORITHM` | Algoritmo de firma JWT | No (default `HS256`) | `HS256` | Todos | Usa default |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Minutos de validez del access token | No (default `30`) | `30` | Todos | Usa default |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` / `SMTP_FROM` | Configuración de correo saliente para alertas SLA | No (solo si `SMTP_ENABLED=True`) | — | Prod (opcional) | Sin estas variables, las alertas SLA por correo no se envían |
| `SMTP_ENABLED` | Activa el envío de alertas SLA por correo | No (default `False`) | `False` | Prod (opcional) | Alertas SLA solo visibles en el dashboard, no por correo |
| `SLA_WARNING_HOURS_BEFORE` | Horas antes del vencimiento para alertar | No (default `4.0`) | `4.0` | Todos | Usa default |
| `SLA_CHECK_INTERVAL_MINUTES` | Frecuencia del chequeo periódico de SLA | No (default `30`) | `30` | Todos | Usa default |
| `LOG_LEVEL` | Nivel de logging | No (default `INFO`) | `INFO` | Todos | Usa default |
| `DOMAIN` | Dominio de producción (usado en plantillas de despliegue) | Sí en producción | `sirccd.example.com` | Prod | Solo relevante para `docker-compose.prod.yml`/proxy |
| `ADMIN_USERNAME` / `ADMIN_EMAIL` / `ADMIN_PASSWORD` / `ADMIN_FULL_NAME` | Usadas únicamente por `backend/scripts/seed_admin.py` para crear el admin inicial | Sí, al ejecutar el script | — | Setup inicial | El script falla explícitamente si `ADMIN_PASSWORD` no está definida (no hay contraseña por defecto) |
| `INTEGRATION_TEST` | Bandera usada por `tests/test_contract.py` para habilitar pruebas de contrato contra un servidor real | No | — | Test | Sin ella, las pruebas de contrato se saltan/usan modo local |

## Frontend

Fuente: `frontend/.env.example`, `frontend/next.config.js`.

| Variable | Descripción | Obligatoria | Valor de ejemplo | Entorno | Consecuencia si falta |
|---|---|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | URL base del backend consumida por el cliente HTTP (Axios) | Sí | `http://localhost:8000/api/v1` | Todos | El frontend no puede llamar al backend |
| `NEXT_PUBLIC_MAP_CENTER_LAT` | Latitud del centro por defecto del mapa | No | `19.4517` | Todos | Usa default embebido en `next.config.js` |
| `NEXT_PUBLIC_MAP_CENTER_LNG` | Longitud del centro por defecto del mapa | No | `-70.6970` | Todos | Usa default embebido en `next.config.js` |
| `NEXT_PUBLIC_MAP_DEFAULT_ZOOM` | Nivel de zoom inicial del mapa | No | `13` | Todos | Usa default embebido en `next.config.js` |
| `NEXT_PUBLIC_APP_NAME` | Nombre mostrado en la UI | No | `SIRCCD` | Todos | Sin uso confirmado en el código fuente (ver nota abajo) |
| `NEXT_PUBLIC_APP_VERSION` | Versión mostrada en la UI | No | `0.1.0` | Todos | Sin uso confirmado en el código fuente (ver nota abajo) |

> **Nota**: `NEXT_PUBLIC_APP_NAME` y `NEXT_PUBLIC_APP_VERSION` están declaradas en `frontend/.env.example` pero no se encontró ningún `process.env.NEXT_PUBLIC_APP_NAME`/`APP_VERSION` en `src/` durante la auditoría. Podrían ser aspiracionales o haber quedado huérfanas tras un refactor — no se eliminaron por incertidumbre (ver [REPOSITORY_AUDIT.md](REPOSITORY_AUDIT.md#6-código-potencialmente-obsoleto)).

> Debido a que Next.js inlinea las variables `NEXT_PUBLIC_*` **en tiempo de build** (ver `frontend/Dockerfile`), cambiar estas variables en producción requiere reconstruir la imagen, no solo reiniciar el contenedor.

## ML (`ml/.env.template`)

Módulo desacoplado, con su propio set de variables (entrenamiento, no producción): `MINIO_*` (propias, para subir/bajar artefactos), `WANDB_*` (Weights & Biases), `GOOGLE_PLACES_API_KEY`, `TORCH_HOME`, `CUDA_VISIBLE_DEVICES`, rutas de datasets. Estas variables solo se usan localmente/en Colab durante entrenamiento y no se cruzan con el `.env.example` de la raíz salvo por la convención de nombres `MINIO_ACCESS_KEY`/`MINIO_SECRET_KEY`.

## Variables usadas en `docker-compose.prod.yml`

Todas las variables listadas en el `.env.example` de la raíz (`DOMAIN`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `REDIS_PASSWORD`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `SECRET_KEY`, `FIELD_ENCRYPTION_KEY`, `ROBOFLOW_API_KEY`, `ROBOFLOW_MODEL_ID`) están efectivamente interpoladas en `docker-compose.prod.yml` — ninguna quedó como configuración muerta.
