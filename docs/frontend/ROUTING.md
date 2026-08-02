# Rutas

[← Volver al índice](../README.md)

Protección de rutas 100% del lado cliente (sin `middleware.ts` de Next.js) — ver [../SECURITY.md](../SECURITY.md).

| Ruta | Archivo | Nivel de acceso | Descripción | Parámetros |
|---|---|---|---|---|
| `/` | `src/app/page.tsx` | público (gate de redirección) | Pantalla de carga que redirige a `/login` (sin sesión) o `/portal`/`/dashboard` según `user.role` | — |
| `/login` | `src/app/login/page.tsx` | público | Formulario de login (username/password) | — |
| `/register` | `src/app/register/page.tsx` | público | Registro de ciudadano (`authService.register`) | — |
| `/guia` | `src/app/guia/page.tsx` | público | Guía de usuario del portal ciudadano, accesible sin sesión. Versión web de [../MANUAL_USUARIO.md](../MANUAL_USUARIO.md) | — |
| `/portal` | `src/app/portal/page.tsx` (+ `layout.tsx`) | ciudadano (`UserRole.CIUDADANO`; el layout redirige a no-ciudadanos a `/dashboard`) | Feed personal de reportes: tarjetas de estadísticas, reportes paginados, modal de detalle, mapa de reportes propios | — |
| `/dashboard` | `src/app/dashboard/page.tsx` (+ `layout.tsx`) | supervisor/admin/staff (el layout llama `useAuth()`; ciudadanos son enviados a `/portal`) | Dashboard de KPIs: conteos de incidentes, cumplimiento de SLA, gráficos de estado/prioridad (Recharts) | — |
| `/dashboard/incidents` | `src/app/dashboard/incidents/page.tsx` | supervisor/admin/staff | Lista/mapa/vista dividida de incidentes con filtros, tabla, exportación CSV/GeoJSON/KPI/PDF | — |
| `/dashboard/incidents/[id]` | `src/app/dashboard/incidents/[id]/page.tsx` | lectura: cualquier usuario del dashboard; actualización de estado: solo supervisor/admin | Detalle de incidente: fotos, desglose de score de prioridad, estado de SLA, línea de tiempo de auditoría, modal de actualización de estado | `[id]` id de incidente |
| `/dashboard/reports` | `src/app/dashboard/reports/page.tsx` | lectura: cualquier usuario del dashboard; aprobar/rechazar: solo supervisor/admin | Tabla de reportes con filtros, modal de detalle con acciones de revisión | — |
| `/dashboard/reports/new` | `src/app/dashboard/reports/new/page.tsx` | cualquier usuario autenticado (ciudadano o staff) | Formulario de nuevo reporte: subida de imagen con chequeo EXIF/privacidad, selector de ubicación, campos de dirección, descripción | — |
| `/dashboard/sla` | `src/app/dashboard/sla/page.tsx` | supervisor/admin (panel de configuración solo admin) | Monitoreo de SLA: listas de incidentes vencidos/por vencer; `SLAConfigPanel` editable solo si `user.role === UserRole.ADMIN` | — |
| `/dashboard/users` | `src/app/dashboard/users/page.tsx` | supervisor/admin (vista); admin (crear/editar/desactivar/eliminar) | Tabla de gestión de usuarios; `isAdmin` controla todas las acciones de mutación | — |
| `/dashboard/settings` | `src/app/dashboard/settings/page.tsx` | admin (`UserRole.ADMIN` únicamente; otros ven aviso "solo admin") | Editor de pesos de priorización (severidad/antigüedad/tipo de daño/ubicación/duplicados) y radios de POI/duplicados/clustering | — |

## Layouts

- `src/app/layout.tsx` — raíz: `I18nProvider` + `ToastContainer`.
- `src/app/dashboard/layout.tsx` — renderiza `Sidebar` + `Topbar`, aplica `useAuth()` como guardia de acceso.
- `src/app/portal/layout.tsx` — renderiza `PortalTopbar`, redirige según rol usando `useAuthStore` directamente.
