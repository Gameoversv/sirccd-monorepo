# R-10: Diseño de Wireframes (Web, Móvil y Panel Municipal)

**Fecha:** 2026-01-14  
**Versión:** 1.0  
**Estado:** Completo

## Objetivo

Diseñar wireframes de baja y media fidelidad para las tres interfaces principales del sistema SIRCCD:
1. **App Ciudadano** (móvil iOS/Android + web responsive)
2. **Dashboard Municipal** (web)

---

## 1. Visión general del diseño

### 1.1 Principios de diseño

| Principio | Aplicación |
|-----------|------------|
| **Mobile-first** | Diseñar primero para móvil, escalar a desktop |
| **Simplicidad** | Máximo 3 pasos para completar acción principal |
| **Accesibilidad** | WCAG 2.1 AA, contraste 4.5:1, tamaños táctiles ≥44px |
| **Offline-first** | Permitir uso sin conexión (caché, sync posterior) |
| **Feedback visual** | Mostrar estado de carga, confirmaciones, errores |
| **Progresión clara** | Breadcrumbs, stepper, indicadores de progreso |

---

### 1.2 Paleta de colores del sistema

```css
/* Colores principales */
--primary: #2563eb;        /* Azul - acciones principales */
--primary-dark: #1e40af;   /* Azul oscuro - hover */
--primary-light: #dbeafe; /* Azul claro - backgrounds */

/* Colores de estado */
--success: #16a34a;        /* Verde - éxito */
--warning: #ea580c;        /* Naranja - advertencia */
--danger: #dc2626;         /* Rojo - error/crítico */
--info: #0891b2;           /* Cyan - información */

/* Prioridades de reportes */
--priority-critical: #dc2626;  /* Rojo */
--priority-high: #ea580c;      /* Naranja */
--priority-medium: #eab308;    /* Amarillo */
--priority-low: #16a34a;       /* Verde */
--priority-minimal: #06b6d4;   /* Cyan */

/* Neutrales */
--gray-50: #f9fafb;
--gray-100: #f3f4f6;
--gray-200: #e5e7eb;
--gray-300: #d1d5db;
--gray-400: #9ca3af;
--gray-500: #6b7280;
--gray-600: #4b5563;
--gray-700: #374151;
--gray-800: #1f2937;
--gray-900: #111827;

/* Tipografía */
--font-heading: 'Inter', sans-serif;
--font-body: 'Inter', sans-serif;
--font-mono: 'JetBrains Mono', monospace;
```

---

### 1.3 Iconografía

