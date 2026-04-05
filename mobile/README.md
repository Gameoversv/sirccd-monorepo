# Mobile SIRCCD

Modulo de app movil ciudadana para reporte en campo.

## 1) Estado actual

El modulo esta en estado scaffold minimo:

- mobile/assets/
- mobile/lib/

Todavia no existe un proyecto Flutter completo inicializado.

## 2) Objetivo funcional

La app movil debe permitir:

1. login/registro ciudadano,
2. crear reporte con camara/galeria,
3. capturar geolocalizacion,
4. enviar reporte al backend,
5. consultar estado de reportes enviados.

## 3) Donde ira cada cosa (propuesta)

Estructura recomendada para `lib/`:

- features/auth/
- features/reports/
- features/profile/
- shared/services/
- shared/widgets/
- shared/state/

## 4) Integraciones requeridas

- autenticacion y reportes contra backend.
- manejo de token y reintento de envios.
- soporte offline para reportes pendientes.

## 5) Documentacion oficial

- ../docs/mobile.md
- ../docs/monorepo.md
- ../docs/README.md
