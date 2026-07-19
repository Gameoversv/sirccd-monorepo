# Gestión de estado

[← Volver al índice](../README.md)

Zustand, 3 stores en `src/store/`, re-exportados desde `src/store/index.ts`.

## `authStore.ts` (`useAuthStore`) — persistido

Persistido vía `zustand/persist` en `localStorage`, clave `sirccd-auth-storage` (solo `user`/`token`/`isAuthenticated` se persisten).

| Campo | Descripción |
|---|---|
| `user` | Usuario actual o `null` |
| `token` | JWT actual o `null` |
| `isAuthenticated` | Booleano de sesión activa |
| `isLoading`, `error` | Estado de UI del flujo de login |
| `hasHydrated` | Indica si la rehidratación desde `localStorage` ya terminó — evita un falso logout al refrescar la página mientras Zustand aún no leyó el storage |

Acciones: `setUser`, `setHasHydrated`, `setToken`, `login(authResponse)` (construye `user` desde la respuesta de auth y guarda el token), `logout`, `setError`, `setLoading`, `clearError`.

## `incidentsStore.ts` (`useIncidentsStore`) — no persistido

| Campo | Descripción |
|---|---|
| `incidents` | Lista de incidentes cargados |
| `selectedIncident` | Incidente actualmente seleccionado |
| `filters` | Filtros activos (`IncidentFilters`) |
| `pagination` | `{page, per_page, total, total_pages}` |
| `isLoading`, `error` | Estado de UI |

Acciones: `setIncidents(paginatedResponse)`, `addIncident`, `updateIncident(id, partial)`, `deleteIncident(id)`, `setSelectedIncident`, `setFilters(partial)` (resetea `page` a 1), `clearFilters`, `setPage`, `setLoading`, `setError`, `clearError`.

## `uiStore.ts` (`useUIStore`) — no persistido

| Campo | Descripción |
|---|---|
| `isSidebarOpen` | Estado del sidebar del dashboard |
| `activeModal` / `modalData` | Modal global activo y sus datos |
| `toasts` | Cola de notificaciones toast |
| `mapFilters` | `{showReports, showIncidents, showPOIs, damageClasses, statuses, severities}` |
| `isMobileMenuOpen` | Menú móvil |
| `isGlobalLoading` | Loader global |

Acciones: `toggleSidebar`, `setSidebarOpen`, `openModal(id, data?)`, `closeModal`, `addToast(toast)` (genera id automáticamente), `removeToast(id)`, `setMapFilters(partial)`, `resetMapFilters`, `toggleMobileMenu`, `setMobileMenuOpen`, `setGlobalLoading`.

## Qué NO vive en Zustand

Los datos de servidor (reportes, usuarios) que no necesitan cachearse globalmente se cargan directamente en cada página vía los servicios (`src/services/`) y se guardan en estado local de React (`useState`) cuando el alcance es solo esa página — solo `incidentsStore` centraliza estado de servidor de forma global, y solo para incidentes.
