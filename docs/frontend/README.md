# Frontend

[← Volver al índice](../README.md)

## Resumen

Aplicación Next.js 14 (App Router, TypeScript) que sirve dos superficies distintas desde el mismo proyecto: el **dashboard operativo** (`/dashboard/*`, para supervisores/administradores) y el **portal ciudadano** (`/portal`, para ciudadanos). Sin rutas API internas de Next.js — todo el acceso a datos va directo al backend FastAPI.

## Documentos

- [Rutas](ROUTING.md) — cada página, su nivel de acceso y propósito.
- [Componentes](COMPONENTS.md) — responsabilidad, props clave y dónde se usa cada uno.
- [Gestión de estado](STATE_MANAGEMENT.md) — los 3 stores de Zustand.
- [Integración con la API](API_INTEGRATION.md) — cada función de servicio y el endpoint que llama.
- [Pruebas](TESTING.md) — Playwright, qué cubre y qué no.

## Punto de entrada

`src/app/layout.tsx` (layout raíz) envuelve la app en `I18nProvider` + `ToastContainer`. `src/app/page.tsx` es una pantalla de carga/redirección: envía a `/login` si no hay sesión, o a `/portal`/`/dashboard` según `user.role`.

## Stack

Next.js 14 (App Router), TypeScript, Zustand (estado), Tailwind CSS (estilos), react-leaflet + leaflet.heat (mapas), recharts (gráficos), react-i18next (ES/EN), axios (HTTP).

## Comandos

```bash
cd frontend
npm install
npm run dev          # desarrollo, puerto 3000
npm run build         # build de producción
npm run type-check    # tsc --noEmit
npm run lint           # next lint
npx playwright test   # pruebas E2E
```

