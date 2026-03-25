# Historias de Usuario - SIRCCD

## 📖 Formato Estándar

**Historia:**  
Como [rol], quiero [acción], para [beneficio].

**Criterios de Aceptación (Given-When-Then):**
- **Given** (contexto/precondición)
- **When** (acción/evento)
- **Then** (resultado esperado)

---

## 👤 1. Citizen (Ciudadano)

### US-CIT-01 — Crear reporte con evidencia

**Historia:**  
Como Ciudadano, quiero crear un reporte con foto y descripción, para informar un daño vial de forma clara y verificable.

**Prioridad:** Alta  
**Estimación:** 5 puntos

**Criterios de Aceptación:**

- **Given** que estoy en el formulario de reporte,  
  **When** adjunto al menos 1 foto y escribo una descripción mínima,  
  **Then** el sistema permite enviar el reporte.

- **Given** que falta la foto,  
  **When** intento enviar,  
  **Then** el sistema me indica el campo faltante y no envía.

- **Given** que envié el reporte,  
  **When** finaliza el envío,  
  **Then** recibo un número/ID de seguimiento.

---

### US-CIT-02 — Capturar ubicación automáticamente

**Historia:**  
Como Ciudadano, quiero que el sistema tome mi ubicación GPS, para ubicar el incidente con precisión.

**Prioridad:** Alta  
**Estimación:** 3 puntos

**Criterios de Aceptación:**

- **Given** que tengo GPS habilitado,  
  **When** abro el formulario,  
  **Then** se completa la ubicación automáticamente con precisión estimada.

- **Given** que el GPS tiene baja precisión,  
  **When** el sistema detecta baja señal,  
  **Then** me avisa y permite ajustar manualmente en el mapa.

---

### US-CIT-03 — Reportar sin GPS (modo manual)

**Historia:**  
Como Ciudadano, quiero reportar sin GPS, para poder enviar reportes aunque el GPS falle.

**Prioridad:** Media  
**Estimación:** 3 puntos

**Criterios de Aceptación:**

- **Given** que no concedí permisos de ubicación,  
  **When** abro el formulario,  
  **Then** puedo ingresar dirección aproximada o marcar un punto en el mapa.

- **Given** que no ingresé ubicación manual,  
  **When** intento enviar,  
  **Then** el sistema solicita un método de ubicación válido.

---

### US-CIT-04 — Reportar sin internet (borrador/cola)

**Historia:**  
Como Ciudadano, quiero guardar el reporte y enviarlo cuando vuelva el internet, para no perder la información.

**Prioridad:** Media  
**Estimación:** 5 puntos

**Criterios de Aceptación:**

- **Given** que no hay conexión,  
  **When** intento enviar,  
  **Then** el sistema ofrece guardar como borrador/pendiente.

- **Given** que hay conexión nuevamente,  
  **When** abro "pendientes",  
  **Then** puedo reintentar el envío y confirmar que se publicó.

---

### US-CIT-05 — Ver estado del reporte

**Historia:**  
Como Ciudadano, quiero ver el estado de mis reportes, para saber si ya se atendieron.

**Prioridad:** Alta  
**Estimación:** 3 puntos

**Criterios de Aceptación:**

- **Given** que tengo reportes creados,  
  **When** entro a "Mis reportes",  
  **Then** veo lista con estados (ej.: recibido, en revisión, asignado, en progreso, resuelto, cerrado).

- **Given** que abro un reporte,  
  **When** veo el detalle,  
  **Then** aparece historial de cambios con fecha.

---

### US-CIT-06 — Recibir notificaciones de cambios

**Historia:**  
Como Ciudadano, quiero recibir notificaciones cuando cambie el estado, para estar informado sin revisar manualmente.

**Prioridad:** Alta  
**Estimación:** 5 puntos

**Criterios de Aceptación:**

- **Given** que activé notificaciones,  
  **When** el estado cambia,  
  **Then** recibo una notificación con el nuevo estado.

- **Given** que desactivé notificaciones,  
  **When** el estado cambia,  
  **Then** no se envía notificación.

---

### US-CIT-07 — Editar reporte antes de ser asignado

