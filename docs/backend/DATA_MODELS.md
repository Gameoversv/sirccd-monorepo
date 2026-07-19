# Modelos de datos

[← Volver al índice](../README.md)

Ver también el esquema de base de datos y diagrama de relaciones en [../database/SCHEMA.md](../database/SCHEMA.md). Este documento detalla los modelos SQLAlchemy tal como están definidos en `backend/models/`.

## User (`users`) — `models/user.py`

| Campo | Tipo | Restricciones |
|---|---|---|
| id | Integer | PK |
| email | String(255) | unique, indexed, not null |
| username | String(100) | unique, indexed, not null |
| full_name | String(255) | nullable |
| phone | EncryptedString(200) | nullable — **cifrado en reposo (Fernet, S-03)** |
| hashed_password | String(255) | not null |
| is_active | Boolean | default `True`, not null |
| is_verified | Boolean | default `False`, not null |
| role | Enum(`UserRole`) | default `ciudadano`, not null |
| created_at, updated_at | DateTime | — |
| last_login | DateTime | nullable |

Relaciones: `reports` → `Report` (cascade all, delete-orphan), `incidents` → `Incident` (por `Incident.reported_by`).
Enum `UserRole`: `admin`, `ciudadano`, `supervisor`.

## Report (`reports`) — `models/report.py`

| Campo | Tipo | Restricciones |
|---|---|---|
| id | Integer | PK |
| user_id | Integer | FK → `users.id`, not null, indexed |
| location | Geography(POINT, srid=4326) | not null |
| address, city, province | String | nullable |
| damage_type | Enum(`DamageType`) | not null |
| severity | Enum(`SeverityLevel`) | not null |
| confidence | Float | not null (0.0–1.0) |
| image_url | String(500) | not null |
| image_width, image_height | Integer | nullable |
| detections_json | Text | nullable |
| status | Enum(`ReportStatus`) | default `pending`, not null, indexed |
| description | Text | nullable |
| rejection_reason | Text | nullable |
| duplicate_of_report_id | Integer | FK → `reports.id` (autorreferencia), nullable, indexed |
| created_at | DateTime | indexed |
| updated_at, reviewed_at | DateTime | nullable |

Relaciones: `user` → `User`; `incident` → `Incident` (uno a uno, `uselist=False`); `primary_report` → `Report` (autorreferencia, `backref=duplicate_reports`).
Enums: `ReportStatus` = `pending, approved, rejected, processing`; `DamageType` = `bache, grieta`; `SeverityLevel` = `baja, media, alta`.

## Incident (`incidents`) — `models/incident.py`

| Campo | Tipo | Restricciones |
|---|---|---|
| id | Integer | PK |
| report_id | Integer | FK → `reports.id`, not null, **unique**, indexed |
| reported_by | Integer | FK → `users.id`, not null, indexed |
| location | Geography(POINT, srid=4326) | not null |
| address, city, province | String | nullable |
| damage_type | Enum(`DamageType`) | not null, indexed |
| severity | Enum(`SeverityLevel`) | not null, indexed |
| priority | Enum(`PriorityLevel`) | not null, indexed |
| priority_score | Float | nullable |
| priority_breakdown | JSON | nullable |
| status | Enum(`IncidentStatus`) | default `open`, not null, indexed |
| estimated_repair_hours | Float | nullable |
| started_at, completed_at, verified_at | DateTime | nullable |
| is_verified | Boolean | default `False`, not null |
| verified_by | Integer | FK → `users.id`, nullable |
| verification_notes | Text | nullable |
| before_image_url, after_image_url | String(500) | nullable |
| notes | Text | nullable |
| sla_deadline | DateTime | nullable, indexed |
| created_at | DateTime | indexed |
| updated_at | DateTime | — |