**Librería recomendada:** [Lucide Icons](https://lucide.dev/) (open source, consistente)

| Categoría | Iconos clave |
|-----------|--------------|
| **Navegación** | Home, Map, List, Settings, User, Menu |
| **Acciones** | Plus, Camera, Upload, Send, Save, Edit, Delete |
| **Estados** | Check, X, AlertTriangle, Info, Clock, MapPin |
| **Reportes** | Navigation (ubicación), Image, FileText, MessageSquare |
---

## 2. App Ciudadano (Móvil + Web)

### 2.1 Flujo principal

```
[Onboarding] → [Home] → [Crear Reporte] → [Confirmación] → [Seguimiento]
              ↓
          [Mis Reportes] → [Detalle] → [Agregar Evidencia/Comentario]
```

---

### 2.2 Wireframe 1: Splash & Onboarding

**Pantalla:** Splash Screen

```
┌─────────────────────────────────────┐
│                                     │
│                                     │
│          [LOGO MUNICIPIO]           │
│                                     │
│            SIRCCD                   │
│    Sistema Inteligente de Reportes │
│                                     │
│         [Loading spinner]           │
│                                     │
│                                     │
└─────────────────────────────────────┘
```

**Pantalla:** Onboarding (3 slides - swipeable)

```
┌─────────────────────────────────────┐
│ [Skip]                              │
│                                     │
│     [Ilustración: persona con       │
│      smartphone fotografiando       │
│      bache]                         │
│                                     │
│   Reporta daños viales en segundos │
│                                     │
│   Toma foto, confirma ubicación     │
│   y envía. Nosotros hacemos el      │
│   resto.                            │
│                                     │
│   ●  ○  ○           [Siguiente →]  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ [Skip]                              │
│                                     │
│     [Ilustración: equipo            │
│      reparando calle]               │
│                                     │
│   Seguimiento en tiempo real        │
│                                     │
│   Recibe notificaciones cuando tu   │
│   reporte sea validado, asignado    │
│   y resuelto.                       │
│                                     │
│   ○  ●  ○           [Siguiente →]  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│                                     │
│     [Ilustración: mapa con          │
│      pins de reportes]              │
│                                     │
│   Contribuye a tu comunidad         │
│                                     │
│   Tu reporte ayuda a priorizar y    │
│   mejorar la infraestructura de     │
│   tu ciudad.                        │
│                                     │
│   ○  ○  ●           [Comenzar]     │
└─────────────────────────────────────┘
```

---

### 2.3 Wireframe 2: Autenticación

**Pantalla:** Login / Registro

```
┌─────────────────────────────────────┐
│ [← Volver]                          │
│                                     │
│        [LOGO MUNICIPIO]             │
│                                     │
│   Inicia sesión o crea una cuenta  │
│                                     │
│   ┌─────────────────────────────┐  │
│   │ 📧 Correo electrónico       │  │
│   └─────────────────────────────┘  │
│                                     │
│   ┌─────────────────────────────┐  │
│   │ 🔒 Contraseña               │  │
│   └─────────────────────────────┘  │
│                                     │
│   ¿Olvidaste tu contraseña?         │
│                                     │
│   ┌─────────────────────────────┐  │
│   │     [Iniciar sesión]        │  │
│   └─────────────────────────────┘  │
│                                     │
│   ───────── o ─────────             │
│                                     │
│   ┌─────────────────────────────┐  │
│   │  [G] Continuar con Google   │  │
│   └─────────────────────────────┘  │
│                                     │
│   ¿No tienes cuenta? Regístrate     │
│                                     │
└─────────────────────────────────────┘
```

**Nota:** Registro opcional - se puede reportar anónimamente, pero con cuenta se tiene seguimiento.

---

### 2.4 Wireframe 3: Home (Dashboard ciudadano)

```
┌─────────────────────────────────────┐
│ [☰ Menu]    SIRCCD    [🔔 2]       │
├─────────────────────────────────────┤
│                                     │
│  Hola, Juan 👋                      │
│  ¿Detectaste algún daño vial hoy?  │
│                                     │
│  ┌───────────────────────────────┐ │
│  │                               │ │
│  │    [+] REPORTAR DAÑO          │ │
│  │                               │ │
│  │    [📷 Camera icon]           │ │
│  │                               │ │
│  └───────────────────────────────┘ │
│                                     │
│  Mis reportes activos               │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 🔴 Bache en Av. Juárez      │   │
│  │ En progreso • Hace 2 días   │   │
│  │ [Ver detalles →]            │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 🟡 Señal caída              │   │
│  │ Validado • Hace 5 días      │   │
│  │ [Ver detalles →]            │   │
│  └─────────────────────────────┘   │
│                                     │
│  [Ver todos mis reportes]           │
│                                     │
│  ┌───────────────────────────────┐ │
│  │ 📊 Estadísticas del mes       │ │
│  │ 3 reportes • 1 resuelto       │ │
│  └───────────────────────────────┘ │
│                                     │
└─────────────────────────────────────┘
│ [🏠 Home] [📍 Mapa] [📋 Reportes]  │
└─────────────────────────────────────┘
```

**Componentes:**
- Header con menú hamburguesa, título, notificaciones
- Botón CTA principal (Reportar daño) - destacado
- Lista de reportes activos (últimos 3)
- Card de estadísticas
- Bottom navigation bar

---

### 2.5 Wireframe 4: Crear Reporte - Paso 1 (Foto)

```
┌─────────────────────────────────────┐
│ [← Cancelar]  Nuevo reporte  [?]   │
├─────────────────────────────────────┤
│                                     │
│  Paso 1 de 4                        │
│  ▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░         │
│                                     │
│  Toma una foto del daño             │
│                                     │
│  ┌───────────────────────────────┐ │
│  │                               │ │
│  │                               │ │
│  │       [Vista de cámara]       │ │
│  │         o                     │ │
│  │   [Imagen capturada preview]  │ │
│  │                               │ │
│  │                               │ │
│  │                               │ │
│  └───────────────────────────────┘ │
│                                     │
│  Consejos:                          │
│  • Enfoca el daño claramente        │
│  • Incluye referencia (calle, poste)│
│  • Evita incluir personas o placas  │
│                                     │
│  ┌─────────────────────────────┐   │
│  │    [📷 Tomar foto]          │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │    [🖼️ Desde galería]       │   │
│  └─────────────────────────────┘   │
│                                     │
│                [Siguiente →]        │
│                                     │
└─────────────────────────────────────┘
```

**Funcionalidades:**
- Botón para abrir cámara nativa
- Opción de seleccionar desde galería
- Preview de imagen capturada
- Botón "Siguiente" solo activo si hay imagen

---

### 2.6 Wireframe 5: Crear Reporte - Paso 2 (Ubicación)

```
┌─────────────────────────────────────┐
│ [← Atrás]     Nuevo reporte         │
├─────────────────────────────────────┤
│                                     │
│  Paso 2 de 4                        │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░         │
│                                     │
│  Confirma la ubicación              │
│                                     │
│  ┌───────────────────────────────┐ │
│  │                               │ │
│  │    [Mapa interactivo]         │ │
│  │                               │ │
│  │         📍 <- Pin             │ │
│  │      (arrastrable)            │ │
│  │                               │ │
│  │  [My Location] [Zoom +/-]    │ │
│  │                               │ │
│  └───────────────────────────────┘ │
│                                     │
│  📍 Ubicación detectada:            │
│  ┌─────────────────────────────┐   │
│  │ Av. Juárez #123, Centro     │   │
│  │ [✏️ Editar dirección]       │   │
│  └─────────────────────────────┘   │
│                                     │
│  ℹ️ Arrastra el pin para ajustar    │
│                                     │
│  ☑️ Usar mi ubicación actual        │
│                                     │
│                [Siguiente →]        │
│                                     │
└─────────────────────────────────────┘
```

**Funcionalidades:**
- Mapa con pin arrastrable
- Autodetección de ubicación GPS
- Geocodificación inversa (coords → dirección)
- Checkbox para forzar ubicación actual
- Búsqueda de dirección (opcional)

---

### 2.7 Wireframe 6: Crear Reporte - Paso 3 (Categoría y Descripción)

```
┌─────────────────────────────────────┐
│ [← Atrás]     Nuevo reporte         │
├─────────────────────────────────────┤
│                                     │
│  Paso 3 de 4                        │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░         │
│                                     │
│  Describe el problema               │
│                                     │
│  Categoría *                        │
│  ┌─────────────────────────────┐   │
│  │ Seleccionar... ▼            │   │
│  └─────────────────────────────┘   │
│  (Opciones: Bache, Socavón,         │
│   Alcantarilla, Señalización,       │
│   Alumbrado, Banqueta, Otro)        │
│                                     │
│  Severidad estimada                 │
│  ┌───┬───┬───┬───┬───┐             │
│  │ ● │ ○ │ ○ │ ○ │ ○ │             │
│  └───┴───┴───┴───┴───┘             │
│  Leve          Crítico              │
│                                     │
│  Descripción *                      │
│  ┌─────────────────────────────┐   │
│  │ Bache grande que afecta     │   │
│  │ ambos carriles...           │   │
│  │                             │   │
│  │                    (120/500)│   │
│  └─────────────────────────────┘   │
│                                     │
│  ℹ️ Sé específico: tamaño, impacto, │
│     referencia visual                │
│                                     │
│                [Siguiente →]        │
│                                     │
└─────────────────────────────────────┘
```

**Componentes:**
- Dropdown de categorías
- Selector de severidad (1-5 estrellas/círculos)
- Textarea con contador de caracteres
- Validación: categoría y descripción obligatorias

---

### 2.8 Wireframe 7: Crear Reporte - Paso 4 (Confirmación)

```
┌─────────────────────────────────────┐
│ [← Atrás]     Nuevo reporte         │
├─────────────────────────────────────┤
│                                     │
│  Paso 4 de 4                        │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │
│                                     │
│  Confirma tu reporte                │
│                                     │
│  ┌───────────────────────────────┐ │
│  │ [Imagen capturada - thumbnail]│ │
│  └───────────────────────────────┘ │
│                                     │
│  📍 Ubicación                       │
│  Av. Juárez #123, Centro            │
│  [Ver en mapa]                      │
│                                     │
│  🏷️ Categoría                       │
│  Bache grande                       │
│                                     │
│  ⭐ Severidad                       │
│  ●●●○○ (Alta)                       │
│                                     │
│  📝 Descripción                     │
│  Bache grande que afecta ambos      │
│  carriles en la intersección con... │
│  [Leer más]                         │
│                                     │
│  ── Información adicional ──        │
│                                     │
│  ☑️ Acepto términos y condiciones   │
│  ☑️ Permitir uso de mi ubicación    │
│                                     │
│  ┌─────────────────────────────┐   │
│  │   [✓] ENVIAR REPORTE        │   │
│  └─────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

**Funcionalidades:**
- Resumen visual de todos los datos
- Links para editar cada sección
- Checkboxes de consentimiento
- Botón de envío con loading state

---

### 2.9 Wireframe 8: Confirmación de Envío

```
┌─────────────────────────────────────┐
│                                     │
│                                     │
│           ✓                         │
│         (checkmark animado)         │
│                                     │
│     ¡Reporte enviado con éxito!     │
│                                     │
│  Tu reporte ha sido recibido y      │
│  será validado en las próximas      │
│  24 horas.                          │
│                                     │
│  Folio: #2026-001234                │
│                                     │
│  ┌─────────────────────────────┐   │
│  │   Estado: En validación     │   │
│  │   Creado: 14 ene 2026 10:30 │   │
│  └─────────────────────────────┘   │
│                                     │
│  Te notificaremos cuando haya       │
│  cambios en tu reporte.             │
│                                     │
│  ┌─────────────────────────────┐   │
│  │  [Ver mi reporte]           │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │  [Ir al inicio]             │   │
│  └─────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

**Funcionalidades:**
- Animación de éxito (checkmark)
- Mostrar folio del reporte
- Opciones para ver detalle o volver al inicio
- Auto-redirect después de 5 segundos

---

### 2.10 Wireframe 9: Detalle de Reporte (Ciudadano)

```
┌─────────────────────────────────────┐
│ [← Volver]  Reporte #2026-001234    │
├─────────────────────────────────────┤
│                                     │
│  ┌───────────────────────────────┐ │
│  │ [Imagen del reporte]          │ │
│  │        (swipeable si hay      │ │
│  │         múltiples fotos)      │ │
│  └───────────────────────────────┘ │
│                                     │
│  Estado: 🟡 Validado                │
│  Prioridad: Alta                    │
│                                     │
│  ── Timeline ──                     │
│                                     │
│  ✓ Creado                           │
│    14 ene 2026, 10:30               │
│                                     │
│  ✓ Validado                         │
│    14 ene 2026, 15:45               │
│    Operador: M. García              │
│                                     │
│  ○ Asignado (pendiente)             │
│                                     │
│  ── Detalles ──                     │
│                                     │
│  📍 Ubicación                       │
│  Av. Juárez #123, Centro            │
│  [Ver en mapa →]                    │
│                                     │
│  🏷️ Categoría                       │
│  Bache grande                       │
│                                     │
│  📝 Descripción                     │
│  Bache grande que afecta ambos      │
│  carriles en la intersección...     │
│                                     │
│  💬 Comentarios (2)                 │
│  ┌─────────────────────────────┐   │
│  │ Operador M. García:         │   │
│  │ "Validado. Alta prioridad." │   │
│  │ 14 ene, 15:45               │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ Tú:                         │   │
│  │ "Gracias por la atención"   │   │
│  │ 14 ene, 16:00               │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 💬 Agregar comentario       │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 📷 Agregar más evidencia    │   │
│  └─────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

**Componentes:**
- Carrusel de imágenes
- Badge de estado con color
- Timeline vertical de eventos
- Sección de detalles expandible
- Lista de comentarios con timestamps
- Botones de acción (comentar, agregar foto)

---

### 2.11 Wireframe 10: Mapa de Reportes

```
┌─────────────────────────────────────┐
│ [☰]  Mapa de reportes  [⚙️]         │
├─────────────────────────────────────┤
│                                     │
│  ┌───────────────────────────────┐ │
│  │ [Filtros activos: Todos] ▼    │ │
│  └───────────────────────────────┘ │
│                                     │
│  ┌───────────────────────────────┐ │
│  │                               │ │
│  │    [Mapa con pins coloreados] │ │
│  │                               │ │
│  │    🔴 <- Crítico              │ │
│  │  🟠  🟡 <- Media/Alta          │ │
│  │      🟢 <- Baja               │ │
│  │                               │ │
│  │  [My Location] [Layers]       │ │
│  │  [Zoom +/-]                   │ │
│  │                               │ │
│  └───────────────────────────────┘ │
│                                     │
│  ┌───────────────────────────────┐ │
│  │ Reportes cercanos (3)         │ │
│  │                               │ │
│  │ 🔴 Socavón - Av. Reforma      │ │
│  │    500m • Crítico             │ │
│  │    [Ver →]                    │ │
│  │                               │ │
│  │ 🟡 Bache - Calle 5            │ │
│  │    800m • Media               │ │
│  │    [Ver →]                    │ │
│  └───────────────────────────────┘ │
│                                     │
│  (Desliza para ver más)             │
│                                     │
└─────────────────────────────────────┘
│ [🏠 Home] [📍 Mapa] [📋 Reportes]  │
└─────────────────────────────────────┘
```

**Funcionalidades:**
- Mapa interactivo con clusters si hay muchos pins
- Pins coloreados según prioridad
- Filtros (por categoría, prioridad, fecha)
- Bottom sheet con lista de reportes cercanos
- Tap en pin → mostrar popup con detalle básico

---

### 2.12 Wireframe 11: Lista de Mis Reportes

```
┌─────────────────────────────────────┐
│ [☰ Menu]  Mis reportes              │
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────────────────────┐   │
│  │ [Buscar...] 🔍              │   │
│  └─────────────────────────────┘   │
│                                     │
│  Filtros: [Todos ▼] [Fecha ▼]      │
│                                     │
│  ── Activos (3) ──                  │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 🔴 Bache en Av. Juárez      │   │
│  │                             │   │
│  │ En progreso                 │   │
│  │ Hace 2 días • #2026-001234  │   │
│  │                             │   │
│  │ [Ver detalles]              │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 🟡 Señal caída              │   │
│  │                             │   │
│  │ Validado                    │   │
│  │ Hace 5 días • #2026-001189  │   │
│  │                             │   │
│  │ [Ver detalles]              │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 🟢 Grieta superficial       │   │
│  │                             │   │
│  │ En validación               │   │
│  │ Hace 7 días • #2026-001002  │   │
│  │                             │   │
│  │ [Ver detalles]              │   │
│  └─────────────────────────────┘   │
│                                     │
│  ── Cerrados (5) ──                 │
│  [Mostrar →]                        │
│                                     │
└─────────────────────────────────────┘
│ [🏠 Home] [📍 Mapa] [📋 Reportes]  │
└─────────────────────────────────────┘
```

**Componentes:**
- Barra de búsqueda
- Filtros (estado, fecha)
- Cards de reportes con estado visual
- Sección colapsable de cerrados
- Pull-to-refresh

---

### 2.13 Wireframe 12: Notificaciones

```
┌─────────────────────────────────────┐
│ [← Volver]  Notificaciones  [✓ Todas]│
├─────────────────────────────────────┤
│                                     │
│  Hoy                                │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ ● Reporte #2026-001234      │   │
│  │                             │   │
│  │ Tu reporte fue asignado.    │   │
│  │                             │   │
│  │                             │   │
│  │ Hace 2 horas                │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ ● Reporte #2026-001189      │   │
│  │                             │   │
│  │ Tu reporte fue validado.    │   │
│  │ Prioridad: Alta             │   │
│  │                             │   │
│  │ Hace 5 horas                │   │
│  └─────────────────────────────┘   │
│                                     │
│  Ayer                               │
│                                     │
│  ┌─────────────────────────────┐   │
│  │   Reporte #2026-001002      │   │
│  │                             │   │
│  │ Operador M. García comentó  │   │
│  │ en tu reporte.              │   │
│  │                             │   │
│  │ 13 ene, 14:30               │   │
│  └─────────────────────────────┘   │
│                                     │
│  Esta semana                        │
│                                     │
│  ┌─────────────────────────────┐   │
│  │   Reporte #2026-000987      │   │
│  │                             │   │
│  │ Tu reporte fue cerrado.     │   │
│  │ ¡Gracias por tu reporte!    │   │
│  │                             │   │
│  │ 11 ene, 09:15               │   │
│  └─────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

**Funcionalidades:**
- Agrupación por fecha
- Badge de no leído (●)
- Tap en notificación → navegar a detalle del reporte
- Marcar todas como leídas

---

## 3. Dashboard Municipal (Web)

### 3.1 Flujo principal

```
[Login] → [Dashboard] → [Mapa] / [Tabla] / [Métricas]
           ↓
       [Gestión de Reportes] → [Validar] / [Asignar] / [Cerrar]
           ↓
       [Configuración del Sistema]
```

---

### 3.2 Wireframe 20: Login Municipal

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                                                                 │
│                      [LOGO MUNICIPIO]                           │
│                                                                 │
│                  Dashboard Municipal - SIRCCD                   │
│                                                                 │
│        ┌─────────────────────────────────────────┐             │
│        │                                         │             │
│        │  Usuario                                │             │
│        │  ┌───────────────────────────────────┐ │             │
│        │  │ operador@municipio.gob.mx         │ │             │
│        │  └───────────────────────────────────┘ │             │
│        │                                         │             │
│        │  Contraseña                             │             │
│        │  ┌───────────────────────────────────┐ │             │
│        │  │ ••••••••••••                      │ │             │
│        │  └───────────────────────────────────┘ │             │
│        │                                         │             │
│        │  ☑️ Recordar sesión                     │             │
│        │                                         │             │
│        │  ┌───────────────────────────────────┐ │             │
│        │  │      Iniciar sesión               │ │             │
│        │  └───────────────────────────────────┘ │             │
│        │                                         │             │
│        │  ¿Olvidaste tu contraseña?              │             │
│        │                                         │             │
│        └─────────────────────────────────────────┘             │
│                                                                 │
│              Soporte técnico: soporte@municipio.gob.mx          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### 3.3 Wireframe 21: Dashboard Principal (Operador)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [LOGO] SIRCCD                        Operador M. García  [🔔 5] [⚙️] [👤] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ [Dashboard] [Mapa] [Reportes] [Métricas] [Configuración]        │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐│
│ │ Resumen del día - Martes 14 de Enero, 2026                             ││
│ │                                                                         ││
│ │ ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐      ││
│ │ │   🔴    │  │   🟠    │  │   🟡    │  │   ✅    │  │   ⏱️    │      ││
│ │ │    8    │  │   23    │  │   45    │  │   12    │  │   3.2h  │      ││
│ │ │Críticos │  │  Altos  │  │ Medios  │  │Resueltos│  │Prom.resp││
│ │ └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘      ││
│ └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐│
│ │ Reportes pendientes de validar                                         ││
│ │                                                                         ││
│ │ ┌────────────────────────────┐  ┌────────────────────────────┐          ││
│ │ │🔴 #2026-001456             │  │🟠 #2026-001455             │          ││
│ │ │Socavón - Av. Reforma       │  │Bache - Calle 5             │          ││
│ │ │Hace 15 min                 │  │Hace 1 hora                 │          ││
│ │ │[Validar] [Rechazar]        │  │[Validar] [Rechazar]        │          ││
│ │ └────────────────────────────┘  └────────────────────────────┘          ││
│ │                                                                         ││
│ │ [Ver todos (12)]                                                        ││
│ └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐│
│ │ Gráfica: Reportes por día (últimos 7 días)                             ││
│ │                                                                         ││
│ │  60 ┤                                                           ●       ││
│ │     │                                                     ●             ││
│ │  40 ┤                                         ●     ●                   ││
│ │     │                           ●       ●                               ││
│ │  20 ┤               ●     ●                                             ││
│ │     │                                                                   ││
│ │   0 └───────┬───────┬───────┬───────┬───────┬───────┬───────          ││
│ │           Lun    Mar    Mié    Jue    Vie    Sáb    Dom               ││
│ │                                                                         ││
│ │  [Nuevos: ●]  [Resueltos: ○]                     [Exportar datos]      ││
│ └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Componentes:**
- Header con navegación principal
- Cards de KPIs (métricas clave)
- Widgets de reportes pendientes
- Gráficas de tendencias
- Acciones rápidas por widget

---

### 3.4 Wireframe 22: Vista de Mapa (Municipal)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [LOGO] SIRCCD                                    [🔔 5] [⚙️] [👤] M. García │
├─────────────────────────────────────────────────────────────────────────────┤
│ [Dashboard] [Mapa] [Reportes] [Métricas] [Configuración]        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ ┌───────────────────────────────┐ ┌───────────────────────────────────────┐│
│ │ Filtros                       │ │                                       ││
│ │                               │ │                                       ││
│ │ Prioridad:                    │ │      [Mapa con clusters de pins]     ││
│ │ ☑️ Crítica  ☑️ Alta  ☑️ Media  │ │                                       ││
│ │ ☑️ Baja  ☑️ Mínima             │ │   🔴 Cluster (8)                     ││
│ │                               │ │        🟠 Pin                         ││
│ │ Estado:                       │ │   🟡 Pin    🟢 Pin                    ││
│ │ ☑️ Nuevo  ☑️ Validado          │ │                                       ││
│ │ ☑️ Asignado  ☑️ En progreso    │ │                                       ││
│ │ ☐ Resuelto  ☐ Cerrado         │ │   [+] [-] [Layers] [My Location]     ││
│ │                               │ │                                       ││
│ │ Fecha:                        │ │                                       ││
│ │ Últimas 24h ▼                 │ │                                       ││
│ │                               │ │                                       ││
│ │ [Aplicar filtros]             │ │                                       ││
│ │ [Limpiar]                     │ │                                       ││
│ │                               │ │                                       ││
│ │ ── Leyenda ──                 │ │                                       ││
│ │ 🔴 Crítica                    │ │                                       ││
│ │ 🟠 Alta                       │ │                                       ││
│ │ 🟡 Media                      │ │                                       ││
│ │ 🟢 Baja                       │ │                                       ││
│ │ 🔵 Mínima                     │ │                                       ││
│ └───────────────────────────────┘ └───────────────────────────────────────┘│
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐│
│ │ Reportes en vista (23)                                    [Vista tabla] ││
│ │                                                                         ││
│ │ ┌──────┬────────────────────────────┬──────────┬────────┬────────────┐ ││
│ │ │Folio │Ubicación                   │Categoría │Prior.  │Estado      │ ││
│ │ ├──────┼────────────────────────────┼──────────┼────────┼────────────┤ ││
│ │ │001456│Av. Reforma #456            │Socavón   │🔴Crít. │Validado    │ ││
│ │ │001455│Calle 5 #123                │Bache     │🟠Alto  │Asignado    │ ││
│ │ │001454│Av. Juárez #789             │Señal     │🟡Medio │En progreso │ ││
│ │ └──────┴────────────────────────────┴──────────┴────────┴────────────┘ ││
│ └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Funcionalidades:**
- Filtros múltiples (prioridad, estado, fecha)
- Mapa con clustering dinámico
- Panel inferior con lista de reportes visible
- Click en pin → popup con acciones rápidas

---

### 3.5 Wireframe 23: Tabla de Reportes (Municipal)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [LOGO] SIRCCD                                    [🔔 5] [⚙️] [👤] M. García │
├─────────────────────────────────────────────────────────────────────────────┤
│ [Dashboard] [Mapa] [Reportes] [Métricas] [Configuración]        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Gestión de Reportes                                                        │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐│
│ │ [Buscar por folio, ubicación, descripción...]            [🔍]           ││
│ │                                                                         ││
│ │ Filtros: [Prioridad ▼] [Estado ▼] [Categoría ▼] [Fecha ▼]             ││
│ │                                                                         ││
│ │ [Aplicar filtros] [Limpiar] [Exportar CSV] [Exportar PDF]              ││
│ └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐│
│ │ Acciones múltiples: [Asignar ▼] [Cambiar prioridad ▼]                 ││
│ │ [Cerrar seleccionados] [Exportar selección]                             ││
│ └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐│
│ │                                                                         ││
│ │ ☐ Folio     Ubicación          Categoría  Prior. Estado    Asignado ... ││
│ │ ────────────────────────────────────────────────────────────────────── ││
│ │ ☐ #001456   Av. Reforma #456   Socavón    🔴    Validado   Norte    [>]││
│ │             Zona Norte                    Crít.                        ││
│ │             Hace 2h                                                     ││
│ │                                                                         ││
│ │ ☐ #001455   Calle 5 #123       Bache      🟠    Asignado   Sur      [>]││
│ │             Centro                        Alto                         ││
│ │             Hace 5h                                                     ││
│ │                                                                         ││
│ │ ☐ #001454   Av. Juárez #789    Señal      🟡    En prog.   Norte    [>]││
│ │             Zona Oeste                    Medio                        ││
│ │             Hace 1 día                                                  ││
│ │                                                                         ││
│ │ ☐ #001453   Blvd. López #234   Alumbrado  🔴    Nuevo      -        [>]││
│ │             Zona Sur                      Crít.                        ││
│ │             Hace 30 min                                                 ││
│ │                                                                         ││
│ │ ☐ #001452   Calle 12 #567      Alcantari  🟠    Resuelto   Centro   [>]││
│ │             Zona Este                     Alto                         ││
│ │             Hace 2 días                                                 ││
│ │                                                                         ││
│ │ ☐ #001451   Parque Central     Basura     🟡    Validado   Sur      [>]││
│ │             Centro                        Medio                        ││
│ │             Hace 4h                                                     ││
│ │                                                                         ││
│ │ ☐ #001450   Av. Hidalgo #890   Bache      🟢    Asignado   Norte    [>]││
│ │             Zona Norte                    Bajo                         ││
│ │             Hace 6h                                                     ││
│ │                                                                         ││
│ │ ☐ #001449   Calle 8 #345       Grafiti    🔵    Cerrado    Centro   [>]││
│ │             Centro                        Mín.                         ││
│ │             Hace 3 días                                                 ││
│ │                                                                         ││
│ │ ────────────────────────────────────────────────────────────────────── ││
│ │                                                                         ││
│ │ Mostrando 1-8 de 156 reportes           [<] Página 1 de 20 [>]         ││
│ │                                                                         ││
│ └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Funcionalidades:**
- Búsqueda full-text
- Filtros avanzados combinables
- Selección múltiple con acciones en lote
- Ordenamiento por columna (click en header)
- Paginación
- Exportación a CSV/PDF
- Click en fila → ver detalle
- Indicadores visuales de prioridad y estado

---

### 3.6 Wireframe 24: Detalle de Reporte (Operador Municipal)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [LOGO] SIRCCD                                    [🔔 5] [⚙️] [👤] M. García │
├─────────────────────────────────────────────────────────────────────────────┤
│ [← Volver a lista]  Reporte #2026-001456                       [Editar]    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ ┌────────────────────────────────────┐ ┌──────────────────────────────────┐│
│ │ Información general                │ │ Acciones rápidas                 ││
│ │                                    │ │                                  ││
│ │ Estado: 🟡 Validado                │ │ ┌──────────────────────────────┐ ││
│ │ Prioridad: 🔴 Crítica (95/100)     │ │ │ Asignar                      │ ││
│ │ Categoría: Socavón                 │ │ └──────────────────────────────┘ ││
│ │                                    │ │                                  ││
│ │ Reportado: 14 ene 2026, 08:30      │ │ ┌──────────────────────────────┐ ││
│ │ Por: Juan Pérez                    │ │ │ Cambiar prioridad            │ ││
│ │ Contacto: 555-1234                 │ │ └──────────────────────────────┘ ││
│ │                                    │ │                                  ││
│ │ Validado: 14 ene 2026, 09:00       │ │ ┌──────────────────────────────┐ ││
│ │ Por: M. García (tú)                │ │ │ Rechazar reporte             │ ││
│ │                                    │ │ └──────────────────────────────┘ ││
│ │ Asignado: Carlos Martínez          │ │ ┌──────────────────────────────┐ ││
│ │ Estado: 🚗 En ruta                 │ │ │ Exportar PDF                 │ ││
│ │                                    │ │ └──────────────────────────────┘ ││
│ └────────────────────────────────────┘ │                                  ││
│                                        │ ┌──────────────────────────────┐ ││
│ ┌────────────────────────────────────┐ │ │ Cerrar reporte               │ ││
│ │ Ubicación                          │ │ └──────────────────────────────┘ ││
│ │                                    │ └──────────────────────────────────┘│
│ │ 📍 Av. Reforma #456, Zona Norte    │                                    │
│ │    CP 64000                        │                                    │
│ │                                    │                                    │
│ │ ┌────────────────────────────────┐ │                                    │
│ │ │ [Mapa con pin]                 │ │                                    │
│ │ │                                │ │                                    │
│ │ │ 📍 Ubicación del daño          │ │                                    │
│ │ │ 👷 Equipo asignado (1.2 km)    │ │                                    │
│ │ │                                │ │                                    │
│ │ │ [Abrir en Google Maps]         │ │                                    │
│ │ └────────────────────────────────┘ │                                    │
│ │                                    │                                    │
│ └────────────────────────────────────┘                                    │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐│
│ │ Descripción del ciudadano                                               ││
│ │                                                                         ││
│ │ Socavón de aproximadamente 80cm de diámetro y 40cm de profundidad que  ││
│ │ afecta el carril derecho de la Av. Reforma. Representa un riesgo para  ││
│ │ vehículos y peatones. Se observa daño en el asfalto y exposición de    ││
│ │ tierra y piedras.                                                       ││
│ │                                                                         ││
│ └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐│
│ │ Evidencia fotográfica (3)                                               ││
│ │                                                                         ││
│ │ ┌───────────┐ ┌───────────┐ ┌───────────┐                              ││
│ │ │ [Imagen 1]│ │ [Imagen 2]│ │ [Imagen 3]│                              ││
│ │ │           │ │           │ │           │                              ││
│ │ │ Vista gral│ │ Acercam.  │ │ Contexto  │                              ││
│ │ └───────────┘ └───────────┘ └───────────┘                              ││
│ │                                                                         ││
│ │ [Ver galería completa]                                                  ││
│ │                                                                         ││
│ └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐│
│ │ Análisis automático (ML)                                                ││
│ │                                                                         ││
│ │ • Categoría detectada: Socavón (95% confianza)                          ││
│ │ • Severidad estimada: Alta                                              ││
│ │ • Dimensiones: ~80cm × 40cm (profundidad estimada)                      ││
│ │ • Materiales requeridos: 1 ton asfalto, rodillo compactador             ││
│ │ • Tiempo estimado de reparación: 2-3 horas                              ││
│ │ • Costo estimado: $3,500 - $5,000 MXN                                   ││
│ │                                                                         ││
│ └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐│
│ │ Cálculo de prioridad (Score: 95/100)                                    ││
│ │                                                                         ││
│ │ • Severidad ML: 40/40 pts (máximo)                                      ││
│ │ • Denuncias múltiples: 20/20 pts (5 reportes del mismo daño)            ││
│ │ • Ubicación: 15/15 pts (vía primaria)                                   ││
│ │ • Impacto social: 12/15 pts (zona residencial)                          ││
│ │ • Antigüedad: 8/10 pts (2 horas sin atención)                           ││
│ │                                                                         ││
│ │ [Ver detalles del cálculo]                                              ││
│ │                                                                         ││
│ └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐│
│ │ Historial de estados                                                    ││
│ │                                                                         ││
│ │ 🟡 Validado           14 ene 2026, 09:00   M. García                    ││
│ │    "Reporte válido, requiere atención urgente"                          ││
│ │                                                                         ││
│ │ 🔵 Nuevo              14 ene 2026, 08:30   Sistema                      ││
│ │    "Reporte creado por ciudadano"                                       ││
│ │                                                                         ││
│ └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐│
│ │ Comentarios internos                                                    ││
│ │                                                                         ││
│ │ [Agregar comentario...]                                                 ││
│ │                                                                         ││
│ │ No hay comentarios aún                                                  ││
│ │                                                                         ││
│ └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Funcionalidades:**
- Vista completa de información del reporte
- Acciones contextuales según estado
- Análisis ML con métricas
- Desglose del score de prioridad
- Historial completo de cambios
- Sistema de comentarios internos
- Exportación a PDF
- Mapa interactivo con ubicación

---

### 3.8 Wireframe 26: Panel de Métricas y Analytics

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [LOGO] SIRCCD                                    [🔔 5] [⚙️] [👤] M. García │
├─────────────────────────────────────────────────────────────────────────────┤
│ [Dashboard] [Mapa] [Reportes] [Métricas] [Configuración]        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Métricas y Analytics                                                        │
│                                                                             │
│ Período: [Últimos 30 días ▼]  [Comparar con mes anterior ☐]  [Exportar]   │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐│
│ │ KPIs principales                                                        ││
│ │                                                                         ││
│ │ ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ ││
│ │ │   1,234  │  │    892   │  │    342   │  │   3.2h   │  │   89%    │ ││
│ │ │  Reportes│  │Resueltos │  │ Pendien. │  │Tiempo    │  │Resolu-   │ ││
│ │ │  totales │  │          │  │          │  │promedio  │  │ción      │ ││
│ │ │  ▲ +12%  │  │  ▲ +8%   │  │  ▼ -5%   │  │  ▼ -15%  │  │  ▲ +3%   │ ││
│ │ └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘ ││
│ └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│ ┌────────────────────────────────────┐ ┌──────────────────────────────────┐│
│ │ Reportes por día                   │ │ Distribución por categoría       ││
│ │                                    │ │                                  ││
│ │  60 ┤                       ●      │ │  ┌─────────────────────────────┐││
│ │     │                 ●            │ │  │ Baches       35% █████████  │││
│ │  40 ┤           ●                  │ │  │ Socavones    22% ██████     │││
│ │     │     ●                        │ │  │ Alumbrado    18% █████      │││
│ │  20 ┤ ●                            │ │  │ Alcantarilla 12% ███        │││
│ │     │                              │ │  │ Basura        8% ██         │││
│ │   0 └───┬───┬───┬───┬───┬───┬──   │ │  │ Otros         5% █          │││
│ │       1  5  10  15  20  25  30    │ │  └─────────────────────────────┘││
│ │                                    │ │                                  ││
│ │  [Nuevos] [Resueltos] [En progr.]│ │  [Ver detalles por subcategoría] ││
│ └────────────────────────────────────┘ └──────────────────────────────────┘│
│                                                                             │
│ ┌────────────────────────────────────┐ ┌──────────────────────────────────┐│
│ │ Distribución por prioridad         │ │ Tiempo de resolución por prior.  ││
│ │                                    │ │                                  ││
│ │       🔴 Crítica    8%             │ │  🔴 Crítica    1.5h promedio     ││
│ │       🟠 Alta      19%             │ │  🟠 Alta       2.8h promedio     ││
│ │       🟡 Media     36%             │ │  🟡 Media      5.2h promedio     ││
│ │       🟢 Baja      28%             │ │  🟢 Baja      12.4h promedio     ││
│ │       🔵 Mínima     9%             │ │  🔵 Mínima    24.8h promedio     ││
│ │                                    │ │                                  ││
│ │  ┌────────────────────────┐       │ │  ┌─────────────────────────────┐││
│ │  │ [Gráfico de dona]      │       │ │  │ [Gráfico de barras]         │││
│ │  │        36%             │       │ │  │  ███                        │││
│ │  │    🟡          🟢       │       │ │  │  ███████                    │││
│ │  │  19%  28%              │       │ │  │  ████████████               │││
│ │  │🟠 🔴  🔵                │       │ │  │  ████████████████████████   │││
│ │  │  8%   9%               │       │ │  │  █████████████████████████  │││
│ │  └────────────────────────┘       │ │  └─────────────────────────────┘││
│ └────────────────────────────────────┘ └──────────────────────────────────┘│
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐│
│ │ Rendimiento operativo                                                   ││
│ │                                                                         ││
│ │ Equipo        Asignados  Resueltos  En prog.  Tasa res.  Tiempo prom.  ││
│ │ ────────────────────────────────────────────────────────────────────── ││
│ │ Norte            156        148         8       95%         2.8h       ││
│ │ Sur              134        116        18       87%         3.5h       ││
│ │ Centro           189        181         8       96%         2.2h       ││
│ │ Este             112         98        14       88%         3.1h       ││
│ │ Oeste             98         89         9       91%         2.9h       ││
│ │                                                                         ││
│ │ [Ver detalles por operador]                                             ││
│ └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│ ┌────────────────────────────────────┐ ┌──────────────────────────────────┐│
│ │ Mapa de calor - Zonas críticas     │ │ Horarios de mayor reporte        ││
│ │                                    │ │                                  ││
│ │ ┌────────────────────────────────┐ │ │  100 ┤                          ││
│ │ │ [Mapa con intensidad de color] │ │ │      │        ██                ││
│ │ │                                │ │ │   75 ┤    ██  ██  ██            ││
│ │ │  🔥 Zona Norte (234 reportes)  │ │ │      │ ██ ██  ██  ██  ██        ││
│ │ │  🔥 Centro (189 reportes)      │ │ │   50 ┤ ██ ██  ██  ██  ██  ██    ││
│ │ │  🟡 Zona Sur (134 reportes)    │ │ │      │ ██ ██  ██  ██  ██  ██  ██││
│ │ │  🟡 Zona Este (112 reportes)   │ │ │   25 ┤ ██ ██  ██  ██  ██  ██  ██││
│ │ │  🟢 Zona Oeste (98 reportes)   │ │ │      │ ██ ██  ██  ██  ██  ██  ██││
│ │ │                                │ │ │    0 └─┬──┬───┬───┬───┬───┬───┬─││
│ │ └────────────────────────────────┘ │ │      0 4  8  12  16  20  24   ││
│ │                                    │ │                                  ││
│ │ [Exportar datos geoespaciales]     │ │  Pico: 08:00-10:00 (73 reportes) ││
│ └────────────────────────────────────┘ └──────────────────────────────────┘│
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐│
│ │ Satisfacción ciudadana (últimas 500 calificaciones)                     ││
│ │                                                                         ││
│ │  Calificación promedio: 4.3 / 5.0  ⭐⭐⭐⭐☆                              ││
│ │                                                                         ││
│ │  5 estrellas  ████████████████████████████████  58%  (290)             ││
│ │  4 estrellas  ████████████████                  28%  (140)             ││
│ │  3 estrellas  ████                               8%   (40)             ││
│ │  2 estrellas  ██                                 4%   (20)             ││
│ │  1 estrella   █                                  2%   (10)             ││
│ │                                                                         ││
│ │  [Ver comentarios de ciudadanos]                                        ││
│ └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Funcionalidades:**
- KPIs con comparaciones temporales
- Múltiples gráficas (líneas, dona, barras, mapa de calor)
- Filtrado por período personalizado
- Tabla de rendimiento operativo
- Mapa de calor geoespacial
- Análisis de horarios pico
- Métricas de satisfacción
- Exportación de datos (CSV, PDF, JSON)

---

### 3.9 Wireframe 27: Configuración del Sistema

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [LOGO] SIRCCD                                    [🔔 5] [⚙️] [👤] M. García │
├─────────────────────────────────────────────────────────────────────────────┤
│ [Dashboard] [Mapa] [Reportes] [Métricas] [Configuración]        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Configuración del Sistema                                                   │
│                                                                             │
│ ┌───────────────────────┐ ┌─────────────────────────────────────────────┐ │
│ │ Navegación            │ │                                             │ │
│ │                       │ │ Pesos del Score de Prioridad                │ │
│ │ • Score de prioridad  │ │                                             │ │
│ │ • Categorías          │ │ Configuración de pesos para el cálculo      │ │
│ │ • Umbrales            │ │ automático de prioridad (Total: 100 pts)    │ │
│ │ • Notificaciones      │ │                                             │ │
│ │ • Usuarios y roles    │ │ ┌─────────────────────────────────────────┐ │ │
│ │ • Integrations        │ │ │ Severidad detectada por ML              │ │ │
│ │ • Sistema             │ │ │                                         │ │ │
│ │                       │ │ │ Peso actual: 40 pts (40%)               │ │ │
│ │                       │ │ │                                         │ │ │
│ │                       │ │ │ ├────────────────────────┤──────┤       │ │ │
│ │                       │ │ │ 0        20        40        60    100  │ │ │
│ │                       │ │ │                                         │ │ │
│ │                       │ │ │ Descripción:                            │ │ │
│ │                       │ │ │ Peso asignado según la severidad del    │ │ │
│ │                       │ │ │ daño detectado por el modelo ML.        │ │ │
│ │                       │ │ └─────────────────────────────────────────┘ │ │
│ │                       │ │                                             │ │
│ │                       │ │ ┌─────────────────────────────────────────┐ │ │
│ │                       │ │ │ Denuncias múltiples                     │ │ │
│ │                       │ │ │                                         │ │ │
│ │                       │ │ │ Peso actual: 20 pts (20%)               │ │ │
│ │                       │ │ │                                         │ │ │
│ │                       │ │ │ ├──────────┤──────────────────────┤     │ │ │
│ │                       │ │ │ 0        20        40        60    100  │ │ │
│ │                       │ │ │                                         │ │ │
│ │                       │ │ │ Máximo de denuncias: 5 ▼                │ │ │
│ │                       │ │ │ Puntos por denuncia: 4 pts              │ │ │
│ │                       │ │ └─────────────────────────────────────────┘ │ │
│ │                       │ │                                             │ │
│ │                       │ │ ┌─────────────────────────────────────────┐ │ │
│ │                       │ │ │ Tipo de vía                             │ │ │
│ │                       │ │ │                                         │ │ │
│ │                       │ │ │ Peso actual: 15 pts (15%)               │ │ │
│ │                       │ │ │                                         │ │ │
│ │                       │ │ │ ├──────┤────────────────────────────┤   │ │ │
│ │                       │ │ │ 0        20        40        60    100  │ │ │
│ │                       │ │ │                                         │ │ │
│ │                       │ │ │ Vía primaria: 15 pts                    │ │ │
│ │                       │ │ │ Vía secundaria: 10 pts                  │ │ │
│ │                       │ │ │ Vía terciaria: 5 pts                    │ │ │
│ │                       │ │ └─────────────────────────────────────────┘ │ │
│ │                       │ │                                             │ │
│ │                       │ │ ┌─────────────────────────────────────────┐ │ │
│ │                       │ │ │ Impacto social                          │ │ │
│ │                       │ │ │                                         │ │ │
│ │                       │ │ │ Peso actual: 15 pts (15%)               │ │ │
│ │                       │ │ │                                         │ │ │
│ │                       │ │ │ ├──────┤────────────────────────────┤   │ │ │
│ │                       │ │ │ 0        20        40        60    100  │ │ │
│ │                       │ │ │                                         │ │ │
│ │                       │ │ │ Zona alta densidad: 15 pts              │ │ │
│ │                       │ │ │ Zona media densidad: 10 pts             │ │ │
│ │                       │ │ │ Zona baja densidad: 5 pts               │ │ │
│ │                       │ │ └─────────────────────────────────────────┘ │ │
│ │                       │ │                                             │ │
│ │                       │ │ ┌─────────────────────────────────────────┐ │ │
│ │                       │ │ │ Antigüedad del reporte                  │ │ │
│ │                       │ │ │                                         │ │ │
│ │                       │ │ │ Peso actual: 10 pts (10%)               │ │ │
│ │                       │ │ │                                         │ │ │
│ │                       │ │ │ ├────┤──────────────────────────────┤   │ │ │
│ │                       │ │ │ 0        20        40        60    100  │ │ │
│ │                       │ │ │                                         │ │ │
│ │                       │ │ │ > 24h sin atención: 10 pts              │ │ │
│ │                       │ │ │ > 12h sin atención: 7 pts               │ │ │
│ │                       │ │ │ > 6h sin atención: 4 pts                │ │ │
│ │                       │ │ │ < 6h: 0 pts                             │ │ │
│ │                       │ │ └─────────────────────────────────────────┘ │ │
│ │                       │ │                                             │ │
│ │                       │ │ ┌─────────────────────────────────────────┐ │ │
│ │                       │ │ │ Total: 100 pts ✅                        │ │ │
│ │                       │ │ │                                         │ │ │
│ │                       │ │ │ [Restablecer valores por defecto]       │ │ │
│ │                       │ │ │ [Guardar cambios]                       │ │ │
│ │                       │ │ │                                         │ │ │
│ │                       │ │ │ ⚠️ Los cambios afectarán el cálculo de   │ │ │
│ │                       │ │ │ prioridad de reportes nuevos.           │ │ │
│ │                       │ │ └─────────────────────────────────────────┘ │ │
│ │                       │ │                                             │ │
│ └───────────────────────┘ └─────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Funcionalidades:**
- Ajuste dinámico de pesos del score
- Validación en tiempo real (suma = 100)
- Configuración de umbrales por componente
- Restaurar valores por defecto
- Advertencias sobre impacto de cambios
- Guardado con confirmación

---

### 3.11 Wireframe 29: Configuración - Categorías

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [LOGO] SIRCCD                                    [🔔 5] [⚙️] [👤] M. García │
├─────────────────────────────────────────────────────────────────────────────┤
│ [Dashboard] [Mapa] [Reportes] [Métricas] [Configuración]        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Configuración del Sistema                                                   │
│                                                                             │
│ ┌───────────────────────┐ ┌─────────────────────────────────────────────┐ │
│ │ Navegación            │ │                                             │ │
│ │                       │ │ Gestión de Categorías                       │ │
│ │ • Score de prioridad  │ │                                             │ │
│ │ • Categorías          │ │ ┌─────────────────────────────────────────┐ │ │
│ │ • Umbrales            │ │ │ [+ Nueva categoría]                     │ │ │
│ │ • Notificaciones      │ │ └─────────────────────────────────────────┘ │ │
│ │ • Usuarios y roles    │ │                                             │ │
│ │ • Integrations        │ │ ┌─────────────────────────────────────────┐ │ │
│ │ • Sistema             │ │ │ 🚧 Baches                    [Edit] [...] │ │ │
│ │                       │ │ │                                         │ │ │
│ │                       │ │ │ Activa: ✅ | Icono: 🚧                  │ │ │
│ │                       │ │ │ Materiales: Asfalto, Rodillo            │ │ │
│ │                       │ │ │ Tiempo estimado: 20-45 min              │ │ │
│ │                       │ │ │ Costo promedio: $800-1,500 MXN          │ │ │
│ │                       │ │ │                                         │ │ │
│ │                       │ │ │ Reportes este mes: 432 (35%)            │ │ │
│ │                       │ │ └─────────────────────────────────────────┘ │ │
│ │                       │ │                                             │ │
│ │                       │ │ ┌─────────────────────────────────────────┐ │ │
│ │                       │ │ │ 🕳️ Socavones                 [Edit] [...] │ │ │
│ │                       │ │ │                                         │ │ │
│ │                       │ │ │ Activa: ✅ | Icono: 🕳️                  │ │ │
│ │                       │ │ │ Materiales: Asfalto, Equipo pesado      │ │ │
│ │                       │ │ │ Tiempo estimado: 2-4 horas              │ │ │
│ │                       │ │ │ Costo promedio: $3,500-8,000 MXN        │ │ │
│ │                       │ │ │                                         │ │ │
│ │                       │ │ │ Reportes este mes: 271 (22%)            │ │ │
│ │                       │ │ └─────────────────────────────────────────┘ │ │
│ │                       │ │                                             │ │
│ │                       │ │ ┌─────────────────────────────────────────┐ │ │
│ │                       │ │ │ 💡 Alumbrado público         [Edit] [...] │ │ │
│ │                       │ │ │                                         │ │ │
│ │                       │ │ │ Activa: ✅ | Icono: 💡                  │ │ │
│ │                       │ │ │ Materiales: Lámparas, Cableado          │ │ │
│ │                       │ │ │ Tiempo estimado: 1-2 horas              │ │ │
│ │                       │ │ │ Costo promedio: $500-1,200 MXN          │ │ │
│ │                       │ │ │                                         │ │ │
│ │                       │ │ │ Reportes este mes: 222 (18%)            │ │ │
│ │                       │ │ └─────────────────────────────────────────┘ │ │
│ │                       │ │                                             │ │
│ │                       │ │ [Ver todas las categorías (12)]             │ │ │
│ │                       │ │                                             │ │ │
│ └───────────────────────┘ └─────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Especificaciones Técnicas

### 4.1 Responsive Design - Breakpoints

```
Mobile (Portrait):  320px - 479px
Mobile (Landscape): 480px - 767px
Tablet (Portrait):  768px - 1023px
Tablet (Landscape): 1024px - 1279px
Desktop:            1280px - 1919px
Large Desktop:      1920px+
```

**Comportamiento adaptativo:**

- **Mobile**: Navegación en drawer, cards en columna única, mapas pantalla completa
- **Tablet**: Navegación en tabs, grid 2 columnas, sidebars colapsables
- **Desktop**: Navegación horizontal, grid 3-4 columnas, sidebars fijos

### 4.2 Biblioteca de Componentes

#### Componentes base (reutilizables):

1. **Buttons**
   - Primary, Secondary, Tertiary, Danger
   - Tamaños: Small (32px), Medium (40px), Large (48px)
   - Estados: Default, Hover, Active, Disabled, Loading

2. **Cards**
   - ReportCard (vista lista/grid)
   - WorkOrderCard (dashboard)
   - MetricCard (KPIs)
   - Sombras: elevation-1 (2px), elevation-2 (4px), elevation-3 (8px)

3. **Forms**
   - TextInput, TextArea
   - Select, MultiSelect
   - Checkbox, Radio, Toggle
   - DatePicker, TimePicker
   - FileUpload (drag & drop)
   - Validación en tiempo real con mensajes de error

4. **Navigation**
   - TopBar (desktop)
   - BottomNavigation (mobile)
   - Drawer (mobile menu)
   - Breadcrumbs
   - Tabs

5. **Data Display**
   - Table (ordenable, filtrable, paginada)
   - List (virtual scrolling para listas largas)
   - Badge, Tag
   - Avatar, Icon
   - Tooltip, Popover

6. **Feedback**
   - Alert (success, warning, error, info)
   - Toast (notificaciones temporales)
   - Modal, Dialog
   - LoadingSpinner, Skeleton
   - ProgressBar

7. **Maps**
   - MapView (Leaflet/Mapbox)
   - Marker, Cluster
   - Popup, InfoWindow
   - DrawingTools (para delimitación de zonas)

### 4.3 Patrones de Navegación

#### App Ciudadano y Operador:
- **Bottom Navigation** (4-5 items principales)
- **Swipe gestures** para cambiar entre tabs
- **Pull to refresh** en listas
- **Infinite scroll** en listas de reportes
- **Bottom sheets** para filtros y opciones

#### Dashboard Municipal:
- **Top Navigation** con dropdowns
- **Sidebar** colapsable para navegación secundaria
- **Breadcrumbs** para tracking de ubicación
- **Command palette** (Cmd/Ctrl + K) para búsqueda rápida
- **Keyboard shortcuts** para acciones comunes

### 4.4 Comportamiento Offline

**App Ciudadano:**
- Caché de reportes recientes (últimos 50)
- Creación de reportes en modo offline (queue)
- Sincronización automática al recuperar conexión
- Indicador visual de estado de sincronización

**App Operador:**
- Caché de reportes asignados (todos)
- Actualización de estado offline
- Caché de mapas (áreas frecuentes)
- Sincronización bidireccional con conflict resolution

**Dashboard Municipal:**
- Vista de solo lectura offline
- Caché de últimas 24h de datos
- Indicador de "datos desactualizados"

### 4.5 Accesibilidad (WCAG 2.1 AA)

- **Contraste mínimo**: 4.5:1 para texto normal, 3:1 para texto grande
- **Navegación por teclado**: Tab order lógico, focus visible
- **Screen readers**: ARIA labels, roles semánticos
- **Tamaños táctiles**: Mínimo 44×44px para elementos interactivos
- **Texto alternativo**: Todas las imágenes tienen alt descriptivo
- **Zoom**: Soporta hasta 200% sin pérdida de funcionalidad
- **Modo alto contraste**: Paleta alternativa

### 4.6 Performance

**Métricas objetivo:**
- **LCP** (Largest Contentful Paint): < 2.5s
- **FID** (First Input Delay): < 100ms
- **CLS** (Cumulative Layout Shift): < 0.1
- **TTI** (Time to Interactive): < 3.5s

**Optimizaciones:**
- Lazy loading de imágenes
- Code splitting por ruta
- Virtual scrolling en listas >50 items
- Debounce en búsquedas (300ms)
- Memoización de componentes pesados
- Service workers para caché

### 4.7 Animaciones y Transiciones

```css
/* Velocidades estándar */
--transition-fast: 150ms;
--transition-normal: 250ms;
--transition-slow: 350ms;

/* Easing functions */
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
```

**Microinteracciones:**
- Hover en botones (scale 1.02, transition 150ms)
- Click en cards (scale 0.98 → 1.0, transition 100ms)
- Apertura de modals (fade + slide, 250ms)
- Transiciones de página (slide horizontal, 350ms)
- Loading states (skeleton → fade in, 200ms)

---

## 6. Exportación e Implementación

### 6.1 Guía para Figma

**Pasos para crear el diseño en Figma:**

1. **Configuración inicial:**
   - Crear nuevo proyecto: "SIRCCD - Wireframes"
   - Configurar frames por plataforma:
     - iPhone 14 Pro (430×932) para App Ciudadano/Operador
     - Desktop HD (1920×1080) para Dashboard Municipal
   - Configurar grid: 8px base unit

2. **Crear Design System:**
   - **Variables de color** (Settings → Variables):
     - primary-blue: #2563eb
     - critical-red: #dc2626
     - high-orange: #ea580c
     - etc. (usar tabla de Sección 1.2)
   
   - **Text Styles** (crear estilos para cada nivel):
     - heading-1 (Inter Bold 32px)
     - heading-2 (Inter Bold 24px)
     - body-regular (Inter Regular 16px)
     - etc.
   
   - **Components** (crear biblioteca reutilizable):
     - Buttons (con variantes: primary/secondary, sizes)
     - Cards (ReportCard, WorkOrderCard, MetricCard)
     - Forms (Input, Select, Checkbox, etc.)
     - Navigation (TopBar, BottomNav, Tabs)

3. **Crear wireframes:**
   - Usar componentes de la biblioteca
   - Agrupar elementos relacionados en frames
   - Nombrar capas descriptivamente
   - Usar Auto Layout para elementos flexibles

4. **Prototipar flujos:**
   - Conectar screens con links
   - Agregar interacciones (click, hover, scroll)
   - Configurar transiciones (instant, dissolve, smart animate)
   - Definir estados (default, hover, active, disabled)

5. **Exportar para desarrollo:**
   - **Specs**: Usar Inspect panel (código CSS/React/SwiftUI)
   - **Assets**: Exportar iconos en SVG, imágenes en PNG/WebP
   - **Design tokens**: Exportar variables a JSON (plugin "Design Tokens")
   - **Handoff**: Compartir link con modo "Dev Mode" activado

**Plugins recomendados:**
- **Iconify**: Integración con Lucide Icons
- **Design Tokens**: Exportar variables a código
- **Auto Layout**: Helpers para responsive design
- **Contrast**: Verificar accesibilidad de colores
- **A11y - Focus Orderer**: Definir orden de navegación

### 6.2 Guía para Penpot (Alternativa Open Source)

**Pasos para crear el diseño en Penpot:**

1. **Configuración inicial:**
   - Crear nuevo proyecto: "SIRCCD - Wireframes"
   - Configurar boards (equivalente a frames):
     - Mobile: 430×932
     - Desktop: 1920×1080
   - Grid: 8px square grid

2. **Crear bibliotecas:**
   - **Paleta de colores** (Assets → Colors):
     - Agregar todos los colores de la Sección 1.2
   
   - **Tipografías** (Assets → Typography):
     - Importar fuentes Inter y JetBrains Mono
     - Crear estilos de texto
   
   - **Componentes** (Create Component):
     - Buttons, Cards, Forms, etc.
     - Usar "Component Variants" para estados

3. **Implementar wireframes:**
   - Usar sistema de grids y guías
   - Crear layouts con Flexbox (equivalente a Auto Layout)
   - Agrupar elementos lógicamente
   - Nombrar capas con convención: `Category/Name`

4. **Prototipar:**
   - Usar Flow tool para conectar screens
   - Configurar interacciones en Interactions panel
   - Definir hotspots para elementos clicables
   - Preview en navegador para testing

5. **Exportar:**
   - **Code**: Export → CSS/SVG
   - **Assets**: Export → PNG/SVG (individual o batch)
   - **Sharing**: Generate public link para handoff
   - **Specs**: Usar View mode para desarrolladores

**Ventajas de Penpot:**
- 100% open source y gratuito
- Basado en estándares web (SVG)
- Colaboración en tiempo real
- Auto-guardado en navegador
- No vendor lock-in

### 6.3 Entrega a Desarrollo

**Estructura de entrega:**

```
/designs
  /figma (o /penpot)
    link-to-project.txt
  /assets
    /icons
      - lucide-icons.zip
    /images
      - placeholder-images/
    /logos
      - municipio-logo.svg
  /design-tokens
    - colors.json
    - typography.json
    - spacing.json
  /specs
    - component-library.pdf
    - responsive-breakpoints.md
    - accessibility-checklist.md
```

**Checklist de entrega:**
- [ ] Todos los wireframes completos (30 screens)
- [ ] Design system documentado
- [ ] Componentes reutilizables creados
- [ ] Prototipos funcionales con navegación
- [ ] Design tokens exportados a JSON
- [ ] Assets exportados (iconos, imágenes)
- [ ] Documentación de accesibilidad
- [ ] Especificaciones responsive
- [ ] Guía de implementación para devs

---

## 7. Resumen y Próximos Pasos

### 7.1 Inventario de Wireframes Creados

**App Ciudadano (12 wireframes):**
1. Splash screen
2-4. Onboarding (3 slides)
5. Login
6. Registro
7. Home/Dashboard
8-11. Crear reporte (wizard 4 pasos)
12. Detalle de reporte
13. Mapa con filtros
14. Lista de reportes
15. Notificaciones

**App Operador (6 wireframes):**
16. Login
17. Dashboard
18. Lista de reportes asignados
19. Detalle de reporte
20. Actualizar estado (marcar resuelto)
21. Ruta del día optimizada

**Dashboard Municipal (10 wireframes):**
23. Login
24. Dashboard principal
25. Vista de mapa
26. Tabla de reportes
27. Detalle de reporte (operador)
28. Panel de métricas/analytics
29. Configuración - Score
30. Configuración - Categorías

**Total: 30+ wireframes completos**

### 7.2 Próximos Pasos Recomendados

1. **Fase de Diseño (2-3 semanas):**
   - Crear diseños de alta fidelidad en Figma/Penpot
   - Validar flujos con stakeholders
   - Testing de usabilidad con usuarios reales
   - Ajustes según feedback

2. **Fase de Desarrollo Frontend (6-8 semanas):**
   - Implementar design system (componentes base)
   - Desarrollo de App Ciudadano (React Native/Flutter)
   - Desarrollo de App Operador (React Native/Flutter)
   - Desarrollo de Dashboard Municipal (React/Vue)

3. **Fase de Integración (2-3 semanas):**
   - Conectar con backend APIs
   - Integrar modelo ML de clasificación
   - Implementar sistema de notificaciones
   - Pruebas de integración

4. **Fase de Testing (2 semanas):**
   - QA funcional
   - Testing de accesibilidad
   - Performance testing
   - Security testing

5. **Piloto y Lanzamiento (1-2 semanas):**
   - Despliegue en ambiente de staging
   - Piloto con equipo seleccionado
   - Ajustes finales
   - Lanzamiento a producción

---

## Apéndice

### A. Referencias de Diseño

**Inspiración de UX/UI:**
- **Waze**: Reportes colaborativos de incidentes
- **SeeClickFix**: App cívica de reportes municipales
- **Citizen**: Alertas y reportes de seguridad
- **Google Maps**: Navegación y visualización de incidentes

**Guías de diseño:**
- [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)
- [Material Design 3](https://m3.material.io/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

### B. Herramientas Recomendadas

**Diseño:**
- Figma / Penpot (wireframes y prototipos)
- Lucide Icons (biblioteca de iconos)
- Coolors.co (generador de paletas)

**Desarrollo:**
- React Native / Flutter (apps móviles)
- React / Vue (dashboard web)
- Leaflet / Mapbox (mapas)
- TailwindCSS (estilos)

**Testing:**
- Lighthouse (performance y accesibilidad)
- axe DevTools (accesibilidad)
- BrowserStack (testing cross-browser)

---

**Fin del documento de wireframes completo**

*Creado: 14 de enero de 2026*  
*Versión: 1.0*  
*Proyecto: SIRCCD - Sistema Inteligente de Reportes Ciudadanos de Calles Dañadas*
