# API

[← Volver al índice](../README.md)

Todas las rutas están bajo el prefijo `/api/v1` (`settings.API_V1_STR`). Documentación interactiva (Swagger) disponible en `/api/v1/docs` cuando el backend está corriendo.

**Convenciones de autenticación en las tablas:**

| Etiqueta | Significado |
|---|---|
| `none` | Endpoint público, sin autenticación |
| `ActiveUser` / `get_current_active_user` | Cualquier usuario autenticado y activo |
| `CurrentUser` / `get_current_user` | Usuario autenticado (variantes internas equivalentes en la práctica) |
| `OptionalUser` / `get_optional_user` | Autenticación opcional — también acepta URLs firmadas (`exp`/`sig`) |
| `SupervisorUser` / `require_supervisor` | Rol `supervisor` o `admin` |
| `require_admin` | Rol `admin` únicamente |

## Auth (`/api/v1/auth`)

| Método y ruta | Descripción | Auth | Body | Respuesta | Errores | Archivo |
|---|---|---|---|---|---|---|
| POST `/auth/register` | Registra un ciudadano (rol forzado a `ciudadano`) | none | `RegisterRequest` | `RegisterResponse` (201) | 400 email/username ya en uso | `api/routes/auth.py:39` |
| POST `/auth/login` | Login por username o email + password | none | `LoginRequest` | `LoginResponse` | 401 credenciales inválidas, 403 usuario inactivo | `api/routes/auth.py:103` |
| POST `/auth/login/oauth2` | Login compatible OAuth2 (form-encoded, para tooling/Swagger) | none | form OAuth2 | `Token` | 401, 403 | `api/routes/auth.py:170` |
| GET `/auth/me` | Datos del usuario autenticado | ActiveUser | — | `UserResponse` | — | `api/routes/auth.py:215` |
| POST `/auth/verify-token` | Verifica validez de un JWT | none | query `token` | `TokenVerification` | — | `api/routes/auth.py:227` |
| POST `/auth/refresh` | Cambia refresh token por access token nuevo | none | `RefreshTokenRequest` | `Token` | 401 token inválido/expirado/tipo incorrecto, usuario no encontrado/inactivo | `api/routes/auth.py:261` |
| POST `/auth/logout` | Logout (JWT stateless, el cliente descarta el token) | ActiveUser | — | dict | — | `api/routes/auth.py:316` |

## Deduplicación (`/api/v1/deduplication`)

| Método y ruta | Descripción | Auth | Body | Respuesta | Errores | Archivo |
|---|---|---|---|---|---|---|
| POST `/deduplication/check` | Evalúa si un reporte nuevo es duplicado (score fusionado visual+geo+texto) | ActiveUser | form: `image`, `latitude`, `longitude`, `damage_type`, `description?`, `visual_threshold?`, `geo_threshold?` | `DuplicateCheckResponse` | 500 | `api/routes/deduplication.py:29` |
| POST `/deduplication/similar` | Top-K reportes visual/geográficamente similares | ActiveUser | form: `image`, `latitude`, `longitude`, `damage_type`, `description?`, `top_k?` (1-50, default 10) | `SimilarReportsResponse` | 500 | `api/routes/deduplication.py:115` |
| POST `/deduplication/index/rebuild` | Reconstruye el índice FAISS desde reportes aprobados | SupervisorUser | form `batch_size?` (10-1000, default 100) | `IndexRebuildResponse` | 500 | `api/routes/deduplication.py:207` |
| GET `/deduplication/stats` | Estadísticas del servicio de deduplicación | ActiveUser | — | `DeduplicationStats` | 500 | `api/routes/deduplication.py:265` |
| POST `/deduplication/index/save` | Persiste el índice FAISS a disco | SupervisorUser | — | dict | 500 | `api/routes/deduplication.py:300` |
| GET `/deduplication/clusters` | Clustering espacial (DBSCAN) de reportes duplicados | ActiveUser | query `eps_meters?`, `min_samples?`, `damage_type?`, `time_window_days?` | `SpatialClusteringResponse` | 500 | `api/routes/deduplication.py:347` |
| POST `/deduplication/clusters/resolve` | Resuelve un cluster (rechaza no-primarios) | SupervisorUser | `ClusterResolveRequest` | `ClusterResolveResponse` | 404 cluster no encontrado, 500 | `api/routes/deduplication.py:434` |
| POST `/deduplication/clusters/resolve-all` | Resuelve todos los clusters detectados en lote | SupervisorUser | query `eps_meters?`, `min_samples?`, `damage_type?`, `time_window_days?`, `min_cluster_size?` (default 2) | `ClusterResolveResponse` | 500 | `api/routes/deduplication.py:485` |

