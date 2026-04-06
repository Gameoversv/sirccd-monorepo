# Guia de Pruebas - Flujo Completo SIRCCD

Esta guia cubre el flujo end-to-end del sistema para demostracion de avance. Cada paso incluye el comando exacto y el resultado esperado.

---

## Informacion de referencia rapida

| Servicio | URL | Credenciales |
|---------|-----|-------------|
| Backend API | http://localhost:8000/api/v1 | - |
| Swagger UI | http://localhost:8000/api/v1/docs | - |
| Frontend | http://localhost:3000 | - |
| MinIO Console | http://localhost:9001 | sirccd_admin / sirccd_password_2026 |
| PostgreSQL | localhost:5432 | sirccd_user / sirccd_password / sirccd_db |
| Redis | localhost:6379 | - |

**Prefijo de API:** `/api/v1`  
**Ruta de reportes:** `/api/v1/reportes` (en espanol)

---

## Paso 0: Prerequisitos

### Software requerido
- Docker Desktop instalado y corriendo
- Git

### Puertos que deben estar libres
```
8000  → Backend FastAPI
3000  → Frontend Next.js
5432  → PostgreSQL
6379  → Redis
9000  → MinIO API
9001  → MinIO Console
```

Para verificar si un puerto esta en uso (PowerShell):
```powershell
netstat -ano | findstr :8000
netstat -ano | findstr :3000
```

### Clonar o tener el repositorio
```bash
cd c:/Users/wilki/Proyectos/sirccd-monorepo/sirccd-monorepo
```

---

## Paso 1: Levantar todos los servicios

```bash
docker compose up -d
```

Esto levanta: PostgreSQL, Redis, MinIO, Backend, Worker, Frontend.

### Verificar que los contenedores esten corriendo

```bash
docker compose ps
```

Resultado esperado: todos los servicios en estado `running` o `healthy`.

```
NAME          STATUS
postgres      running (healthy)
redis         running (healthy)
minio         running (healthy)
minio-init    exited (0)       ← normal, es un job de inicializacion
backend       running (healthy)
frontend      running
```

### Verificar que MinIO se inicializo correctamente

```bash
docker compose logs minio-init
```

Debe mostrar que los buckets `sirccd-images` y `sirccd-models` fueron creados.

---

## Paso 2: Verificar salud del sistema

### 2.1 Ping basico

```bash
curl http://localhost:8000/api/v1/ping
```

Respuesta esperada:
```json
{"message": "pong"}
```

### 2.2 Health check completo

```bash
curl http://localhost:8000/api/v1/health
```

Respuesta esperada:
```json
{
  "status": "healthy",
  "components": {
    "database": {"status": "healthy"},
    "redis": {"status": "healthy"},
    "minio": {"status": "healthy"}
  },
  "timestamp": "2026-04-05T..."
}
```

> Si algun componente dice `unhealthy`, revisar logs: `docker compose logs <servicio>`

### 2.3 Verificar desde Swagger

Abrir: **http://localhost:8000/api/v1/docs**

El Swagger debe cargarse con todos los endpoints organizados por tag.

---

## Paso 3: Crear usuario ADMIN

El primer usuario se crea con rol CIUDADANO por defecto. Luego se actualiza via base de datos o con un usuario ADMIN existente.

### 3.1 Registrar el primer usuario (futuro admin)

**Via curl:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@sirccd.com",
    "username": "admin_sirccd",
    "password": "Admin2026!",
    "full_name": "Administrador SIRCCD"
  }'
```

**Via Swagger:** `POST /auth/register`

Respuesta esperada (HTTP 201):
```json
{
  "user_id": "uuid-aqui",
  "username": "admin_sirccd",
  "email": "admin@sirccd.com",
  "message": "User registered successfully"
}
```

### 3.2 Elevar el primer usuario a ADMIN (desde PostgreSQL)

```bash
docker exec -it $(docker compose ps -q postgres) psql -U sirccd_user -d sirccd_db -c \
  "UPDATE users SET role = 'ADMIN' WHERE email = 'admin@sirccd.com';"
```

Resultado esperado: `UPDATE 1`

---

## Paso 4: Login como ADMIN y obtener token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin_sirccd",
    "password": "Admin2026!"
  }'
```

