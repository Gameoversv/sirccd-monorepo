# Modulo Frontend

## 1) Proposito del modulo

Frontend implementa la aplicacion web de operacion municipal para:

1. autenticacion y control de acceso,
2. visualizacion de reportes/incidentes,
3. monitoreo de KPIs,
4. operacion geoespacial en mapa,
5. gestion administrativa desde UI.

## 2) Como se implemento

Se construyo sobre Next.js (App Router) con separacion de capas UI/estado/servicios:

- `app/` para rutas y vistas.
- `components/` para bloques reutilizables.
- `services/` para acceso HTTP al backend.
- `store/` para estado global con Zustand.
- `hooks/` para logica reutilizable de UI y flujo.
- `i18n/` para internacionalizacion.

Principios aplicados:

1. componentes pequenos y reusables,
2. servicios API centralizados,
3. estado compartido desacoplado de vistas,
4. utilidades y tipos separados para mantenibilidad.

## 3) Donde esta cada cosa

### 3.1 Rutas y vistas

- `src/app/layout.tsx`: layout raiz de la app.
- `src/app/page.tsx`: entrada principal.
- `src/app/login/`: flujo de login.
- `src/app/register/`: flujo de registro.
- `src/app/dashboard/`: vistas operativas de panel.

### 3.2 Componentes UI

Archivos relevantes en `src/components/`:

- `MapView.tsx`: mapa principal de incidentes/reportes.
- `HeatmapLayer.tsx`: capa de calor geoespacial.
- `FilterPanel.tsx`: filtros de busqueda.
- `IncidentsTable.tsx`: tabla operativa de incidentes.
- `StatusTimeline.tsx` y `StatusUpdateModal.tsx`: ciclo de estado.
- `LocationPicker.tsx`: seleccion de ubicacion.
- `ImageUpload.tsx`: carga de imagenes.
- `I18nProvider.tsx` y `LanguageSwitcher.tsx`: i18n en UI.
- `Button.tsx`, `Card.tsx`, `Toast.tsx`, `MiniMap.tsx`: UI reusable base.

### 3.3 Servicios API

Archivos en `src/services/`:

- `api.ts`: cliente base HTTP.
- `authService.ts`: autenticacion.
- `reportsService.ts`: reportes.
- `incidentsService.ts`: incidentes.
- `metricsService.ts`: metricas.
- `poisService.ts`: POIs.
- `usersService.ts`: administracion de usuarios.

### 3.4 Estado global

Archivos en `src/store/`:

- `authStore.ts`: sesion y usuario.
- `reportsStore.ts`: estado de reportes.
- `incidentsStore.ts`: estado de incidentes.
- `uiStore.ts`: estado de UI.

### 3.5 Hooks y utilidades

- `src/hooks/useAuth.ts`: proteccion de rutas.
- `src/hooks/useAsync.ts`: flujo asincrono.
- `src/hooks/useToast.ts`: notificaciones.
- `src/hooks/useMediaQuery.ts`: comportamiento responsive.
- `src/utils/geo.ts`: utilidades geoespaciales.
- `src/utils/dates.ts`: formateo de fechas.
- `src/utils/labels.ts`: traduccion de etiquetas de dominio.
- `src/utils/cn.ts`: combinacion de clases CSS.
- `src/types/index.ts`: tipos compartidos.

### 3.6 Configuracion del modulo

- `package.json`: dependencias y scripts.
- `next.config.js`: config de build/routing.
- `tailwind.config.js` y `postcss.config.js`: estilo.
- `.env.example` y `.env.local`: variables de entorno.
- `frontend/docs/W-04-MAPA-IMPLEMENTACION.md`: documentacion especifica del mapa.

## 4) Flujos funcionales principales

1. Usuario inicia sesion y obtiene token.
2. UI guarda contexto de auth en store.
3. Servicios consumen backend con token.
4. Vistas renderizan listas, mapas y metricas.
5. Operador ejecuta acciones de estado/gestion.

## 5) Ejecucion local

```powershell
cd frontend
npm install
npm run dev
```

Aplicacion local: `http://localhost:3000`

## 6) Scripts utiles

```powershell
npm run dev
npm run build
npm run start
npm run lint
npm run type-check
```

## 7) Integraciones

- frontend consume backend por REST.
- frontend usa token JWT para rutas protegidas.
- frontend visualiza resultados de dedup, prioridad e incidentes.
