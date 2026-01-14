# API REST - SIRCCD

## 📖 Descripción

Este directorio contiene la especificación OpenAPI v3 de la API REST del Sistema Inteligente Urbano para Reporte y Priorización de Daños Viales (SIRCCD).

La API permite la integración entre el frontend web, la aplicación móvil y los servicios backend, incluyendo:

- Gestión de reportes ciudadanos
- Clasificación automática mediante IA
- Deduplicación de reportes
- Priorización multicriterio de incidentes
- Gestión operativa de brigadas municipales
- KPIs y métricas del sistema

---

## 📄 Archivos

### `openapi.yaml`

Especificación completa de la API REST siguiendo el estándar OpenAPI 3.0.3.

**Incluye:**
- Definición de todos los endpoints
- Schemas de datos (modelos)
- Códigos de respuesta HTTP
- Ejemplos de requests/responses
- Seguridad (JWT Bearer)
- Documentación inline

---

## 🔌 Endpoints Principales

### 🔐 Autenticación (`/auth`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/auth/login` | Iniciar sesión (ciudadano, brigada, admin) |
| POST | `/auth/refresh` | Renovar token de acceso |
| POST | `/auth/logout` | Cerrar sesión |

**Roles soportados:**
- `ciudadano` - Usuarios que reportan daños
- `brigada` - Personal de brigadas municipales
- `administrador` - Gestión completa del sistema
- `supervisor` - Supervisión y validación

---

### 📝 Reportes (`/reportes`)

Gestión de reportes ciudadanos con foto y geolocalización.

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/reportes` | Listar reportes con filtros (estado, tipo, fechas) |
| POST | `/reportes` | Crear reporte (multipart: imagen + GPS) |
| GET | `/reportes/{id}` | Obtener detalles de un reporte |
| PATCH | `/reportes/{id}` | Actualizar estado (validado, rechazado, duplicado) |

**Estados de reporte:**
- `pendiente` - Recién creado, esperando procesamiento
- `procesando` - En análisis por modelo ML
- `validado` - Aprobado, convertido a incidente
- `rechazado` - Descartado (calidad, fuera de alcance)
- `duplicado` - Detectado como duplicado de otro reporte

**Tipos de daño:**
- `bache` - Baches en asfalto
- `grieta` - Grietas longitudinales/transversales
- `hundimiento` - Hundimientos o depresiones

---

### 🚨 Incidentes (`/incidentes`)

Gestión de incidentes validados con priorización y asignación operativa.

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/incidentes` | Listar incidentes con filtros y ordenamiento |
| GET | `/incidentes/{id}` | Detalles completos del incidente |
| PATCH | `/incidentes/{id}` | Actualizar estado operativo |
| POST | `/incidentes/{id}/asignar` | Asignar a brigada específica |

**Estados operativos:**
- `pendiente` - Sin asignar
- `asignado` - Asignado a brigada
- `en_proceso` - Brigada trabajando en él
- `resuelto` - Reparación completada
- `cerrado` - Verificado y cerrado

**Niveles de prioridad:**
- `critica` - Atención inmediata (< 24h)
- `alta` - Urgente (24-48h)
- `media` - Programable (3-7 días)
- `baja` - Mantenimiento rutinario (> 7 días)

---

### 👷 Brigadas (`/brigadas`)

Gestión de brigadas municipales de reparación.

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/brigadas` | Listar brigadas (filtro por estado) |
| POST | `/brigadas` | Crear nueva brigada |
| GET | `/brigadas/{id}` | Detalles de brigada |
| PATCH | `/brigadas/{id}` | Actualizar estado/capacidad |
| GET | `/brigadas/{id}/incidentes` | Incidentes asignados a la brigada |

**Tipos de brigada:**
- `baches` - Especializada en reparación de baches
- `señalizacion` - Señalización vial
- `drenaje` - Sistemas de drenaje
- `mixta` - Multipropósito

**Estados:**
- `disponible` - Lista para asignaciones
- `ocupada` - Con carga de trabajo activa
- `inactiva` - Fuera de servicio

---

### ⚡ Priorización (`/prioridad`)

Cálculo inteligente de prioridad multicriterio.

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/prioridad/calcular` | Calcular prioridad de incidente |
| GET | `/prioridad/ranking` | Ranking completo ordenado por prioridad |

**Factores de priorización:**

1. **Severidad** (40%)
   - Área/longitud del daño detectado
   - Basado en segmentación YOLOv8

2. **Riesgo** (30%)
   - Proximidad a POIs críticos (hospitales, escuelas, estaciones)
   - Análisis geoespacial con buffer