Respuesta esperada:
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user_id": "uuid",
  "username": "admin_sirccd",
  "email": "admin@sirccd.com",
  "role": "ADMIN",
  "full_name": "Administrador SIRCCD"
}
```

**Guardar el `access_token`** — se usa en todos los pasos siguientes.

```bash
# PowerShell: guardar token en variable
$ADMIN_TOKEN = "eyJhbGci..."

# Bash/Linux: guardar token en variable
ADMIN_TOKEN="eyJhbGci..."
```

---

## Paso 5: Crear usuario SUPERVISOR

Con el token de ADMIN, crear un usuario supervisor para operacion municipal:

```bash
# PowerShell
curl -X POST http://localhost:8000/api/v1/users/ `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer $ADMIN_TOKEN" `
  -d '{
    "email": "supervisor@municipio.com",
    "username": "supervisor_op",
    "password": "Supervisor2026!",
    "full_name": "Supervisor Municipal",
    "role": "SUPERVISOR"
  }'
```

```bash
# Bash/Linux
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "email": "supervisor@municipio.com",
    "username": "supervisor_op",
    "password": "Supervisor2026!",
    "full_name": "Supervisor Municipal",
    "role": "SUPERVISOR"
  }'
```

Respuesta esperada (HTTP 201): usuario creado con `role: "SUPERVISOR"`.

---

## Paso 6: Crear usuario CIUDADANO

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ciudadano@correo.com",
    "username": "juan_ciudadano",
    "password": "Ciudadano2026!",
    "full_name": "Juan Perez"
  }'
```

El rol CIUDADANO es el default — no requiere accion adicional.

---

## Paso 7: Login como CIUDADANO

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "juan_ciudadano",
    "password": "Ciudadano2026!"
  }'
```

Guardar el token del ciudadano:
```bash
# PowerShell
$CITIZEN_TOKEN = "eyJhbGci..."

# Bash
CITIZEN_TOKEN="eyJhbGci..."
```

---

## Paso 8: Crear un reporte de dano vial

Este es el paso central. Se envia imagen + coordenadas + descripcion.

### 8.1 Preparar una imagen de prueba

Usar cualquier imagen JPG/PNG de un bache o grieta. Si no tienes una, puedes usar una imagen de prueba existente en:
```
backend/tests/manual/fixtures/
```

### 8.2 Enviar el reporte (multipart/form-data)

```bash
# PowerShell
curl -X POST http://localhost:8000/api/v1/reportes `
  -H "Authorization: Bearer $CITIZEN_TOKEN" `
  -F "image=@C:\ruta\a\imagen_bache.jpg" `
  -F "latitude=19.4517" `
  -F "longitude=-70.6970" `
  -F "description=Bache profundo en Av. Independencia frente al parque" `
  -F "address=Av. Independencia #45" `
  -F "city=Santiago"
```

```bash
# Bash/Linux
curl -X POST http://localhost:8000/api/v1/reportes \
  -H "Authorization: Bearer $CITIZEN_TOKEN" \
  -F "image=@/ruta/a/imagen_bache.jpg" \
  -F "latitude=19.4517" \
  -F "longitude=-70.6970" \
  -F "description=Bache profundo en Av. Independencia frente al parque" \
  -F "address=Av. Independencia #45" \
  -F "city=Santiago"
```

**Via Swagger:** `POST /reportes` → Click en "Try it out" → subir imagen y llenar campos.

Respuesta esperada (HTTP 201):
```json
{
  "id": "uuid-del-reporte",
  "status": "PROCESSING",
  "image_url": "http://localhost:9000/sirccd-images/...",
  "latitude": 19.4517,
  "longitude": -70.6970,
  "description": "Bache profundo en Av. Independencia frente al parque",
  "damage_type": "BACHE",
  "severity": "ALTA",
  "confidence": 0.89,
  "created_at": "2026-04-05T..."
}
```

Guardar el ID del reporte:
```bash
# PowerShell
$REPORT_ID = "uuid-del-reporte"

# Bash
REPORT_ID="uuid-del-reporte"
```

---

## Paso 9: Verificar el estado del reporte

### 9.1 Consultar el reporte por ID

```bash
# PowerShell
curl http://localhost:8000/api/v1/reportes/$REPORT_ID `
  -H "Authorization: Bearer $CITIZEN_TOKEN"

# Bash
curl http://localhost:8000/api/v1/reportes/$REPORT_ID \
  -H "Authorization: Bearer $CITIZEN_TOKEN"