## Reportes (`/api/v1/reportes`)

| Método y ruta | Descripción | Auth | Body | Respuesta | Errores | Archivo |
|---|---|---|---|---|---|---|
| GET `/reportes` | Lista reportes con filtros/paginación (ciudadano solo ve los propios) | ActiveUser | query `page`,`per_page`,`status`,`damage_type`,`severity`,`search`,`sort_by`,`sort_order` | dict paginado | — | `api/routes/reports.py:69` |
| PATCH `/reportes/{id}/review` | Aprueba/rechaza un reporte; al aprobar crea/fusiona un incidente | require_supervisor | `UpdateReportStatusRequest` | dict (id, status, reviewed_at, incident_id) | 404, 400 estado inválido | `api/routes/reports.py:160` |
| POST `/reportes` | Crea reporte con imagen+GPS; encola detección ML | ActiveUser | form: `image`, `latitude`, `longitude`, `description?`, `address?`, `city?`, `province?`, `focal_scale_factor?` | `CreateReportResponse` (201) | 500 error de imagen/BD | `api/routes/reports.py:274` |
| GET `/reportes/{id}` | Detalle de un reporte | ActiveUser | — | `ReportResponse` | 404, 403 (ciudadano no dueño) | `api/routes/reports.py:487` |
| GET `/reportes/{id}/image` | Sirve la imagen (original/anotada) vía proxy firmado | OptionalUser | query `variant` (original\|annotated), `exp?`, `sig?` | imagen (bytes) | 401 sin token/firma, 404 | `api/routes/reports.py:546` |
| GET `/reportes/jobs/{job_id}/status` | Estado de un job de detección ML (RQ) | SupervisorUser | — | dict | 404 job no encontrado | `api/routes/reports.py:630` |
| GET `/reportes/queue/stats` | Estadísticas de la cola ML | SupervisorUser | — | dict | 500 | `api/routes/reports.py:654` |
| POST `/reportes/verify-image` | Detecta rostros/placas en una imagen sin modificarla (pre-check de privacidad) | ActiveUser | form `image` | dict (is_clean, conteos, regiones, warnings) | 422 formato no soportado o >10MB | `api/routes/reports.py:677` |

## Configuración de prioridad (`/api/v1/admin/settings`)

| Método y ruta | Descripción | Auth | Body | Respuesta | Errores | Archivo |
|---|---|---|---|---|---|---|
| GET `/admin/settings/priority` | Obtiene pesos/config de score de prioridad (crea fila default si no existe) | require_admin | — | `PrioritySettingsResponse` | — | `api/routes/settings.py:69` |
| PUT `/admin/settings/priority` | Actualiza pesos/radios; los pesos deben sumar 1.0 | require_admin | `PrioritySettingsUpdateRequest` | `PrioritySettingsResponse` | 400 pesos no suman 1.0 | `api/routes/settings.py:79` |

## Incidentes (`/api/v1/incidents`)