**Historia:**  
Como Ciudadano, quiero editar la descripción o agregar fotos antes de la asignación, para corregir o complementar la evidencia.

**Prioridad:** Baja  
**Estimación:** 3 puntos

**Criterios de Aceptación:**

- **Given** que el reporte está "recibido/en revisión",  
  **When** edito campos permitidos,  
  **Then** los cambios se guardan y quedan registrados.

- **Given** que el reporte ya está "asignado/en progreso",  
  **When** intento editar,  
  **Then** el sistema bloquea la edición y sugiere "enviar comentario".

---

### US-CIT-08 — Evitar duplicados (sugerencia de reportes cercanos)

**Historia:**  
Como Ciudadano, quiero que el sistema me avise si ya existe un reporte similar cercano, para evitar duplicar reportes.

**Prioridad:** Media  
**Estimación:** 8 puntos

**Criterios de Aceptación:**

- **Given** que seleccioné una ubicación,  
  **When** hay reportes recientes cerca (< 100m),  
  **Then** el sistema muestra sugerencias antes de enviar.

- **Given** que vi sugerencias,  
  **When** confirmo "es un reporte nuevo",  
  **Then** el sistema permite continuar.

---

### US-CIT-09 — Confirmar resolución

**Historia:**  
Como Ciudadano, quiero confirmar si el problema fue resuelto, para mejorar la calidad del cierre del caso.

**Prioridad:** Media  
**Estimación:** 3 puntos

**Criterios de Aceptación:**

- **Given** que el reporte está marcado como "resuelto",  
  **When** recibo solicitud de confirmación,  
  **Then** puedo responder "sí/no".

- **Given** que respondo "no",  
  **When** envío el motivo,  
  **Then** el reporte se reabre o pasa a revisión (según reglas).

---

### US-CIT-10 — Ver mapa de reportes públicos

**Historia:**  
Como Ciudadano, quiero ver un mapa con reportes cercanos, para tomar rutas más seguras y conocer riesgos.

**Prioridad:** Baja  
**Estimación:** 5 puntos

**Criterios de Aceptación:**

- **Given** que existe un módulo de mapa,  
  **When** lo abro,  
  **Then** veo marcadores con información limitada (sin datos sensibles).

- **Given** que aplico filtros (categoría/estado),  
  **When** confirmo,  
  **Then** el mapa se actualiza acorde a los filtros.

---

## 🏢 2. Operator (Operador Municipal)

### US-OPE-01 — Ver cola de reportes entrantes

**Historia:**  
Como Operador Municipal, quiero ver una cola priorizada de reportes, para triage rápido y ordenado.

**Prioridad:** Alta  
**Estimación:** 5 puntos

**Criterios de Aceptación:**

- **Given** que ingreso al panel,  
  **When** abro "Entrantes",  
  **Then** veo reportes ordenados por score/prioridad y fecha.

- **Given** que cambio el criterio (fecha/score),  
  **When** aplico,  
  **Then** la lista se reordena correctamente.

---

### US-OPE-02 — Revisar y validar un reporte

**Historia:**  
Como Operador Municipal, quiero validar reportes (completitud/categoría/ubicación), para mejorar calidad antes de asignar.

**Prioridad:** Alta  
**Estimación:** 5 puntos

**Criterios de Aceptación:**

- **Given** un reporte nuevo,  
  **When** lo abro,  
  **Then** puedo ajustar categoría y confirmar ubicación.

- **Given** que faltan datos críticos,  
  **When** marco "Requiere info",  
  **Then** se envía solicitud al ciudadano y el reporte queda en espera.

---

### US-OPE-03 — Asignar reportes

**Historia:**
Como Operador Municipal, quiero asignar reportes, para asegurar atención oportuna.

**Prioridad:** Alta
**Estimación:** 5 puntos

**Criterios de Aceptación:**

- **Given** que seleccioné un reporte,
  **When** confirmo la asignación,
  **Then** el reporte cambia a "asignado".

---

### US-OPE-04 — Repriorizar manualmente con justificación

**Historia:**  
Como Operador Municipal, quiero ajustar la prioridad manualmente con motivo, para manejar emergencias o contexto local.