```

El estado deberia haber cambiado de `PROCESSING` a `PENDING` despues del procesamiento ML.

### 9.2 Ver lista de reportes propios

```bash
curl "http://localhost:8000/api/v1/reportes?page=1&per_page=10" \
  -H "Authorization: Bearer $CITIZEN_TOKEN"
```

---

## Paso 10: Verificar la imagen en MinIO

1. Abrir **http://localhost:9001**
2. Login: `sirccd_admin` / `sirccd_password_2026`
3. Navegar al bucket `sirccd-images`
4. Ver la imagen subida (puede estar anonimizada si tenia rostros o placas)

---

## Paso 11: Login como SUPERVISOR y aprobar el reporte

### 11.1 Login del supervisor

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "supervisor_op",
    "password": "Supervisor2026!"
  }'
```

Guardar el token:
```bash
# PowerShell
$SUPERVISOR_TOKEN = "eyJhbGci..."

# Bash
SUPERVISOR_TOKEN="eyJhbGci..."
```

### 11.2 Ver todos los reportes pendientes

```bash
# PowerShell
curl "http://localhost:8000/api/v1/reportes?status=PENDING" `
  -H "Authorization: Bearer $SUPERVISOR_TOKEN"

# Bash
curl "http://localhost:8000/api/v1/reportes?status=PENDING" \
  -H "Authorization: Bearer $SUPERVISOR_TOKEN"
```

### 11.3 Aprobar el reporte

```bash
# PowerShell
curl -X PATCH "http://localhost:8000/api/v1/reportes/$REPORT_ID/review" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer $SUPERVISOR_TOKEN" `
  -d '{"status": "approved"}'

# Bash
curl -X PATCH "http://localhost:8000/api/v1/reportes/$REPORT_ID/review" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SUPERVISOR_TOKEN" \
  -d '{"status": "approved"}'
```

Respuesta esperada:
```json
{
  "status": "APPROVED",
  "incident_id": "uuid-del-incidente",
  "message": "Report approved and incident created/updated"
}
```

Guardar el ID del incidente:
```bash
# PowerShell
$INCIDENT_ID = "uuid-del-incidente"

# Bash
INCIDENT_ID="uuid-del-incidente"
```

> Al aprobar, el backend ejecuta el gate geo+visual (30m + cosine >= 0.82). Si hay incidente coincidente lo asocia; si no, crea uno nuevo.  
> Si la confianza ML del reporte era >= 0.75, la aprobacion ya ocurrio automaticamente al procesar el reporte.

---

## Paso 12: Ver el incidente creado

### 12.1 Lista de incidentes

```bash
# PowerShell
curl "http://localhost:8000/api/v1/incidents/" `
  -H "Authorization: Bearer $SUPERVISOR_TOKEN"

# Bash
curl "http://localhost:8000/api/v1/incidents/" \
  -H "Authorization: Bearer $SUPERVISOR_TOKEN"
```

### 12.2 Detalle del incidente

```bash
# PowerShell
curl "http://localhost:8000/api/v1/incidents/$INCIDENT_ID" `
  -H "Authorization: Bearer $SUPERVISOR_TOKEN"

# Bash
curl "http://localhost:8000/api/v1/incidents/$INCIDENT_ID" \
  -H "Authorization: Bearer $SUPERVISOR_TOKEN"
```

Respuesta esperada incluye:
```json
{
  "id": "uuid",
  "status": "OPEN",
  "priority": "ALTA",
  "damage_type": "BACHE",
  "severity": "ALTA",
  "latitude": 19.4517,
  "longitude": -70.6970,
  "report_count": 1,
  "priority_score": 0.82,
  "priority_factors": {
    "severity": 0.35,
    "time_elapsed": 0.12,
    "damage_type": 0.15,
    "poi_proximity": 0.15,
    "duplicates": 0.05
  },
  "status_history": [...]
}
```

### 12.3 Estadisticas de incidentes

```bash
curl "http://localhost:8000/api/v1/incidents/stats/overview" \
  -H "Authorization: Bearer $SUPERVISOR_TOKEN"
