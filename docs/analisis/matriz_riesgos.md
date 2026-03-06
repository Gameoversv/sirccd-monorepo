# Proyecto SIRCCD – Sistema Inteligente Urbano para Reporte y Priorización de Daños Viales

## 📌 1. Riesgos Técnicos (IA, ML, Backend, Web, Móvil)

### R-01 — Baja calidad de imágenes

**Tipo:** Técnico  
**Probabilidad:** Alta  
**Impacto:** Alto  
**Severidad:** 🔴 Crítica

**Descripción:** Fotos borrosas, nocturnas, con lluvia o mala iluminación afectan la clasificación.

**Mitigación:**
- Validadores de calidad de imagen
- Data augmentation
- Filtros mínimos antes de subir

---

### R-02 — Falla en detección de duplicados

**Tipo:** Técnico  
**Probabilidad:** Media  
**Impacto:** Alto  
**Severidad:** 🔴 Alta

**Mitigación:**
- Ajustar umbrales de similitud
- Embeddings visuales más robustos
- DBSCAN + Haversine para clustering
- Pruebas de "near-duplicates"

---

### R-03 — Clasificación incorrecta de daños

**Tipo:** Técnico  
**Probabilidad:** Media  
**Impacto:** Alto  
**Severidad:** 🔴 Alta

**Mitigación:**
- Fine-tuning con datasets locales urbanos
- Métricas F1 por clase
- Validación manual en piloto

---

### R-04 — Latencia alta en la inferencia (TTR)

**Tipo:** Técnico  
**Probabilidad:** Media  
**Impacto:** Alto  
**Severidad:** 🔴 Alta

**Mitigación:**
- Optimizar modelo (ONNX/TFLite)
- Procesamiento batch pequeño
- Aceleración opcional (GPU/TPU)

---

### R-05 — Integración fallida entre web–backend–ML

**Tipo:** Técnico  
**Probabilidad:** Media  
**Impacto:** Alto  
**Severidad:** 🔴 Alta

**Mitigación:**
- Pruebas contractuales (OpenAPI)
- Mocks de servicios
- Versionado estable de APIs

---

## 📌 2. Riesgos de Seguridad y Privacidad

### R-06 — Imágenes sin difuminar (rostros/placas)

**Tipo:** Seguridad  
**Probabilidad:** Baja  
**Impacto:** Alto  
**Severidad:** 🔴 Alta

**Mitigación:**
- Prohibir almacenamiento de originales
- Pipelines obligatorios
- Pruebas automatizadas de privacidad

---

### R-07 — Accesos no autorizados (fallo RBAC)

**Tipo:** Seguridad  
**Probabilidad:** Baja  
**Impacto:** Alto  
**Severidad:** 🔴 Alta

**Mitigación:**
- Auditoría RBAC
- JWT con expiración y refresh tokens seguros
- Políticas de mínimo privilegio

---

### R-08 — Vulnerabilidades en despliegue

**Tipo:** Seguridad / Infra  
**Probabilidad:** Media  
**Impacto:** Medio  
**Severidad:** 🟠 Media

**Mitigación:**
- Hardening del backend
- Cabeceras CSP/HSTS/STS
- Pentest básico + remediación

---

## 📌 3. Riesgos Operacionales (Infraestructura, BD, Almacenamiento)

### R-09 — Caída del backend

**Tipo:** Operacional  
**Probabilidad:** Baja  
**Impacto:** Alto  
**Severidad:** 🔴 Alta

**Mitigación:**
- Healthchecks
- Auto-restart (Docker/PM2)
- Observabilidad (Prometheus + Grafana)

---

### R-10 — Pérdida/corrupción de datos

**Tipo:** Infraestructura  
**Probabilidad:** Baja  
**Impacto:** Alto  
**Severidad:** 🔴 Crítica

**Mitigación:**
- Backups automáticos
- Restore probado
- PostgreSQL WAL
- Redundancia

---

### R-11 — Carga excesiva de imágenes

**Tipo:** Operacional  
**Probabilidad:** Baja  
**Impacto:** Medio  
**Severidad:** 🟠 Media

**Mitigación:**
- Usar S3/MinIO
- TTL de imágenes
- Compresión automática

---

## 📌 4. Riesgos de Gestión del Proyecto

### R-12 — Retrasos en entregas

**Tipo:** Gestión  
**Probabilidad:** Media  
**Impacto:** Alto  
**Severidad:** 🔴 Alta

**Mitigación:**
- Priorizar MVP
- Desglosar tareas
- Revisiones semanales con tutor

---

### R-13 — Falta de datos locales etiquetados

**Tipo:** Gestión  
**Probabilidad:** Media  
**Impacto:** Medio  
**Severidad:** 🟠 Media

**Mitigación:**
- Plan de etiquetado temprano
- Semi-automatización de severidad
- Captura asistida con guías visuales

---

## 📌 5. Riesgos de Usuario y UX

### R-14 — Baja adopción del sistema

**Tipo:** Usuario  
**Probabilidad:** Baja–Media  
**Impacto:** Medio  
**Severidad:** 🟠 Media

**Mitigación:**
- Flujo de uso simple
- Onboarding guiado
- Comunicación con brigadas municipales

---

### R-15 — Problemas de compatibilidad web/móvil

**Tipo:** UX/UI  
**Probabilidad:** Media  
**Impacto:** Medio  
**Severidad:** 🟠 Media

**Mitigación:**
- Pruebas cross-browser
- Diseño responsive
- Test de accesibilidad

---

## 📌 6. Mapa de Severidad (Guía visual)

| Severidad | Color | Descripción |
|-----------|-------|-------------|
| Crítica | 🔴 Rojo | Riesgo que puede comprometer el proyecto o la seguridad |
| Alta | 🟠 Naranja | Afecta avance, precisión del modelo o funcionalidad clave |
| Media | 🟡 Amarillo | Riesgo manejable con mitigación |
| Baja | 🟢 Verde | Impacto mínimo |

---

## 📁 Ubicación en el monorepo

```
docs/
└── matriz_riesgos.md
```
