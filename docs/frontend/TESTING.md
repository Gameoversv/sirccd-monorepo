# Pruebas — Frontend

[← Volver al índice](../README.md)

## Framework

Playwright (`playwright.config.ts`): directorio `tests/`, `baseURL http://localhost:3001`, navegador Chromium únicamente, capturas de pantalla en fallos.

## Cobertura actual

**Un único spec**: `tests/portal.spec.ts` ("Portal ciudadano"), cubre:

- Redirección de login como ciudadano.
- Visibilidad del logo.
- Cambio de idioma (ES/EN).
- Cambio de tema (claro/oscuro).
- Saludo con nombre de usuario.
- CTA de "reportar" y navegación al formulario de nuevo reporte.
- Sección "Mis Reportes".
- Logout y redirección.

**No hay pruebas del dashboard** (`/dashboard/*`) ni pruebas unitarias/de componentes — solo el flujo del portal ciudadano está cubierto automáticamente.

## Ejecución

```bash
cd frontend
npx playwright test                 # correr toda la suite
npx playwright test --ui             # modo interactivo
npx playwright show-report           # ver el último reporte HTML
```

Requiere el frontend corriendo en `http://localhost:3001` (puerto distinto del de desarrollo normal, 3000 — confirmar el puerto correcto al ejecutar localmente, posible desalineación con `npm run dev` que por defecto usa 3000).

## Limitaciones conocidas

- Sin cobertura automatizada del dashboard operativo — la superficie usada por supervisores/administradores no tiene ninguna prueba E2E ni unitaria.
- Sin pruebas unitarias de utilidades (`src/utils/`, `src/lib/`) ni de hooks (`src/hooks/`).
- Sin CI que ejecute esta suite automáticamente (ver [../infrastructure/CI_CD.md](../infrastructure/CI_CD.md)) — depende de ejecución manual.