```

---

## Paso 13: Actualizar el estado del incidente

Simular que un operario va al sitio a reparar el bache:

```bash
# PowerShell
curl -X PATCH "http://localhost:8000/api/v1/incidents/$INCIDENT_ID/status" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer $SUPERVISOR_TOKEN" `
  -d '{
    "status": "IN_PROGRESS",
    "notes": "Cuadrilla asignada. Inicio de reparacion programado para manana."
  }'

# Bash
curl -X PATCH "http://localhost:8000/api/v1/incidents/$INCIDENT_ID/status" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SUPERVISOR_TOKEN" \
  -d '{
    "status": "IN_PROGRESS",
    "notes": "Cuadrilla asignada. Inicio de reparacion programado para manana."
  }'
```

Luego marcar como resuelto:

```bash
curl -X PATCH "http://localhost:8000/api/v1/incidents/$INCIDENT_ID/status" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SUPERVISOR_TOKEN" \
  -d '{
    "status": "RESOLVED",
    "notes": "Bache reparado con asfalto en frio. Tiempo de intervencion: 3 horas."
  }'
```

---

## Paso 14: Recalcular prioridad del incidente

```bash
# PowerShell
curl -X POST "http://localhost:8000/api/v1/incidents/$INCIDENT_ID/recalculate-priority" `
  -H "Authorization: Bearer $SUPERVISOR_TOKEN"

# Bash
curl -X POST "http://localhost:8000/api/v1/incidents/$INCIDENT_ID/recalculate-priority" \
  -H "Authorization: Bearer $SUPERVISOR_TOKEN"
```

Respuesta muestra factores de prioridad desglosados:
```json
{
  "old_priority": "ALTA",
  "new_priority": "MEDIA",
  "score": 0.65,
  "factors": {
    "severity": 0.35,
    "time_elapsed": 0.20,
    "damage_type": 0.15,
    "poi_proximity": 0.20,
    "duplicates": 0.10
  }
}
```

---

## Paso 15: Ver datos geoespaciales (heatmap)

```bash
curl "http://localhost:8000/api/v1/incidents/heatmap?weight_by=severity" \
  -H "Authorization: Bearer $SUPERVISOR_TOKEN"
```

Respuesta con puntos para visualizar en mapa:
```json
{
  "points": [
    [19.4517, -70.6970, 0.85]
  ],
  "weight_by": "severity",
  "count": 1
}
```

---

## Paso 16: Exportar datos

### 16.1 Exportar incidentes en GeoJSON

```bash
# PowerShell
curl "http://localhost:8000/api/v1/export/incidents/geojson" `
  -H "Authorization: Bearer $SUPERVISOR_TOKEN" `
  -o incidentes_export.geojson

# Bash
curl "http://localhost:8000/api/v1/export/incidents/geojson" \
  -H "Authorization: Bearer $SUPERVISOR_TOKEN" \
  -o incidentes_export.geojson
```

### 16.2 Exportar en CSV

```bash
# PowerShell
curl "http://localhost:8000/api/v1/export/incidents/csv" `
  -H "Authorization: Bearer $SUPERVISOR_TOKEN" `
  -o incidentes_export.csv

# Bash
curl "http://localhost:8000/api/v1/export/incidents/csv" \
  -H "Authorization: Bearer $SUPERVISOR_TOKEN" \
  -o incidentes_export.csv
```

### 16.3 Exportar KPIs

```bash
curl "http://localhost:8000/api/v1/export/metrics/kpi?group_by=day" \
  -H "Authorization: Bearer $SUPERVISOR_TOKEN" \
  -o kpis.csv
```

---

## Paso 17: Demostrar deduplicacion geo+visual

El sistema fusiona reportes en el momento de aprobacion usando un gate geo+visual.  
El criterio es: misma zona (30 metros) **Y** similitud visual coseno >= 0.82.

### 17.1 Caso A — mismo dano (deberia fusionar)

1. Subir reporte 1 con `imagen_bache_A.jpg` en coordenadas (19.4517, -70.6970)
2. Aprobarlo → se crea Incidente #1
3. Subir reporte 2 con `imagen_bache_A.jpg` (misma imagen o foto similar del mismo bache) en las mismas coordenadas
4. Aprobarlo → **debe asociarse al Incidente #1** (no crear incidente nuevo)

Verificar en logs del backend:
```
Dedup visual: reporte X vs incidente Y sim=0.998 → fusionando
```

### 17.2 Caso B — danos diferentes en la misma cuadra (NO debe fusionar)