| Método y ruta | Descripción | Auth | Body | Respuesta | Errores | Archivo |
|---|---|---|---|---|---|---|
| GET `/incidents/` | Lista con filtros avanzados/paginación | require_supervisor | query `status[]`,`priority[]`,`damage_type`,`severity`,`city`,`is_verified`,`date_from`,`date_to`,`zone_id`,`skip`,`limit`,`sort_by`,`sort_order` | `IncidentListResponse` | — | `api/routes/incidents.py:116` |
| GET `/incidents/{id}` | Detalle completo de un incidente | require_supervisor | — | `IncidentDetailResponse` | 404 | `api/routes/incidents.py:256` |
| PATCH `/incidents/{id}/status` | Cambia estado (transiciones validadas) | require_supervisor | `UpdateIncidentStatusRequest` | `IncidentDetailResponse` | 400 transición inválida, 500 | `api/routes/incidents.py:309` |
| PATCH `/incidents/{id}/details` | Actualiza horas estimadas de reparación y/o imagen "después" | require_supervisor | form `estimated_repair_hours?`, `after_image?` | dict | 404 | `api/routes/incidents.py:354` |
| POST `/incidents/{id}/after-image` | Sube foto "después" de la reparación | require_supervisor | form `image` | dict | 404, 500 | `api/routes/incidents.py:387` |
| GET `/incidents/{id}/image` | Sirve imagen antes/después vía proxy firmado | OptionalUser | query `variant` (before\|after), `exp?`, `sig?` | imagen (bytes) | 401, 404 | `api/routes/incidents.py:418` |
| POST `/incidents/{id}/recalculate-priority` | Recalcula score/nivel de prioridad | require_supervisor | — | `RecalculatePriorityResponse` | 404, 500 | `api/routes/incidents.py:486` |
| GET `/incidents/{id}/priority-breakdown` | Desglose de factores de prioridad (persistido o al vuelo) | require_supervisor | — | dict | 404, 500 | `api/routes/incidents.py:555` |
| GET `/incidents/stats/overview` | Estadísticas agregadas (distribución por estado/prioridad/tipo, cumplimiento SLA) | require_supervisor | — | `IncidentStatsResponse` | — | `api/routes/incidents.py:597` |
| GET `/incidents/{id}/audit` | Bitácora de auditoría completa | require_supervisor | — | `AuditLogListResponse` | 404 | `api/routes/incidents.py:733` |
| GET `/incidents/heatmap` | Puntos de mapa de calor ponderados por frecuencia/severidad/antigüedad | ActiveUser | query `weight_by`, `status[]?`,`damage_type?`,`severity?` | dict (points, weight_by, count) | — | `api/routes/incidents.py:763` |
| GET `/incidents/sla/expiring` | Incidentes por vencer/vencidos dentro de una ventana | require_supervisor | query `within_hours?` (default 4.0) | `SLAExpiringResponse` | — | `api/routes/incidents.py:836` |
| GET `/incidents/{id}/sla` | Estado de SLA de un incidente específico | require_supervisor | — | `SLAStatusResponse` | 404 | `api/routes/incidents.py:884` |
| GET `/incidents/sla/config` | Configuración de SLA activa | require_supervisor | — | `SLAConfigResponse` | — | `api/routes/incidents.py:909` |
| PUT `/incidents/sla/config` | Crea/actualiza configuración de SLA | require_admin | `UpdateSLAConfigRequest` | `SLAConfigResponse` | — | `api/routes/incidents.py:935` |
| POST `/incidents/sla/check` | Encola manualmente el job de chequeo de SLA | require_admin | — | dict (queued, job_id/error) | — | `api/routes/incidents.py:967` |

## Puntos de interés (`/api/v1/pois`)

| Método y ruta | Descripción | Auth | Body | Respuesta | Errores | Archivo |
|---|---|---|---|---|---|---|
| GET `/pois/` | Lista POIs agrupados en capas de riesgo (escuela/hospital/bomberos/centro comunitario) | ActiveUser | query `categories[]?`, `limit?` (1-5000, default 1000) | `POILayerListResponse` | — | `api/routes/pois.py:55` |

## Exportación (`/api/v1/export`)