Relaciones: `original_report` → `Report`; `reported_by_user` → `User`; `metrics` → `Metric` (cascade delete-orphan); `audit_logs` → `IncidentAuditLog` (cascade delete-orphan, ordenado por `created_at`).
Enums: `IncidentStatus` = `open, in_progress, resolved, verified, closed`; `PriorityLevel` = `baja, media, alta, critica`.

## IncidentAuditLog (`incident_audit_logs`) — `models/incident_audit_log.py`

| Campo | Tipo | Restricciones |
|---|---|---|
| id | Integer | PK |
| incident_id | Integer | FK → `incidents.id` (ON DELETE CASCADE), not null, indexed |
| user_id | Integer | FK → `users.id` (ON DELETE SET NULL), nullable |
| event_type | String(50) | not null, indexed |
| field_name | String(100) | nullable |
| old_value, new_value | String(500) | nullable |
| notes | Text | nullable |
| created_at | DateTime | indexed |

Relaciones: `incident` → `Incident`; `user` → `User`.

## Metric (`metrics`) — `models/metric.py`

| Campo | Tipo | Restricciones |
|---|---|---|
| id | Integer | PK |
| incident_id | Integer | FK → `incidents.id`, nullable, indexed |
| metric_type | String(100) | not null, indexed |
| value | Float | not null |
| unit | String(50) | nullable |
| category | String(100) | nullable, indexed |
| subcategory | String(100) | nullable |
| metadata_json | Text | nullable |
| notes | Text | nullable |
| recorded_at, created_at | DateTime | indexed / — |

Relaciones: `incident` → `Incident`.

## POI (`pois`) — `models/poi.py`

| Campo | Tipo | Restricciones |
|---|---|---|
| id | Integer | PK |
| name | String(500) | not null |
| category | Enum(`POICategory`) | not null, indexed |
| location | Geography(POINT, srid=4326) | not null |
| address, city, province | String(100/500) | nullable |
| source | String(100) | nullable |
| external_id | String(255) | nullable |
| priority_weight | Integer | default `1`, not null |
| created_at, updated_at | DateTime | — |

Sin relaciones definidas. Enum `POICategory`: `school, university, hospital, clinic, fire_station, police_station, bridge, bus_station, commercial, other`.

## Zone (`zones`) — `models/zone.py`

| Campo | Tipo | Restricciones |
|---|---|---|
| id | Integer | PK |
| name | String(200) | not null, unique, indexed |
| code | String(50) | nullable, unique, indexed |
| boundary | Geography(POLYGON, srid=4326) | not null |
| created_at | DateTime | — |

Sin relaciones definidas.

## PrioritySetting (`priority_settings`) — `models/priority_setting.py`

Fila de configuración global (patrón singleton, se autocrea con defaults si no existe — ver `GET /admin/settings/priority`).

| Campo | Tipo | Default |
|---|---|---|
| weight_severity | Float | 0.35 |
| weight_age | Float | 0.20 |
| weight_damage_type | Float | 0.15 |
| weight_location | Float | 0.20 |
| weight_duplicates | Float | 0.10 |
| poi_radius_meters | Integer | 500 |
| duplicate_radius_meters | Integer | 100 |
| duplicate_time_window_days | Integer | 30 |
| clustering_eps_meters | Integer | 50 |
| clustering_min_samples | Integer | 2 |
| updated_by | Integer (FK → `users.id`) | nullable |

> Los 5 pesos (`weight_*`) deben sumar 1.0 — validado en `PUT /admin/settings/priority` (400 si no cumple).

## SLAConfig (`sla_configs`) — `models/sla_config.py`

Fila de configuración global de umbrales de SLA por nivel de prioridad.

| Campo | Tipo | Default |
|---|---|---|
| sla_hours_baja | Float | 72.0 |
| sla_hours_media | Float | 48.0 |
| sla_hours_alta | Float | 24.0 |
| sla_hours_critica | Float | 8.0 |
| warning_threshold_pct | Float | 0.8 |
| updated_by | Integer (FK → `users.id`) | nullable |
