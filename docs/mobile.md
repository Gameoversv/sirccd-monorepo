# Modulo Mobile

## 1) Proposito del modulo

Mobile sera la aplicacion ciudadana para reportar danos viales desde campo.

Objetivos funcionales esperados:

1. login/registro de ciudadano,
2. captura de imagen (camara/galeria),
3. captura de ubicacion,
4. envio de reporte al backend,
5. seguimiento del estado del reporte.

## 2) Estado actual

El modulo existe como scaffold minimo y no tiene app Flutter completa inicializada.

## 3) Donde esta cada cosa

- `mobile/assets/`: recursos estaticos (placeholder).
- `mobile/lib/`: espacio para codigo fuente Flutter (placeholder).

## 4) Arquitectura recomendada para implementacion

### Estructura sugerida de `lib/`

1. `features/auth/`
2. `features/reports/`
3. `features/profile/`
4. `shared/services/`
5. `shared/widgets/`
6. `shared/state/`

### Recomendaciones de implementacion

1. separar UI, estado y acceso API.
2. incluir estrategia offline-first para reportes pendientes.
3. integrar permisos de camara y geolocalizacion de forma robusta.
4. desacoplar modelos DTO de modelos de UI.

## 5) Integraciones

- consume autenticacion y endpoints de reportes del backend.
- debe integrarse con pipeline de build/test en `infra/ci-cd/`.

## 6) Siguiente paso tecnico

1. inicializar proyecto Flutter real en esta carpeta.
2. definir convenciones de arquitectura y estado.
3. implementar primer flujo vertical: login -> crear reporte -> consultar estado.
