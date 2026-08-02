# Pruebas — Frontend

[← Volver al índice](../README.md)

## Framework

Playwright (`playwright.config.ts`): directorio `tests/`, Chromium únicamente, capturas en fallos. La `baseURL` sale de `E2E_BASE_URL` con `http://localhost:3001` por defecto. En CI (`process.env.CI`) se activan 2 reintentos, un solo worker, `forbidOnly`, vídeo en fallos, traza en el primer reintento y reportes `html` + `github`.

Las credenciales de los usuarios de prueba viven en `tests/helpers/auth.ts`, parametrizables por entorno (`E2E_CIUDADANO_USER`, `E2E_ADMIN_USER`, ...).

## Cobertura actual

### `tests/public.spec.ts` — superficies públicas

No dependen de datos sembrados: redirección de la raíz a `/login`, render de `/login` y `/register`, acceso a `/guia` sin sesión, rechazo de credenciales inválidas y bloqueo de `/dashboard` sin sesión.

### `tests/dashboard.spec.ts` — dashboard operativo

Requiere el admin sembrado. Login como admin, navegación a incidentes y reportes, gestión de usuarios y ajustes de priorización.

### `tests/portal.spec.ts` — portal ciudadano

Requiere el ciudadano sembrado. Cubre:

- Redirección de login como ciudadano.
- Visibilidad del logo.
- Cambio de idioma (ES/EN).
- Cambio de tema (claro/oscuro).
- Saludo con nombre de usuario.
- CTA de "reportar" y navegación al formulario de nuevo reporte.
- Sección "Mis Reportes".
- Logout y redirección.

## Ejecución

```bash
cd frontend
npm run test:e2e            # toda la suite
npm run test:e2e:ui         # modo interactivo
npm run test:e2e:report     # ver el último reporte HTML
```

### Requisitos para correrla en local

1. Backend arriba en `http://localhost:8000` con su base de datos migrada.
2. Frontend arriba en el puerto **3001**, no en el 3000 de `npm run dev`:
   ```bash
   npm run build && npm run start -- --port 3001
   ```
   Debe construirse con `NEXT_PUBLIC_API_URL` apuntando al backend: Next.js inlinea las `NEXT_PUBLIC_*` en tiempo de build, no de arranque.
3. Usuarios de prueba sembrados:
   ```bash
   cd backend
   ADMIN_USERNAME=test_admin ADMIN_EMAIL=test_admin@sirccd.test \
     ADMIN_PASSWORD='Test1234!' python -m scripts.seed_admin

   curl -X POST http://localhost:8000/api/v1/auth/register \
     -H 'Content-Type: application/json' \
     -d '{"email":"test_ciudadano@sirccd.test","username":"test_ciudadano","password":"Test1234!","full_name":"Juan Pérez"}'
   ```

Para apuntar a otro host: `E2E_BASE_URL=http://localhost:3000 npm run test:e2e`.

## Ejecución en CI

`.github/workflows/e2e-tests.yml` levanta el stack completo en cada push/PR a `main` o `dev` que toque `frontend/` o `backend/`: PostGIS y Redis como servicios, migraciones, backend con uvicorn, siembra de los dos usuarios, build y arranque del frontend en 3001, y `npx playwright test`. Publica el reporte HTML como artefacto siempre, y las trazas/vídeos solo en fallo.

Sin `ROBOFLOW_API_KEY` el backend usa el detector mock y, sin MinIO, `storage.py` cae a disco local — suficiente para estos flujos.

## Limitaciones conocidas

- Sin pruebas unitarias de utilidades (`src/utils/`, `src/lib/`) ni de hooks (`src/hooks/`).
- El E2E no cubre el flujo de creación de reporte con imagen real (subida + inferencia + deduplicación); solo llega al formulario.
- El dashboard se cubre a nivel de humo (render y navegación), sin aserciones sobre datos ni transiciones de estado de incidentes.
