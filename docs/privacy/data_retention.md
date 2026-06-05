# Política de Datos y Retención — SIRCCD

**Versión:** 1.0  
**Fecha:** 2026-06-05  
**Clasificación:** Interna — operación del sistema

---

## 1. Alcance

Esta política aplica a todos los datos procesados por SIRCCD:

- Imágenes de reportes ciudadanos (originales y anonimizadas)
- Metadatos de reportes e incidentes (coordenadas, timestamps, descripciones)
- Datos de usuarios (ciudadanos, operadores, administradores)
- Embeddings vectoriales generados para deduplicación
- Logs de operación y auditoría
- Datos de exportación (CSV, GeoJSON)

**Marco normativo de referencia:**  
Ley 172-13 de la República Dominicana (protección de datos de carácter personal) y principios del RGPD/GDPR aplicados como buena práctica internacional.

---

## 2. Principios generales

| Principio | Aplicación en SIRCCD |
|-----------|----------------------|
| **Minimización** | Solo se capturan datos estrictamente necesarios para clasificar y gestionar el daño vial |
| **Limitación de finalidad** | Los datos solo se usan para gestión operativa de infraestructura vial. No se usan para perfilado ciudadano |
| **Exactitud** | Coordenadas GPS y timestamps se registran tal como los provee el dispositivo |
| **Limitación de conservación** | Cada categoría de dato tiene un TTL definido en esta política |
| **Integridad y confidencialidad** | Almacenamiento cifrado en tránsito (TLS), acceso por JWT con roles, MinIO con credenciales rotables |
| **Responsabilidad proactiva** | El sistema anonimiza imágenes automáticamente antes de que sean accesibles a operadores |

---

## 3. Categorías de datos y retención

### 3.1 Imágenes

#### Imagen original del ciudadano

| Atributo | Valor |
|----------|-------|
| Almacenamiento | MinIO (`sirccd-images` bucket) |
| Formato | JPEG/PNG original subido por el ciudadano |
| Contiene PII potencial | Sí — rostros y placas vehiculares visibles |
| **Política de retención** | **Eliminada automáticamente dentro de las 24 horas posteriores a la anonimización exitosa** |
| Qué dispara la eliminación | Confirmación de que la imagen anonimizada fue generada y almacenada correctamente |
| Acceso mientras existe | Solo sistema (worker RQ); ningún rol humano accede a la imagen original |

**Nota de implementación:** El servicio `anonymizer.py` debe invocar `storage.delete_object()` sobre la imagen original en MinIO una vez que la imagen anonimizada es persistida y verificada. Si la anonimización falla, la imagen original queda retenida hasta el siguiente ciclo de retry (máximo 72 horas) antes de eliminación forzada.

#### Imagen anonimizada (rostros y placas difuminados)

| Atributo | Valor |
|----------|-------|
| Almacenamiento | MinIO (`sirccd-images` bucket) |
| Contiene PII | No — rostros y placas fueron difuminados por el pipeline ML |
| **Retención activa** | Durante toda la vida del reporte/incidente activo |
| **Retención post-cierre** | 24 meses a partir de la fecha de resolución del incidente asociado |
| Eliminación | Automática al vencer el período post-cierre |
| Acceso | Ver sección 5 (control de acceso por rol) |

#### Imagen "después" de reparación (`after_image`)

| Atributo | Valor |
|----------|-------|
| Almacenamiento | MinIO (`sirccd-images` bucket) |
| Contiene PII | Potencial — aplicar mismo pipeline de anonimización antes de persistir |
| **Retención** | 36 meses desde la fecha de subida (evidencia de cierre de incidente) |
| Eliminación | Automática al vencer el período |

---

### 3.2 Metadatos de reportes

Los campos del modelo `Report` en PostgreSQL tienen la siguiente política:

| Campo | Contiene PII | Retención | Notas |
|-------|-------------|-----------|-------|
| `id` (UUID) | No | Vida del reporte + 24 meses | Clave de auditoría |
| `user_id` | Indirecto | Pseudonimizado al archivar | Ver sección 3.5 |
| `image_url` | No (URL de imagen anonimizada) | Vida del reporte + 24 meses | |
| `description` | Posible (texto libre) | Vida del reporte + 24 meses | No debe incluir datos personales; guía al ciudadano en UI |
| `lat` / `lng` | Sí — ubicación precisa | 36 meses desde creación | Tras retención, redondeado a 3 decimales y archivado |
| `status` | No | Permanente (histórico estadístico) | |
| `damage_type` / `severity` | No | Permanente | Dato operativo/estadístico |
| `embedding` (binario) | No directamente | 24 meses desde creación del reporte | Se elimina al reconstruir índice FAISS si el reporte es archivado |
| `created_at` / `updated_at` | No | Permanente | Auditoría temporal |

