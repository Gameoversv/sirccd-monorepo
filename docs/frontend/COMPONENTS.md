# Componentes

[← Volver al índice](../README.md)

18 componentes en `src/components/` (tras la limpieza que eliminó `Button.tsx`, `Card.tsx`, `SLAPanel.tsx` y el barrel `index.ts` por falta de uso — ver [../REPOSITORY_AUDIT.md](../REPOSITORY_AUDIT.md#10-estado-de-git-pendiente-de-cerrar)).

| Componente | Archivo | Responsabilidad | Props clave | Usado en |
|---|---|---|---|---|
| `FilterPanel` | `FilterPanel.tsx` | Panel lateral colapsable de filtros de incidentes (severidad, rango de score de prioridad, estado, capas POI, zona, rango de fechas) | `filters`, `onChange`, `onClear`, `total`, `poiLayerFilters`, `onPoiLayerFiltersChange` | `dashboard/incidents/page.tsx` |
| `HeatmapLayer` | `HeatmapLayer.tsx` | Wrapper de react-leaflet que añade overlay de mapa de calor (`leaflet.heat`) | `points: [lat,lng,intensity][]`, `visible` | `MapView.tsx` |
| `I18nProvider` | `I18nProvider.tsx` | Envuelve la app en `I18nextProvider`, sincroniza `<html lang>` con el idioma activo | `children` | `app/layout.tsx` |
| `ImageUpload` | `ImageUpload.tsx` | Selector de imagen (drag/drop o click); ejecuta chequeo de privacidad rostro/placa (`reportsService.verifyImage`) y extrae GPS de EXIF | `value`, `onChange`, `error`, `onExifLocation` | `dashboard/reports/new/page.tsx` |
| `IncidentsTable` | `IncidentsTable.tsx` | Tabla de incidentes ordenable/paginada con badges de severidad/prioridad/estado/SLA | `incidents`, `page`, `totalPages`, `total`, `isLoading`, `onPageChange`, `onSort`, `sortField`, `sortDir` | `dashboard/incidents/page.tsx` |
| `LanguageSwitcher` | `LanguageSwitcher.tsx` | Botón de cambio de idioma ES/EN, persiste en localStorage | `className?` | `login`, `register`, `PortalTopbar`, `Topbar` |
| `LocationPicker` | `LocationPicker.tsx` | Botón de geolocalización + inputs numéricos lat/lng con callback de geocodificación inversa | `value`, `onChange`, `onAddressResolved`, `latError`, `lngError`, `locationSource` | `dashboard/reports/new/page.tsx` |
| `MapView` | `MapView.tsx` | Mapa completo de incidentes: marcadores coloreados por prioridad, toggle de mapa de calor, capa de POIs + radios de riesgo, leyenda | `height`, `center`, `zoom`, `filters`, `poiLayerFilters`, `onIncidentsLoaded` | `dashboard/incidents/page.tsx` (import dinámico, `ssr:false`) |
| `MiniMap` | `MiniMap.tsx` | Mapa Leaflet pequeño, estático, de un solo marcador (no interactivo) | `lat`, `lng`, `label?`, `height?`, `zoom?` | `dashboard/incidents/[id]`, `dashboard/reports/new`, `dashboard/reports`, `portal` (todos import dinámico) |
| `PortalMap` | `PortalMap.tsx` | Mapa multi-marcador centrado en el promedio de coordenadas de los reportes propios del ciudadano | `markers: {id,lat,lng,label?}[]`, `height?` | `portal/page.tsx` (import dinámico) |
| `PortalTopbar` | `PortalTopbar.tsx` | Header del portal ciudadano: logo, toggles de idioma/tema, avatar de usuario, logout | (usa `useAuthStore` directamente) | `portal/layout.tsx` |
| `Sidebar` | `Sidebar.tsx` | Navegación lateral del dashboard; filtra ítems por `user.role` (Usuarios/Configuración restringidos) | — | `dashboard/layout.tsx` |
| `SLABadge` | `SLABadge.tsx` | Píldora de color según estado de SLA (on_track/warning/overdue/completed/not_started), con texto opcional de horas restantes | `status: SLAStatus`, `hoursRemaining?`, `compact?` | `dashboard/incidents/[id]`, `dashboard/sla`, `IncidentsTable` |
| `StatusTimeline` | `StatusTimeline.tsx` | Línea de tiempo vertical de auditoría/hitos de un incidente (usa timestamps de hitos si no hay log de auditoría) | `incident`, `auditLog?: AuditLogEntry[]` | `dashboard/incidents/[id]/page.tsx` |
| `StatusUpdateModal` | `StatusUpdateModal.tsx` | Modal de transición de estado de incidente (usa el mapa `STATUS_TRANSITIONS`) con campo de notas | `incidentId`, `currentStatus`, `onClose`, `onSuccess`, `onSubmit` | `dashboard/incidents/[id]/page.tsx` |
| `ThemeToggle` | `ThemeToggle.tsx` | Botón de tema claro/oscuro, persiste en localStorage (`sirccd-theme`) | `className?` | `login`, `register`, `PortalTopbar`, `Topbar` |
| `Toast` / `ToastContainer` | `Toast.tsx` | Pila global de notificaciones toast, alimentada por `useUIStore.toasts` | `ToastContainer` sin props; `Toast` interno: `id`,`type`,`message`,`duration`,`onClose` | `app/layout.tsx` |
| `Topbar` | `Topbar.tsx` | Header del dashboard: buscador, toggles de idioma/tema, avatar+rol, logout | — | `dashboard/layout.tsx` |

## Utilidades relacionadas (no son componentes, pero soportan a varios)

- `src/utils/labels.ts` — funciones de color/etiqueta usadas por `MapView`, `IncidentsTable`, `FilterPanel`, `StatusTimeline`, `StatusUpdateModal` (ver nota de limpieza en [../REPOSITORY_AUDIT.md](../REPOSITORY_AUDIT.md#6-código-potencialmente-obsoleto)).
- `src/lib/exifGps.ts`, `src/lib/geocode.ts` — usados por `ImageUpload`/`LocationPicker` para extracción GPS y geocodificación.