3. **Antigüedad** (20%)
   - Días desde el primer reporte
   - Penaliza incidentes antiguos

4. **Densidad** (10%)
   - Concentración de reportes en la zona
   - DBSCAN clustering

**Score final:** Valor entre 0-1 que determina el nivel de prioridad.

---

### 📊 Métricas (`/metrics`)

KPIs y estadísticas del sistema.

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/metrics/dashboard` | KPIs generales (periodo configurable) |
| GET | `/metrics/modelo` | Métricas de rendimiento ML |
| GET | `/metrics/geograficos` | Distribución geográfica de incidentes |

**KPIs del dashboard:**
- Reportes totales y tasa de crecimiento
- Incidentes activos vs. resueltos
- Tasa de deduplicación
- Tiempo de respuesta promedio (TTR)
- Brigadas activas
- Cumplimiento de SLA

**Métricas ML:**
- **Clasificación:** F1-score, precisión, recall, accuracy por clase
- **Deduplicación:** Tasa de detección, falsos positivos
- **Inferencia:** Tiempo promedio, throughput (img/s)

---

## 🔒 Seguridad

### Autenticación JWT

Todos los endpoints (excepto `/auth/login`) requieren autenticación mediante **JWT Bearer Token**.

**Headers requeridos:**
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Flujo de autenticación:**

1. **Login:** `POST /auth/login` → retorna `access_token` y `refresh_token`
2. **Uso:** Incluir `access_token` en header `Authorization`
3. **Renovación:** Cuando expire, usar `POST /auth/refresh` con `refresh_token`
4. **Logout:** `POST /auth/logout` para invalidar tokens

**Expiración:**
- Access token: 1 hora
- Refresh token: 7 días

---

## 📦 Modelos de Datos

### Usuario
```json
{
  "id": "uuid",
  "email": "string",
  "nombre": "string",
  "rol": "ciudadano|brigada|administrador|supervisor",
  "activo": true
}
```

### Reporte
```json
{
  "id": "uuid",
  "usuario_id": "uuid",
  "imagen_url": "https://...",
  "imagen_procesada_url": "https://...",
  "latitud": 13.692940,
  "longitud": -89.218191,
  "direccion": "Calle Principal, Col. Escalón",
  "descripcion": "Bache grande...",
  "tipo_dano": "bache|grieta|hundimiento",
  "confianza_clasificacion": 0.95,
  "severidad": 0.78,
  "estado": "pendiente|procesando|validado|rechazado|duplicado",
  "es_duplicado": false,
  "duplicado_de": "uuid|null",
  "created_at": "2026-01-13T10:30:00Z",
  "updated_at": "2026-01-13T10:45:00Z"
}
```

### Incidente
```json
{
  "id": "uuid",
  "reporte_id": "uuid",
  "tipo_dano": "bache|grieta|hundimiento",
  "severidad": 0.78,
  "prioridad": "critica|alta|media|baja",
  "prioridad_score": 0.85,
  "latitud": 13.692940,
  "longitud": -89.218191,
  "direccion": "string",
  "estado_operativo": "pendiente|asignado|en_proceso|resuelto|cerrado",
  "brigada_id": "uuid|null",
  "brigada": { /* objeto Brigada */ },
  "fecha_asignacion": "datetime|null",
  "fecha_resolucion": "datetime|null",
  "tiempo_resolucion_horas": 48.5,
  "notas_resolucion": "string|null",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Brigada
```json
{
  "id": "uuid",
  "nombre": "Brigada Norte 1",
  "tipo": "baches|señalizacion|drenaje|mixta",
  "estado": "disponible|ocupada|inactiva",
  "capacidad_diaria": 10,
  "incidentes_asignados": 3,
  "zona_asignada": "Zona Norte",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

## 🚦 Códigos de Respuesta HTTP

| Código | Descripción | Cuándo se usa |
|--------|-------------|---------------|
| 200 | OK | Operación exitosa (GET, PATCH) |
| 201 | Created | Recurso creado (POST) |
| 204 | No Content | Operación exitosa sin retorno (DELETE, logout) |
| 400 | Bad Request | Solicitud malformada |
| 401 | Unauthorized | Token inválido o ausente |
| 404 | Not Found | Recurso no existe |
| 422 | Unprocessable Entity | Validación fallida |
| 500 | Internal Server Error | Error del servidor |

---

## 🛠️ Uso de la Especificación

### 1. Visualización Interactiva

**Swagger UI:**
```bash
# Abrir en navegador
https://editor.swagger.io/

# Cargar el archivo openapi.yaml
```

**Alternativa local con Docker:**
```bash
docker run -p 8080:8080 \
  -e SWAGGER_JSON=/api/openapi.yaml \
  -v $(pwd)/openapi.yaml:/api/openapi.yaml \
  swaggerapi/swagger-ui
```

Acceder en: http://localhost:8080

---

### 2. Generación de Cliente

**JavaScript/TypeScript:**
```bash
npm install @openapitools/openapi-generator-cli -g
openapi-generator-cli generate \
  -i openapi.yaml \
  -g typescript-axios \
  -o ./generated-client
```

**Python:**
```bash
pip install openapi-generator-cli
openapi-generator generate \
  -i openapi.yaml \
  -g python \
  -o ./generated-client
```

**Dart/Flutter:**
```bash
openapi-generator generate \
  -i openapi.yaml \
  -g dart-dio \
  -o ./lib/api
```

---

### 3. Validación

**Validar sintaxis:**
```bash
# Usar swagger-cli
npm install -g @apidevtools/swagger-cli
swagger-cli validate openapi.yaml
```

**Validar con Docker:**
```bash
docker run --rm -v $(pwd):/spec redocly/openapi-cli lint /spec/openapi.yaml
```

---

### 4. Generación de Documentación

**ReDoc (HTML estático):**
```bash
npx @redocly/cli build-docs openapi.yaml -o docs.html
```

**Acceder:**
```bash
open docs.html
```

---

## 📚 Ejemplos de Uso

### Crear Reporte con cURL

```bash
# 1. Login
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"usuario@example.com","password":"pass123"}' \
  | jq -r '.access_token')