---

### 3.3 Metadatos de incidentes

| Campo | Retención | Notas |
|-------|-----------|-------|
| `id`, `title`, `description` | Permanente (archivo histórico estadístico) | Coordinadas redondeadas al archivar |
| `lat` / `lng` (precisas) | 36 meses; luego reducir precisión a 3 decimales | |
| `status`, `priority`, `damage_type` | Permanente | Dato operativo |
| `resolved_at` | Permanente | Indicador de cierre |
| `report_count` | Permanente | Estadístico |

---

### 3.4 Datos de usuarios

| Campo | Contiene PII | Retención activa | Post-baja |
|-------|-------------|------------------|-----------|
| `email` | Sí | Mientras cuenta activa | Eliminado a los 30 días de desactivación |
| `hashed_password` | Sí (derivado) | Mientras cuenta activa | Eliminado inmediatamente al desactivar |
| `full_name` | Sí | Mientras cuenta activa | Eliminado a los 30 días de desactivación |
| `role` | No | Mientras cuenta activa | Archivado anonimizado |
| `is_active` | No | Permanente | Archivado |
| `created_at` | No | Permanente | Archivado |

**Desactivación vs. eliminación:** El sistema implementa soft delete (`is_active = false`). La eliminación física de PII ocurre automáticamente a los 30 días de la desactivación, mediante una tarea de limpieza programada.

**Derecho de supresión:** Un ciudadano puede solicitar la eliminación de su cuenta y datos asociados. El administrador ejecuta `DELETE /api/users/{id}` (desactivación) y el proceso automático a los 30 días completa la purga de PII. Los reportes e incidentes creados quedan pseudonimizados (se rompe el vínculo `user_id`).

---

### 3.5 Pseudonimización al archivar

Cuando un reporte o su usuario asociado supera el período de retención con PII:

1. El campo `user_id` en `Report` se reemplaza por un UUID constante de sistema (`ARCHIVED_USER_ID`).
2. Los campos de coordenadas precisas se redondean a 3 decimales (~111 m de precisión).
3. El campo `description` se reemplaza por un marcador si contiene palabras clave de PII detectadas.
4. El embedding binario se elimina del registro.

Este proceso preserva la integridad estadística (conteos, tipos de daño, zonas) sin retener datos identificables.

---

### 3.6 Índice FAISS y embeddings

| Dato | Retención | Notas |
|------|-----------|-------|
| Índice FAISS (`faiss_index.bin`) | Regenerado bajo demanda; no tiene TTL propio | |
| Embeddings en BD (`Report.embedding`) | Eliminados al archivar el reporte (ver 3.2) | |
| Vectores en índice FAISS | Eliminados al reconstruir el índice (`/api/deduplication/index/rebuild`) | El rebuild post-archivado purga vectores de reportes archivados |

**Práctica recomendada:** Ejecutar rebuild del índice FAISS mensualmente para purgar vectores de reportes ya archivados o eliminados.

---

### 3.7 Logs de operación y auditoría

| Tipo | Retención | Almacenamiento |
|------|-----------|----------------|
| Logs de acceso a API (Prometheus/Loki) | 90 días | Infraestructura de monitoreo |
| Logs de autenticación (login/logout) | 12 meses | BD o log estructurado |
| Logs de acciones administrativas (cambios de rol, eliminaciones) | 36 meses | Inmutable, append-only |
| Health checks | 30 días | Prometheus |

Los logs de autenticación y acciones administrativas son inmutables: no pueden ser modificados ni eliminados por ningún rol, incluyendo `admin`. Solo el equipo de infraestructura puede rotar estos logs al vencer su TTL.

---

## 4. Ciclo de vida completo de una imagen

```
Ciudadano sube imagen
        |
        v
Worker RQ recibe job
        |
        v
Anonymizer detecta rostros/placas → aplica blur
        |
        v
Imagen anonimizada → persistida en MinIO
        |
        v
¿Anonimización exitosa?
  Si → Imagen original eliminada de MinIO (≤ 24h)
  No → Retry hasta 72h → eliminación forzada
        |
        v
Imagen anonimizada accesible a operadores (rol ≥ operator)
        |
        v
Incidente resuelto
        |
        v
Contador retención iniciado (24 meses)
        |
        v
Vencimiento → Imagen anonimizada eliminada de MinIO
              Metadatos pseudonimizados en BD
```

---