**Prioridad:** Media  
**Estimación:** 3 puntos

**Criterios de Aceptación:**

- **Given** que tengo permisos,  
  **When** modifico prioridad,  
  **Then** el sistema exige una justificación y la guarda en auditoría.

- **Given** que no tengo permisos,  
  **When** intento repriorizar,  
  **Then** el sistema bloquea la acción.

---

### US-OPE-05 — Fusionar reportes duplicados

**Historia:**  
Como Operador Municipal, quiero unificar reportes duplicados, para evitar trabajo repetido y métricas infladas.

**Prioridad:** Media  
**Estimación:** 8 puntos

**Criterios de Aceptación:**

- **Given** que el sistema sugiere duplicados,  
  **When** confirmo "fusionar",  
  **Then** se crea un reporte principal y los otros quedan vinculados.

- **Given** que fusioné,  
  **When** consulto el historial,  
  **Then** se muestra la trazabilidad (IDs relacionados).

---

### US-OPE-06 — Comunicación y notas internas

**Historia:**  
Como Operador Municipal, quiero agregar notas internas y comunicarme con el ciudadano, para coordinar acciones.

**Prioridad:** Media  
**Estimación:** 5 puntos

**Criterios de Aceptación:**

- **Given** que agrego una nota interna,  
  **When** la guardo,  
  **Then** solo perfiles autorizados pueden verla.

- **Given** que envío un mensaje al ciudadano,  
  **When** lo envío,  
  **Then** queda registro de la comunicación.

---

### US-OPE-07 — Cerrar caso administrativamente

**Historia:**  
Como Operador Municipal, quiero cerrar un caso por criterios administrativos, para finalizar reportes inválidos o fuera de jurisdicción.

**Prioridad:** Media  
**Estimación:** 3 puntos

**Criterios de Aceptación:**

- **Given** que el reporte es inválido,  
  **When** selecciono motivo de cierre,  
  **Then** el sistema registra el motivo y notifica al ciudadano (si aplica).

- **Given** que el reporte está fuera de jurisdicción,  
  **When** cierro,  
  **Then** se etiqueta como "fuera de alcance" y se conserva para métricas.

---

### US-OPE-08 — Ver métricas operativas

**Historia:**  
Como Operador Municipal, quiero ver métricas (tiempos, backlog, resueltos), para mejorar la gestión y justificar recursos.

**Prioridad:** Alta  
**Estimación:** 8 puntos

**Criterios de Aceptación:**

- **Given** que abro el dashboard,  
  **When** selecciono rango de fechas,  
  **Then** se recalculan KPIs (SLA, tiempo medio, volumen).

- **Given** que filtro por zona/categoría,  
  **When** aplico filtros,  
  **Then** las métricas reflejan ese subconjunto.

---

## 🔧 3. Admin (Administrador)

### US-ADM-01 — Gestionar roles y permisos (RBAC)

**Historia:**  
Como Administrador, quiero crear/editar roles y permisos, para controlar accesos de forma segura.

**Prioridad:** Alta  
**Estimación:** 8 puntos

**Criterios de Aceptación:**

- **Given** que estoy en "Seguridad",  
  **When** asigno permisos a un rol,  
  **Then** el rol solo puede ejecutar esas acciones.

- **Given** que quito un permiso crítico,  
  **When** guardo,  
  **Then** el cambio impacta inmediatamente (o según política) y queda en auditoría.

---

### US-ADM-02 — Configurar pesos del score de prioridad

**Historia:**  
Como Administrador, quiero configurar pesos del algoritmo de priorización, para ajustar el sistema a políticas municipales.

**Prioridad:** Media  
**Estimación:** 5 puntos

**Criterios de Aceptación:**

- **Given** que accedo a "Scoring",  
  **When** cambio pesos y guardo,  
  **Then** el sistema valida rangos y persiste la configuración.

- **Given** que actualicé pesos,  
  **When** se recalculan prioridades,  
  **Then** se registra versión/configuración aplicada.

---

### US-ADM-03 — Administrar catálogos del sistema

**Historia:**  
Como Administrador, quiero gestionar catálogos (categorías, estados, zonas), para mantener consistencia en datos.