| Método y ruta | Descripción | Auth | Body | Respuesta | Errores | Archivo |
|---|---|---|---|---|---|---|
| GET `/export/incidents/geojson` | Exporta incidentes como GeoJSON | SupervisorUser | query `status[]`,`priority[]`,`damage_type`,`severity`,`city`,`province`,`date_from`,`date_to`,`include_closed` | GeoJSON (JSON) | 400 rango de fechas o >10.000 registros, 500 | `api/routes/export.py:78` |
| GET `/export/incidents/csv` | Exporta lista detallada de incidentes como CSV | SupervisorUser | mismos filtros que geojson | text/csv (streaming) | 400, 500 | `api/routes/export.py:218` |
| GET `/export/kpis/csv` | Exporta KPIs agregados por período como CSV | SupervisorUser | query `date_from`, `date_to` (requeridos), `group_by` (day\|week\|month), `city?`, `province?` | text/csv (streaming) | 400 rango inválido o >730 días, 500 | `api/routes/export.py:330` |
| GET `/export/report/pdf` | Reporte mensual resumido en PDF | SupervisorUser | query `year` (2020-2100), `month` (1-12), `city?`, `province?` | application/pdf (streaming) | 500 | `api/routes/export.py:439` |
| GET `/export/status` | Estado del servicio de exportación (formatos/límites disponibles) | CurrentUser | — | `ExportStatusResponse` | — | `api/routes/export.py:480` |

## Usuarios (`/api/v1/users`)

| Método y ruta | Descripción | Auth | Body | Respuesta | Errores | Archivo |
|---|---|---|---|---|---|---|
| GET `/users/me` | Perfil propio | ActiveUser | — | `UserResponse` | — | `api/routes/users.py:31` |
| GET `/users/` | Lista con paginación/filtros | require_supervisor | query `page`,`per_page`,`role?`,`is_active?`,`search?` | dict (total/page/per_page/total_pages/users) | 400 rol inválido | `api/routes/users.py:39` |
| GET `/users/{id}` | Usuario por ID | require_supervisor | — | `UserResponse` | 404 | `api/routes/users.py:93` |
| POST `/users/` | Crea usuario con rol dado | require_admin | `UserCreate` | `UserResponse` (201) | 400 email/username en uso | `api/routes/users.py:111` |
| PATCH `/users/{id}` | Actualiza datos/rol/estado | require_admin | `UserUpdate` | `UserResponse` | 400 auto-cambio de rol/auto-desactivación/email o username en uso, 404 | `api/routes/users.py:147` |
| DELETE `/users/{id}` | Desactiva usuario (soft-delete) | require_admin | — | 204 | 400 auto-desactivación, 404 | `api/routes/users.py:209` |
| DELETE `/users/{id}/permanent` | Elimina usuario permanentemente | require_admin | — | 204 | 400 auto-eliminación, 404, 409 tiene registros asociados | `api/routes/users.py:234` |

## Zonas (`/api/v1/zones`)

| Método y ruta | Descripción | Auth | Body | Respuesta | Errores | Archivo |
|---|---|---|---|---|---|---|
| GET `/zones/` | Lista zonas administrativas para filtrado | ActiveUser | — | `List[dict]` (id, name, code) | — | `api/routes/zones.py:17` |

## Salud y métricas (`/api/v1/health`, `/api/v1/metrics`, `/api/v1/ping`)

| Método y ruta | Descripción | Auth | Body | Respuesta | Errores | Archivo |
|---|---|---|---|---|---|---|
| GET `/health` | Health check completo o por componente | none | query `component?` (database\|redis\|minio) | dict | 503 no saludable | `api/routes/health.py:17` |
| GET `/health/live` | Liveness probe | none | — | dict | 503 | `api/routes/health.py:72` |
| GET `/health/ready` | Readiness probe (BD+Redis) | none | — | dict | 503 | `api/routes/health.py:95` |
| GET `/metrics` | Métricas Prometheus | none | — | text/plain | — | `api/routes/health.py:125` |
| GET `/ping` | Ping simple | none | — | dict `{message: "pong"}` | — | `api/routes/health.py:157` |