## 5. Control de acceso por rol

### 5.1 Acceso a imágenes

| Tipo de imagen | `citizen` | `operator` | `admin` |
|---------------|-----------|-----------|---------|
| Imagen original | — (nunca accesible) | — | — |
| Imagen anonimizada propia | Solo la suya | Todas | Todas |
| Imagen anonimizada de otros ciudadanos | No | Sí | Sí |
| Imagen "después" de reparación | No | Sí | Sí |

### 5.2 Acceso a metadatos

| Dato | `citizen` | `operator` | `admin` |
|------|-----------|-----------|---------|
| Coordenadas GPS precisas | Solo las propias | Todas | Todas |
| Descripción del reporte | Solo la propia | Todas | Todas |
| `user_id` de otros reportes | No | Solo ID (no nombre) | Sí |
| Datos de usuarios (`/api/users`) | No | No | Sí |
| Exportación CSV/GeoJSON | No | Sí | Sí |
| Logs de auditoría | No | No | Solo lectura |

### 5.3 Operaciones de eliminación

| Acción | `citizen` | `operator` | `admin` |
|--------|-----------|-----------|---------|
| Eliminar reporte propio | No (soft) | No | Sí |
| Desactivar usuario | No | No | Sí |
| Purga manual de imágenes archivadas | No | No | No (automatizado) |
| Rebuild índice FAISS | No | No | Sí |

---

## 6. Transferencia y exportación de datos

### 6.1 Exportaciones CSV/GeoJSON

- Solo accesibles para `operator` y `admin`.
- Los archivos exportados **no incluyen** `user_id`, `email`, ni `full_name` del ciudadano reportante.
- Las coordenadas en exportaciones se incluyen a precisión completa para uso operativo.
- Los archivos exportados no deben almacenarse fuera del entorno controlado del sistema sin cifrado.

### 6.2 Transferencia a terceros

- Ningún dato con PII puede ser transferido a terceros sin anonimización previa.
- Los datasets de entrenamiento ML exportados desde `sirccd-images` deben pasar por el pipeline de anonimización antes de salir del entorno.
- Cualquier integración futura (ej. mobile app) debe autenticarse via JWT y recibe solo datos conforme a su rol.

---

## 7. Seguridad del almacenamiento

| Componente | Medida |
|-----------|--------|
| MinIO | Credenciales de acceso en variables de entorno, nunca en código. Rotación semestral de `MINIO_SECRET_KEY`. Buckets privados (no public-read). |
| PostgreSQL | Acceso exclusivo por aplicación (no expuesto a red pública). Contraseña en `.env`. |
| Redis | Sin autenticación en dev; autenticación habilitada en producción. |
| URLs de imágenes | Pre-signed URLs con expiración de 1 hora para acceso temporal controlado. |
| Tránsito | TLS obligatorio en producción para todos los endpoints. |

---

## 8. Responsabilidades

| Rol | Responsabilidad |
|-----|----------------|
| **Administrador del sistema** | Verificar que los procesos automáticos de purga se ejecuten; auditar logs; gestionar solicitudes de supresión |
| **Operador** | No descargar ni replicar datos fuera del sistema; reportar incidentes de acceso no autorizado |
| **Ciudadano** | Proporcionar solo imágenes del daño vial; no incluir PII en descripción del reporte |
| **Equipo de desarrollo** | Mantener los TTLs implementados consistentes con esta política; ejecutar rebuild FAISS mensual |

---

## 9. Solicitudes de derechos del titular

Un ciudadano puede ejercer los siguientes derechos contactando al administrador del sistema:

| Derecho | Plazo de respuesta | Mecanismo |
|---------|-------------------|-----------|
| **Acceso** — ver qué datos están almacenados | 15 días hábiles | Endpoint `/api/auth/me` + listado de reportes propios |
| **Rectificación** — corregir datos inexactos | 15 días hábiles | `PATCH /api/users/{id}` por admin |
| **Supresión** — eliminar cuenta y datos | 30 días | `DELETE /api/users/{id}` + purga automática PII a los 30 días |
| **Portabilidad** — exportar datos propios | 15 días hábiles | Exportación CSV de reportes propios |
| **Oposición al tratamiento** | Evaluación caso por caso | Contacto con administrador |

---

## 10. Revisión de esta política

Esta política se revisa:

- **Anualmente** en la fecha de publicación.
- **Ante cambios arquitecturales** que modifiquen almacenamiento de datos (nuevos buckets, nuevos campos con PII, integraciones externas).
- **Ante incidentes de seguridad** que expongan datos personales.

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | 2026-06-05 | Versión inicial |
