# Servicios

[← Volver al índice](../README.md)

| Servicio | Archivo | Responsabilidad | Clases/funciones públicas | Módulos que lo usan |
|---|---|---|---|---|
| Anonimización | `services/anonymizer.py` | Difumina rostros y placas en imágenes antes de persistirlas (YOLO11s local) | `ImageAnonymizer`, `detect_faces`, `detect_plates_cascade`, `detect_plates_basic` | `reports.py` (creación de reporte, verify-image) |
| Deduplicación | `services/deduplication_service.py` | Score fusionado (embeddings visuales ResNet50/CLIP + geo + texto) respaldado por FAISS para detectar reportes duplicados | `DeduplicationService`, `VisualEmbedder`, `FAISSIndex`, `get_deduplication_service(db)` | `api/routes/deduplication.py`, `report_processing_service.py` |
| EXIF | `services/exif_service.py` | Extrae metadatos GPS/focal (normalización de zoom) y luego elimina todo el EXIF antes de guardar la imagen | `ExifData`, funciones de extracción | `reports.py` |
| Exportación | `services/export_service.py` | Genera exportaciones de incidentes/KPIs en GeoJSON, CSV y PDF | `ExportService`, `get_export_service(db)` | `api/routes/export.py` |
| Salud | `services/health_service.py` | Verifica estado de BD/Redis/MinIO, expone probes de liveness/readiness | `HealthCheckService`, `get_health_service(db)` | `api/routes/health.py` |
| Inferencia ML | `services/ml_service.py` | Detección de daños vía API hospedada de Roboflow, cálculo de severidad | `MLInferenceService`, `get_ml_service()`, `ml_service` | `report_processing_service.py`, `tasks/ml_tasks.py` |
| Notificaciones | `services/notification_service.py` | Envía correos de alerta SLA (advertencia y vencimiento) vía SMTP | `send_sla_warning`, `send_sla_breach` | `tasks/sla_tasks.py` |
| Prioridad | `services/priority_service.py` | Calcula/recalcula score de prioridad de incidentes (severidad, antigüedad, tipo de daño, proximidad a POIs, duplicados) | `PriorityService`, `get_priority_service(db)` | `api/routes/incidents.py`, `report_processing_service.py` |
| Cola de tareas | `services/queue_service.py` | Gestiona la cola RQ respaldada por Redis para jobs de detección ML | `QueueService`, `get_queue_service()`, `queue_service` | `api/routes/reports.py`, `tasks/ml_tasks.py` |
| Procesamiento de reportes | `services/report_processing_service.py` | Pipeline post-creación de reporte: detección ML, imagen anotada, indexado de deduplicación, creación/fusión automática de incidente | `process_report_detection`, `resolve_incident_dedup` | `tasks/ml_tasks.py` (ejecutado por el worker RQ) |
| SLA | `services/sla_service.py` | Calcula plazos y estado de SLA, identifica incidentes por vencer/vencidos | `get_sla_hours`, `get_sla_status`, `get_sla_info`, `get_expiring_incidents`, `get_overdue_incidents` | `api/routes/incidents.py`, `tasks/sla_tasks.py` |
| Clustering espacial | `services/spatial_clustering_service.py` | Clustering DBSCAN de reportes para detectar grupos de daño duplicado | `SpatialClusteringService`, `get_clustering_params` | `api/routes/deduplication.py` |
| Almacenamiento | `services/storage.py` | Sube/descarga/lee imágenes en MinIO, con fallback a disco local | `StorageService`, `storage_service` | `reports.py`, `incidents.py`, `report_processing_service.py` |

## Efectos secundarios y errores esperados

- **`report_processing_service.process_report_detection`** es el punto donde más servicios convergen: llama a `ml_service` (puede fallar/usar mock si `ROBOFLOW_API_KEY` falta), `deduplication_service` (indexa el nuevo reporte) y `priority_service` (si el reporte se convierte en incidente). Un fallo aquí ocurre dentro del worker RQ, no del request HTTP original — el cliente que creó el reporte no se entera de errores posteriores a la respuesta `201` inicial salvo que consulte `GET /reportes/jobs/{job_id}/status`.
- **`storage.py`** cae a disco local si MinIO no responde — comportamiento intencional para desarrollo, pero silencioso (ver [../SECURITY.md](../SECURITY.md)).
- **`sla_tasks.check_sla_alerts`** depende de `notification_service`, que a su vez depende de `SMTP_ENABLED`; si está deshabilitado, las alertas solo quedan disponibles vía API (`/incidents/sla/expiring`), no se notifican por correo.
