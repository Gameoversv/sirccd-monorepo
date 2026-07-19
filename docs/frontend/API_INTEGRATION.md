# Integración con la API

[← Volver al índice](../README.md)

Cliente HTTP: Axios (`src/services/api.ts`), URL base `NEXT_PUBLIC_API_URL` (default `http://localhost:8000/api/v1`). Interceptor de request adjunta `Authorization: Bearer <token>` leyendo `localStorage` (clave `sirccd-auth-storage`); interceptor de response normaliza errores `detail` de Pydantic y, ante `401`, limpia el storage y redirige a `/login`.

Correspondencia completa con [../backend/API.md](../backend/API.md).

## authService

| Función | Endpoint | Propósito |
|---|---|---|
| `login(credentials)` | `POST /auth/login` | Autentica, retorna token+rol |
| `register(data)` | `POST /auth/register` | Auto-registro de ciudadano |
| `getMe()` | `GET /auth/me` | Perfil del usuario actual |
| `logout()` | (solo cliente) | Limpia `sirccd-auth-storage` de localStorage |

## incidentsService

| Función | Endpoint | Propósito |
|---|---|---|
| `getIncidents(filters, page, perPage)` | `GET /incidents?...` | Lista paginada/filtrada |
| `getIncident(id)` | `GET /incidents/{id}` | Detalle completo |
| `updateStatus(id, status, notes?)` | `PATCH /incidents/{id}/status` | Cambia estado del flujo |
| `uploadAfterImage(id, formData)` | `POST /incidents/{id}/after-image` | Sube foto "después" |
| `exportIncidents(options)` | `GET /export/incidents/{csv\|geojson}?...` | Exporta como blob CSV/GeoJSON |
| `exportMonthlyReport(year, month)` | `GET /export/report/pdf?...` | Blob de reporte PDF mensual |
| `exportKpis(groupBy?)` | `GET /export/kpis/csv?...` | CSV de KPIs del mes actual |
| `recalculatePriority(id)` | `POST /incidents/{id}/recalculate-priority` | Fuerza recálculo de score |
| `getPriorityBreakdown(id)` | `GET /incidents/{id}/priority-breakdown` | Desglose sin recalcular |
| `updateDetails(id, horas)` | `PATCH /incidents/{id}/details` (multipart) | Fija horas estimadas de reparación |
| `getStats()` | `GET /incidents/stats/overview` | Overview de KPIs del dashboard |
| `getAuditLog(id)` | `GET /incidents/{id}/audit` | Bitácora de cambios |
| `getSLAStatus(id)` | `GET /incidents/{id}/sla` | Estado de SLA de un incidente |
| `getSLAExpiring(withinHours?)` | `GET /incidents/sla/expiring?within_hours=` | Incidentes por vencer/vencidos |
| `getSLAConfig()` | `GET /incidents/sla/config` | Umbrales de SLA por prioridad |
| `updateSLAConfig(data)` | `PUT /incidents/sla/config` | Actualiza umbrales (admin) |
| `getHeatmapData(weightBy, filters?)` | `GET /incidents/heatmap?weight_by=...` | Puntos ponderados para mapa de calor |

## poisService

| Función | Endpoint | Propósito |
|---|---|---|
| `getPOILayers(options?)` | `GET /pois?categories=...&limit=` | Marcadores de POI para capas de riesgo del mapa |

## prioritySettingsService

| Función | Endpoint | Propósito |
|---|---|---|
| `getPrioritySettings()` | `GET /admin/settings/priority` | Pesos/radios de priorización |
| `updatePrioritySettings(data)` | `PUT /admin/settings/priority` | Guarda configuración de priorización |

## reportsService

| Función | Endpoint | Propósito |
|---|---|---|
| `getReports(filters, page, perPage)` | `GET /reportes?...` | Lista paginada/filtrada de reportes propios |
| `getReport(id)` | `GET /reportes/{id}` | Detalle de un reporte |
| `createReport(formData)` | `POST /reportes` (multipart) | Crea nuevo reporte ciudadano |
| `updateReport(id, data)` | `PATCH /reportes/{id}` | Actualización parcial |
| `deleteReport(id)` | `DELETE /reports/{id}` | ⚠️ **Ruta inconsistente** — usa `/reports` en vez de `/reportes`. El backend documentado en [../backend/API.md](../backend/API.md) no expone `DELETE /reportes/{id}` en absoluto; este endpoint probablemente no funciona tal como está. Ver `src/services/reportsService.ts:54`. No corregido en esta fase — requiere decisión del equipo (¿implementar el endpoint en el backend, o corregir la ruta si ya existe con otro nombre?) |
| `checkDuplicate(formData)` | `POST /deduplication/check` (multipart) | Detecta duplicados a partir de una imagen |
| `verifyImage(file)` | `POST /reportes/verify-image` (multipart) | Chequeo de privacidad rostro/placa pre-subida |

## usersService

| Función | Endpoint | Propósito |
|---|---|---|
| `getMe()` | `GET /users/me` | Perfil/rol actualizado del usuario actual |
| `listUsers(params?)` | `GET /users?...` | Lista paginada/filtrada (admin/supervisor) |
| `getUser(id)` | `GET /users/{id}` | Detalle de un usuario |
| `createUser(data)` | `POST /users` | Crea usuario (admin) |
| `updateUser(id, data)` | `PATCH /users/{id}` | Actualiza campos/rol/estado |
| `deactivateUser(id)` | `DELETE /users/{id}` | Desactiva (soft-delete) |
| `deleteUser(id)` | `DELETE /users/{id}/permanent` | Elimina permanentemente |

## zonesService

| Función | Endpoint | Propósito |
|---|---|---|
| `getZones()` | `GET /zones/` | Lista de zonas geográficas para filtros |
