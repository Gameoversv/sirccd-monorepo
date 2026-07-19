# Tareas en segundo plano

[← Volver al índice](../README.md)

## Infraestructura de cola

Redis + RQ (Redis Queue). `services/queue_service.py` gestiona la conexión y el encolado; el worker (`worker.py` en Linux/Railway, `worker_windows.py` en desarrollo Windows) consume los jobs. Colas usadas: `ml_inference` (timeout 300s) y `default`.

## `tasks/ml_tasks.py`

### `process_report_ml_detection(report_id: int, focal_scale_factor: Optional[float] = None) -> dict`

Job principal de detección: se encola automáticamente cada vez que se crea un reporte (`POST /reportes`). Corre en el proceso del worker (no en el proceso del API), abre su propia sesión de base de datos, resuelve la imagen desde `report.image_url` (no asume filesystem compartido con el API) y delega a `services/report_processing_service.process_report_detection`, que:

1. Llama a `ml_service` para clasificar el daño (Roboflow, o detector mock si falta `ROBOFLOW_API_KEY`).
2. Genera una imagen anotada con las detecciones.
3. Indexa el reporte en el sistema de deduplicación (FAISS).
4. Si corresponde, dispara la creación/fusión de un incidente.

No relanza excepciones al fallar — captura el error y devuelve `{"report_id", "success": False, "error"}`, consultable vía `GET /reportes/jobs/{job_id}/status`.

### `test_task(message: str) -> dict`

Job de diagnóstico para verificar que la conexión RQ/Redis funciona, sin lógica de negocio.

## `tasks/sla_tasks.py`

### `check_sla_alerts() -> dict`

Job periódico (no un cron nativo de RQ — se debe encolar externamente, ver más abajo):

1. Abre sesión de BD, obtiene emails de usuarios `admin`/`supervisor` activos (`_get_admin_emails`).
2. Busca incidentes por vencer dentro de `SLA_WARNING_HOURS_BEFORE` (`sla_service.get_expiring_incidents`) y envía `notification_service.send_sla_warning`.
3. Busca incidentes vencidos (`sla_service.get_overdue_incidents`) y envía `notification_service.send_sla_breach`.
4. Devuelve `{checked_at, expiring_count, overdue_count, warnings_sent, breaches_sent}`.

**Cómo se dispara**: puede encolarse manualmente vía `POST /incidents/sla/check` (requiere rol admin), o programarse externamente (ej. `rq-scheduler`, cron del sistema, o un scheduler de Railway) usando `SLA_CHECK_INTERVAL_MINUTES` como referencia de frecuencia — **no se encontró en el repositorio un scheduler configurado que lo dispare automáticamente**; confirmar con el equipo si esto corre vía una integración externa (ej. cron job de Railway) no versionada aquí.

## Consultar el estado de un job

```
GET /api/v1/reportes/jobs/{job_id}/status   (requiere rol supervisor)
GET /api/v1/reportes/queue/stats            (requiere rol supervisor)
```

## Levantar el worker localmente

```bash
cd backend
# Linux/Railway:
python worker.py
# Windows (RQ no soporta fork):
python worker_windows.py
```
