# Modulo Frontend

## 1. Proposito del modulo

El frontend implementa el dashboard web de operacion municipal para SIRCCD. Permite a operadores y administradores:

1. **Autenticarse** y controlar acceso segun rol.
2. **Visualizar reportes e incidentes** en mapa geoespacial interactivo con heatmaps.
3. **Gestionar flujos de trabajo**: actualizar estados, asignar prioridades, fusionar reportes.
4. **Monitorear KPIs** mediante graficos y metricas en tiempo real.
5. **Filtrar y buscar** reportes/incidentes por tipo, severidad, estado, fecha y area.
6. **Exportar datos** en CSV y GeoJSON.
7. **Administrar usuarios** del sistema (solo admin).
8. **Operar en espanol e ingles** con cambio de idioma en tiempo real.

## 2. Stack tecnologico

| Componente | Tecnologia | Version | Proposito |
|-----------|------------|---------|-----------|
| Framework | Next.js (App Router) | 14.1+ | Server-side rendering, routing, layouts |
| UI Library | React | 18.2+ | Componentes de interfaz reactivos |
| Lenguaje | TypeScript | 5.3+ | Tipado estatico para mantenibilidad |
| Estilos | Tailwind CSS | 3.4+ | Utility-first CSS responsive |
| PostCSS | postcss | - | Procesamiento de CSS |
| Estado global | Zustand | 4.5+ | Estado compartido ligero y desacoplado |
| HTTP Client | Axios | 1.6+ | Comunicacion con backend REST API |
| Mapas | React Leaflet | 4.2+ | Visualizacion geoespacial interactiva |
| Graficos | Recharts | 3.7+ | Graficos y KPIs del dashboard |
| i18n | i18next + react-i18next | 25.8+ | Internacionalizacion ES/EN |
| Linting | ESLint | - | Calidad y consistencia de codigo |