# 2. Crear reporte
curl -X POST http://localhost:8000/api/v1/reportes \
  -H "Authorization: Bearer $TOKEN" \
  -F "imagen=@./bache.jpg" \
  -F "latitud=13.692940" \
  -F "longitud=-89.218191" \
  -F "descripcion=Bache grande en entrada de colonia"
```

---

### Listar Incidentes Prioritarios

```bash
curl -X GET "http://localhost:8000/api/v1/incidentes?prioridad=critica&estado_operativo=pendiente&orden=prioridad_desc" \
  -H "Authorization: Bearer $TOKEN"
```

---

### Asignar Incidente a Brigada

```bash
curl -X POST http://localhost:8000/api/v1/incidentes/123e4567-e89b-12d3-a456-426614174000/asignar \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "brigada_id": "987e6543-e21b-98c7-d654-426614174999",
    "notas": "Asignado por alta prioridad"
  }'
```

---

### Obtener KPIs del Dashboard

```bash
curl -X GET "http://localhost:8000/api/v1/metrics/dashboard?periodo=mes" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🔄 Versionado

La API sigue versionado semántico en la URL:

- **v1:** `/api/v1/*` - Versión actual (estable)
- **v2:** `/api/v2/*` - Próxima versión mayor (breaking changes)

**Política de deprecación:**
- Aviso con 3 meses de anticipación
- Soporte de versión anterior durante 6 meses
- Documentación de migración publicada

---

## 🧪 Testing

### Postman Collection

Importar `openapi.yaml` directamente en Postman:

1. Abrir Postman
2. Import → Upload Files → `openapi.yaml`
3. Generar colección automáticamente

### Thunder Client (VS Code)

1. Instalar extensión Thunder Client
2. Import → OpenAPI
3. Seleccionar `openapi.yaml`

---

## 📈 Roadmap

- [ ] **v1.1:** Endpoints de notificaciones push
- [ ] **v1.2:** Webhooks para eventos
- [ ] **v1.3:** Streaming de métricas en tiempo real (WebSockets)
- [ ] **v2.0:** GraphQL como alternativa
- [ ] **v2.1:** Soporte para batch operations

---

## 🤝 Contribución

Al modificar la API:

1. Actualizar `openapi.yaml`
2. Validar con `swagger-cli validate`
3. Regenerar clientes si aplica
4. Actualizar tests de integración
5. Documentar breaking changes en CHANGELOG

**Convención de commits:**
```
feat: agregar endpoint de estadísticas por zona
fix: corregir validación en POST /reportes
docs: actualizar ejemplos de autenticación
```

---

## 📞 Soporte

- **Documentación completa:** Ver `openapi.yaml`
- **Issues:** GitHub Issues del monorepo
- **Email técnico:** dev@sirccd.gob.sv

---

## 📄 Licencia

MIT License - Ver archivo LICENSE en la raíz del proyecto.