1. Tomar `imagen_bache.jpg` y `imagen_grieta.jpg` (fotos visualmente distintas)
2. Subir ambas en coordenadas identicas (a menos de 30 metros)
3. Aprobar reporte 1 → se crea Incidente #1
4. Aprobar reporte 2 → **debe crear Incidente #2 separado**

Verificar en logs:
```
Dedup visual: reporte X vs incidente Y sim=0.512 → rechazado (< 0.82)
```

### 17.3 Caso C — autoaprobacion por confianza ML

Si Roboflow devuelve `confidence >= 0.75`, el reporte se aprueba automaticamente sin intervencion del supervisor.  
El gate geo+visual se ejecuta igualmente. Verificar en logs:
```
Auto-aprobando reporte X (confianza=0.87 >= 0.75)
```

### 17.4 Ver estadisticas del indice FAISS

```bash
curl "http://localhost:8000/api/v1/deduplication/stats" \
  -H "Authorization: Bearer $SUPERVISOR_TOKEN"
```

---

## Paso 18: Consultar POIs cercanos

```bash
curl "http://localhost:8000/api/v1/pois/?categories=school&categories=hospital&limit=10" \
  -H "Authorization: Bearer $SUPERVISOR_TOKEN"
```

Los POIs muestran la proximidad al incidente para el calculo de prioridad.

---

## Paso 19: Recorrido del Dashboard Frontend

### 19.1 Abrir el frontend

Navegar a: **http://localhost:3000**

### 19.2 Login desde el frontend

Usar las credenciales del supervisor:
- Email: `supervisor@municipio.com`
- Password: `Supervisor2026!`

### 19.3 Recorrido de pantallas para demostracion

| Pantalla | URL | Que mostrar |
|----------|-----|-------------|
| Dashboard | `/dashboard` | KPIs: total reportes, incidentes abiertos, resolucion |
| Mapa | `/dashboard/map` | Marcadores de incidentes en el mapa, capa de calor |
| Reportes | `/dashboard/reports` | Tabla con filtros, estado, severidad |
| Incidentes | `/dashboard/incidents` | Tabla con prioridad, estado, tipo de dano |
| Detalle incidente | `/dashboard/incidents/{id}` | Timeline de estados, reportes asociados, mapa miniatura |
| Usuarios | `/dashboard/users` | Solo visible con rol ADMIN |

---

## Paso 20: Gestion de usuarios (ADMIN)

### 20.1 Listar todos los usuarios

```bash
curl "http://localhost:8000/api/v1/users/?page=1&per_page=20" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### 20.2 Ver perfil propio

```bash
curl "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## Errores comunes y solucion

### "Connection refused" al llamar la API

```bash
# Verificar que el backend este corriendo
docker compose ps
docker compose logs backend
```

### "401 Unauthorized"

El token expiro (30 minutos). Hacer login nuevamente.

### "422 Unprocessable Entity"

Verificar que el body/form-data tenga los campos requeridos y el formato correcto.

### El reporte queda en estado PROCESSING

El worker puede estar ocupado o caido:
```bash
docker compose logs worker
docker compose restart worker
```

### MinIO no accesible

```bash
docker compose restart minio
docker compose logs minio-init  # verificar que los buckets se crearon
```

### Frontend no carga

```bash
docker compose logs frontend
# Si el frontend no puede conectar al backend:
# Verificar NEXT_PUBLIC_API_URL en docker-compose.yml
```

---

## Flujo completo en resumen

```
[Docker Compose Up] → [Health Check OK]
    ↓
[Registrar Admin] → [Elevar rol a ADMIN en DB]
    ↓
[Crear Supervisor] → [Crear Ciudadano]
    ↓
[Login Ciudadano] → [Subir reporte con imagen]
    ↓
[ML procesa: YOLO clasifica + embeddings + dedup check]
    ↓
[Reporte: PENDING] → [Login Supervisor] → [Aprobar reporte]
    ↓
[Incidente creado automaticamente] → [Prioridad calculada]
    ↓
[Actualizar estado: OPEN → IN_PROGRESS → RESOLVED]
    ↓
[Exportar GeoJSON/CSV] → [Ver en Dashboard Frontend]
    ↓
[Demostrar deduplicacion: segundo reporte = mismo incidente]
```

---

*Documento generado el 2026-04-05 para demostracion de avance del proyecto SIRCCD.*
