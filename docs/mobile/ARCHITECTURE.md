# Arquitectura — Mobile

[← Volver al índice](../README.md)

## Estilo

Clean architecture por feature: cada feature en `lib/features/{nombre}/` se organiza en tres capas — `data/` (datasources, models, repositorios concretos), `domain/` (entidades, contratos de repositorio, casos de uso) y `presentation/` (cubits, páginas, widgets).

Features confirmadas: `auth`, `camera`, `permissions`, `profile`, `reports`.

## Estructura

```text
mobile/lib/
├── core/
│   ├── di/injection.dart          # Inyección de dependencias (get_it)
│   ├── errors/failures.dart       # Tipos de error de dominio
│   ├── network/backend_url.dart   # Configuración de URL del backend
│   └── services/                  # connectivity_service, database_service,
│                                   # permission_service, session_service
├── presentation/
│   ├── router/app_router.dart     # Definición de rutas (go_router)
│   ├── theme/                     # Tema visual
│   └── widgets/                   # Widgets compartidos
├── features/
│   ├── auth/{data,domain,presentation}/
│   ├── camera/
│   ├── permissions/
│   ├── profile/
│   └── reports/{data,domain,presentation}/
└── main.dart
```

## Navegación

`go_router` (`^14.8.1`), definido en `lib/presentation/router/app_router.dart`.

## Gestión de estado

`flutter_bloc` con patrón Cubit (no BLoC de eventos completo). Cada feature expone sus propios cubits en `presentation/cubit/` — confirmado en `auth` (`auth_cubit.dart` + `auth_state.dart`) y `reports`. `bloc_test` está entre las dependencias de desarrollo.

## Integración con el backend

- Cliente HTTP: `dio` (`^5.8.0`).
- Cada feature con acceso a red define su propio `*_remote_datasource.dart` (ej. `auth_remote_datasource.dart`), que llama al backend usando la URL configurada en `core/network/backend_url.dart`.
- El contrato de datos (JSON) debe mantenerse manualmente sincronizado con los schemas Pydantic del backend — no hay generación de tipos compartida entre Dart y Python.

## Autenticación y almacenamiento seguro

- Tokens JWT persistidos con `flutter_secure_storage` (`^9.2.2`) — almacenamiento cifrado nativo (Keychain en iOS, Keystore-backed en Android), a diferencia del frontend web que usa `localStorage`.
- `auth_local_datasource.dart` y `core/services/session_service.dart` gestionan la persistencia y recuperación de la sesión.
- Datos offline (reportes pendientes de sincronizar, presumiblemente) usan `sqflite` como base de datos local.

## Permisos

- Paquete `permission_handler`, con módulo dedicado `lib/features/permissions/` y `core/services/permission_service.dart`.
- **Android** (`AndroidManifest.xml`): `CAMERA`, `ACCESS_FINE_LOCATION`, `ACCESS_COARSE_LOCATION`, `READ_MEDIA_IMAGES`, `READ_EXTERNAL_STORAGE` (API ≤ 32), `INTERNET`.
- **iOS** (`Info.plist`): `NSCameraUsageDescription`, `NSPhotoLibraryUsageDescription`, `NSLocationWhenInUseUsageDescription`.

## Comportamiento offline

`core/services/connectivity_service.dart` detecta conectividad; `database_service.dart` gestiona persistencia local vía `sqflite`. El alcance exacto de qué operaciones funcionan offline (¿solo guardar borrador de reporte, o cola de sincronización completa?) no se verificó a nivel de código en esta fase — pendiente de confirmar antes de documentarlo como comportamiento garantizado.

## Pruebas

`test/unit/features/` y `test/widget/features/`, más el `test/widget_test.dart` por defecto de Flutter. No se auditó la cobertura real en esta fase.