## 3. Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                      App Router (Next.js)                    │
│  Rutas, layouts, proteccion de rutas, SSR/CSR               │
├─────────────────────────────────────────────────────────────┤
│                        Components                            │
│  MapView, HeatmapLayer, FilterPanel, IncidentsTable,         │
│  StatusTimeline, LocationPicker, ImageUpload, Toast, etc.    │
├────────────────────────┬────────────────────────────────────┤
│      Services          │           Store (Zustand)           │
│  (API client layer)    │  authStore, reportsStore,           │
│  api.ts, authService,  │  incidentsStore, uiStore            │
│  reportsService, etc.  │                                     │
├────────────────────────┴────────────────────────────────────┤
│               Hooks / Utils / Types / i18n                   │
│  useAuth, useAsync, useToast, useMediaQuery                  │
│  geo.ts, dates.ts, labels.ts, cn.ts                          │
└─────────────────────────────────────────────────────────────┘
```

### 3.1 Principios de diseno

- **Componentes pequenos y reutilizables**: cada componente tiene una responsabilidad unica.
- **Servicios API centralizados**: toda comunicacion HTTP pasa por `services/`, nunca se llama Axios directo desde componentes.
- **Estado desacoplado**: Zustand stores son independientes de las vistas, se consumen via hooks.
- **Tipos compartidos**: todas las interfaces de dominio en `types/` para consistencia.
- **Utilidades separadas**: funciones puras de formateo, calculo y transformacion en `utils/`.

## 4. Mapa de archivos y directorios

### 4.1 Rutas y vistas (`src/app/`)

| Archivo/Directorio | Descripcion |
|-------------------|-------------|
| `app/layout.tsx` | Layout raiz: providers (i18n, auth), estilos globales, metadata |
| `app/page.tsx` | Pagina de entrada: redirige a login o dashboard segun sesion |
| `app/login/page.tsx` | Formulario de login: email + password, validacion, error handling |
| `app/register/page.tsx` | Formulario de registro de ciudadano |
| `app/dashboard/page.tsx` | Dashboard principal: KPIs, graficos resumen, actividad reciente |
| `app/dashboard/reports/page.tsx` | Vista de gestion de reportes: tabla + filtros + detalle |
| `app/dashboard/incidents/page.tsx` | Vista de gestion de incidentes: tabla + filtros + detalle |
| `app/dashboard/map/page.tsx` | Vista de mapa completa: mapa + heatmap + filtros + marcadores |
| `app/dashboard/admin/page.tsx` | Panel de administracion: gestion de usuarios |

### 4.2 Componentes UI (`src/components/`)

| Componente | Descripcion |
|-----------|-------------|
| `MapView.tsx` | **Mapa principal** (Leaflet): renderiza marcadores de reportes (coloreados por severidad) e incidentes (icono diferenciado). Soporta clusters para alta densidad, popups con detalle al click, y sincronizacion con filtros del FilterPanel |
| `HeatmapLayer.tsx` | **Capa de calor** superpuesta al mapa: muestra densidad de reportes/incidentes. Util para identificar zonas criticas y patrones espaciales |
| `FilterPanel.tsx` | **Panel de filtros** lateral: tipo de dano, rango de severidad, estado, rango de fechas, area geografica. Los filtros se aplican reactivamente a tablas y mapa |
| `IncidentsTable.tsx` | **Tabla operativa** de incidentes: columnas (ID, tipo, severidad, estado, prioridad, reportes, fecha), ordenamiento por columna, paginacion, acciones inline |
| `StatusTimeline.tsx` | **Timeline de estados**: muestra historial de cambios de estado de un reporte/incidente con timestamps y usuario responsable |
| `StatusUpdateModal.tsx` | **Modal de actualizacion**: formulario para cambiar estado de un incidente con comentario opcional |
| `LocationPicker.tsx` | **Selector de ubicacion**: mapa interactivo para elegir coordenadas con click o arrastre de marcador |
| `ImageUpload.tsx` | **Upload de imagenes**: drag-and-drop o click, preview, validacion de formato y tamano |
| `I18nProvider.tsx` | **Provider de i18n**: envuelve la app con contexto de internacionalizacion |
| `LanguageSwitcher.tsx` | **Selector de idioma**: toggle ES/EN en la barra de navegacion |
| `Button.tsx` | Boton base con variantes (primary, secondary, danger, ghost) y estados (loading, disabled) |
| `Card.tsx` | Tarjeta contenedora reutilizable con header, body y footer opcionales |
| `Toast.tsx` | Sistema de notificaciones tipo toast: success, error, warning, info |
| `MiniMap.tsx` | Mapa miniatura para vistas de detalle (solo lectura, sin interaccion) |

### 4.3 Servicios API (`src/services/`)

| Archivo | Descripcion |
|---------|-------------|
| `api.ts` | **Cliente HTTP base**: instancia Axios con baseURL, interceptors para JWT (inyeccion automatica de Bearer token), interceptor de refresh automatico en 401, manejo de errores global |
| `authService.ts` | `login(email, password)`, `register(data)`, `refreshToken()`, `getProfile()` |
| `reportsService.ts` | `getReports(filters, page)`, `createReport(formData)`, `getReport(id)`, `updateReport(id, data)`, `deleteReport(id)` |
| `incidentsService.ts` | `getIncidents(filters, page)`, `getIncident(id)`, `updateIncident(id, data)`, `mergeReports(id, reportIds)` |
| `metricsService.ts` | `getDashboardMetrics()`, `getKPIs(dateRange)` |
| `poisService.ts` | `getNearbyPOIs(lat, lng, radius)` |
| `usersService.ts` | `getUsers(filters)`, `getUser(id)`, `updateUser(id, data)`, `deleteUser(id)` |

### 4.4 Estado global (`src/store/`)

#### authStore.ts - Sesion del usuario
```typescript
{
  user: User | null,          // Perfil del usuario autenticado
  token: string | null,       // Access token JWT
  refreshToken: string | null,// Refresh token
  isAuthenticated: boolean,   // Derivado: !!token
  login(email, password): Promise<void>,
  logout(): void,
  refreshAccessToken(): Promise<void>,
  setUser(user): void
}
```

#### reportsStore.ts - Reportes
```typescript
{
  reports: Report[],          // Lista actual de reportes
  total: number,              // Total de resultados (paginacion)
  filters: ReportFilters,     // Filtros activos
  loading: boolean,           // Estado de carga
  fetchReports(): Promise<void>,
  setFilters(filters): void,
  clearFilters(): void
}
```

#### incidentsStore.ts - Incidentes
```typescript
{
  incidents: Incident[],      // Lista actual de incidentes
  total: number,
  filters: IncidentFilters,
  loading: boolean,
  fetchIncidents(): Promise<void>,
  updateStatus(id, status): Promise<void>,
  setFilters(filters): void
}
```

#### uiStore.ts - Estado de UI
```typescript
{
  sidebarOpen: boolean,       // Sidebar lateral abierto/cerrado
  activeModal: string | null, // Modal activo (nombre)
  theme: 'light' | 'dark',   // Tema visual
  toggleSidebar(): void,
  openModal(name): void,
  closeModal(): void
}
```

### 4.5 Hooks reutilizables (`src/hooks/`)

| Hook | Descripcion |
|------|-------------|
| `useAuth.ts` | **Proteccion de rutas**: verifica sesion activa, redirige a `/login` si no autenticado. Verifica rol minimo para rutas admin |
| `useAsync.ts` | **Flujo asincrono**: encapsula estado `{data, loading, error}` para llamadas async. Evita duplicar logica de loading/error en componentes |
| `useToast.ts` | **Notificaciones**: expone `showToast(type, message)` para feedback visual al usuario |
| `useMediaQuery.ts` | **Responsive**: retorna boolean para breakpoints de Tailwind. Usado para adaptar layout en mobile vs desktop |

### 4.6 Utilidades (`src/utils/`)

| Archivo | Descripcion |
|---------|-------------|
| `geo.ts` | Utilidades geoespaciales: calculo de distancia, formato de coordenadas, bounding box, conversion de unidades |
| `dates.ts` | Formateo de fechas: relative time ("hace 2h"), formato local, rangos de fecha, parsing |
| `labels.ts` | Traduccion de labels de dominio: mapea enums del backend (damage_type, status) a texto legible en el idioma activo |
| `cn.ts` | Merge de clases CSS: combina clases Tailwind de forma segura (wrapper sobre clsx/tailwind-merge) |
| `index.ts` | Re-exportaciones y tipos compartidos entre utilidades |

### 4.7 Internacionalizacion (`src/i18n/`)

Archivos de traduccion JSON para espanol (ES) e ingles (EN). Estructura de keys organizada por seccion:

```
dashboard.title
dashboard.reports
dashboard.incidents
reports.create
reports.status.pending
reports.status.processing
incidents.priority.high
auth.login
auth.register
common.save
common.cancel
common.delete
```

### 4.8 Tipos TypeScript (`src/types/`)

Definiciones de interfaces y tipos de dominio usados en toda la aplicacion:

- `User`, `UserRole`
- `Report`, `ReportStatus`, `ReportFilters`
- `Incident`, `IncidentStatus`, `IncidentFilters`
- `POI`, `POICategory`
- `DashboardMetrics`, `KPI`
- `PaginatedResponse<T>`
- `ApiError`

### 4.9 Configuracion del modulo

| Archivo | Descripcion |
|---------|-------------|
| `package.json` | Dependencias (17+), scripts (dev, build, start, lint, type-check) |
| `next.config.js` | Configuracion Next.js: redirects, rewrites, image domains, env vars |
| `tailwind.config.js` | Configuracion Tailwind: colores custom, breakpoints, plugins |
| `postcss.config.js` | Plugins PostCSS: tailwindcss, autoprefixer |
| `tsconfig.json` | Configuracion TypeScript: paths, strict mode, target |
| `.eslintrc.json` | Reglas de linting: extends next/core-web-vitals |
| `.env.example` | Ejemplo de variables de entorno |
| `.env.local` | Variables locales (no commiteado) |
| `Dockerfile` | Imagen Docker para despliegue |
| `docs/W-04-MAPA-IMPLEMENTACION.md` | Documentacion detallada de la implementacion del mapa Leaflet |

## 5. Flujos funcionales principales

### 5.1 Flujo de autenticacion

```
1. Usuario accede a /login
2. Ingresa email + password
3. authService.login() → POST /api/auth/login
4. Backend valida → {access_token, refresh_token}
5. authStore guarda tokens y perfil
6. Axios interceptor adjunta "Authorization: Bearer <token>" a cada request
7. useAuth hook protege rutas del dashboard
8. Si token por expirar → authService.refreshToken() automatico
9. Si refresh falla → logout + redirect a /login
```

### 5.2 Flujo de visualizacion de mapa

```
1. Operador accede a /dashboard/map
2. incidentsStore.fetchIncidents() carga datos
3. MapView renderiza mapa Leaflet con tile layer
4. Marcadores de incidentes se posicionan por lat/lng
5. HeatmapLayer calcula y renderiza densidad
6. FilterPanel permite filtrar por tipo, severidad, estado
7. Al filtrar → store actualiza → mapa re-renderiza marcadores
8. Click en marcador → popup con detalle del incidente
9. Click en "Ver detalle" → navega a vista de incidente
```

### 5.3 Flujo de gestion de incidentes

```
1. Operador accede a /dashboard/incidents
2. IncidentsTable carga y muestra lista paginada
3. FilterPanel permite refinar busqueda
4. Click en incidente → detalle con reportes asociados
5. StatusTimeline muestra historial de estados
6. Operador click "Actualizar estado" → StatusUpdateModal
7. Selecciona nuevo estado + comentario → PATCH /api/incidents/{id}
8. Store actualiza → tabla y mapa reflejan cambio
9. Toast confirma accion exitosa
```

### 5.4 Flujo de exportacion

```
1. Operador configura filtros en dashboard
2. Click en "Exportar CSV" o "Exportar GeoJSON"
3. Service llama GET /api/export/csv o /geojson con filtros
4. Backend genera archivo → respuesta como descarga
5. Navegador descarga el archivo
```

## 6. Paginacion y filtros

### 6.1 Formato de request

```
GET /api/reports?page=1&page_size=20&status=classified&damage_type=pothole&sort_by=created_at&sort_order=desc
```

### 6.2 Formato de respuesta paginada

```json
{
  "data": [...],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

### 6.3 Filtros soportados

| Filtro | Tipo | Aplica a |
|--------|------|----------|
| `status` | enum | Reportes, Incidentes |
| `damage_type` | string | Reportes, Incidentes |
| `severity_min` / `severity_max` | float | Reportes |
| `priority_min` / `priority_max` | float | Incidentes |
| `date_from` / `date_to` | ISO date | Ambos |
| `lat`, `lng`, `radius` | float | Ambos (area geografica) |
| `sort_by` | string | Ambos |
| `sort_order` | asc/desc | Ambos |

## 7. Ejecucion local

```powershell
cd frontend
npm install        # Instalar dependencias
npm run dev        # Servidor de desarrollo (http://localhost:3000)
npm run build      # Build de produccion
npm run start      # Servidor de produccion
npm run lint       # Verificar reglas de linting
npm run type-check # Verificar tipos TypeScript
```

### Variables de entorno requeridas (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_DEFAULT_LOCALE=es
```

## 8. Integraciones

| Sistema | Mecanismo | Datos |
|---------|-----------|-------|
| Backend | REST API + JWT | Reportes, incidentes, auth, metricas, POIs, usuarios |
| Leaflet Tile Server | HTTPS (OpenStreetMap) | Tiles de mapa base |
| Backend Auth | JWT tokens | Access token en header, refresh automatico |
| Backend Export | REST API (descarga) | Archivos CSV y GeoJSON |