**Prioridad:** Media  
**Estimación:** 5 puntos

**Criterios de Aceptación:**

- **Given** que agrego una categoría,  
  **When** la guardo,  
  **Then** aparece disponible en formularios y paneles.

- **Given** que intento borrar una categoría en uso,  
  **When** confirmo,  
  **Then** el sistema bloquea o solicita reasignación (según regla).

---

### US-ADM-04 — Auditoría y trazabilidad

**Historia:**  
Como Administrador, quiero consultar logs de auditoría, para investigar cambios y accesos sensibles.

**Prioridad:** Alta  
**Estimación:** 8 puntos

**Criterios de Aceptación:**

- **Given** un rango de fechas,  
  **When** filtro por usuario/acción,  
  **Then** veo eventos con fecha, actor y resultado.

- **Given** un evento,  
  **When** lo abro,  
  **Then** veo detalle del recurso afectado (sin exponer datos no permitidos).

---

### US-ADM-05 — Políticas de retención y privacidad

**Historia:**  
Como Administrador, quiero configurar retención/anonimización, para cumplir buenas prácticas y normativas.

**Prioridad:** Media  
**Estimación:** 8 puntos

**Criterios de Aceptación:**

- **Given** que defino una política de retención,  
  **When** la guardo,  
  **Then** queda activa y documentada con fecha de aplicación.

- **Given** que un dato debe anonimizarse,  
  **When** se cumple el umbral,  
  **Then** el sistema anonimiza según la regla definida.

---

### US-ADM-06 — Gestión de usuarios y bloqueo por abuso

**Historia:**  
Como Administrador, quiero bloquear usuarios/reportes abusivos, para proteger el sistema de spam o mal uso.

**Prioridad:** Media  
**Estimación:** 5 puntos

**Criterios de Aceptación:**

- **Given** que detecto abuso,  
  **When** bloqueo un usuario/dispositivo,  
  **Then** no puede crear reportes hasta desbloqueo.

- **Given** que bloqueo,  
  **When** confirmo,  
  **Then** se guarda el motivo y evidencia en auditoría.

---

## 📊 Resumen de Historias de Usuario

| Rol | Total US | Alta Prioridad | Media Prioridad | Baja Prioridad |
|-----|----------|----------------|-----------------|----------------|
| **Citizen** | 10 | 4 | 5 | 1 |
| **Operator** | 8 | 4 | 4 | 0 |
| **Admin** | 6 | 2 | 4 | 0 |
| **TOTAL** | **24** | **10** | **13** | **1** |

---

## 🎯 Estimación Total

**Story Points:** ~138 puntos
**Sprints estimados (20 pts/sprint):** ~7 sprints

---

## 🔗 Dependencias entre US

### Flujo Ciudadano Básico
```
US-CIT-01 (Crear reporte) 
  ↓
US-CIT-02 (Ubicación GPS)
  ↓
US-CIT-05 (Ver estado)
  ↓
US-CIT-06 (Notificaciones)
```

### Flujo Operador
```
US-OPE-01 (Ver cola)
  ↓
US-OPE-02 (Validar)
  ↓
US-OPE-03 (Asignar)
```

### Configuración Administrativa
```
US-ADM-01 (Roles/permisos)
  ↓
US-ADM-03 (Catálogos)
  ↓
US-ADM-02 (Pesos scoring)
```

---

## 📚 Referencias

- [API Specification](../../backend/api/openapi.yaml)
- [Arquitectura Lógica](./arquitectura_logica.md)
- [Modelo de Datos](./modelo_datos.md)

---

## 🤝 Contribución

Al agregar nuevas historias de usuario:

1. Seguir formato estándar: "Como [rol], quiero [acción], para [beneficio]"
2. Incluir criterios GWT completos
3. Asignar prioridad (Alta/Media/Baja)
4. Estimar en story points (Fibonacci: 1, 2, 3, 5, 8, 13)
5. Identificar dependencias
6. Actualizar tabla de resumen

**Convención de IDs:**
- `US-CIT-XX` - Ciudadano
- `US-OPE-XX` - Operador
- `US-ADM-XX` - Administrador

---

## 📄 Licencia

MIT License
