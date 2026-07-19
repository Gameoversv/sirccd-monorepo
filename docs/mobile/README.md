# Mobile

[← Volver al índice](../README.md)

## Resumen

App ciudadana en Flutter/Dart (`mobile/`), permite reportar daños viales con foto + GPS y consultar reportes propios, con soporte de almacenamiento local (offline) y sesión persistente segura.

- **SDK**: Flutter, Dart `^3.9.2` (`pubspec.yaml`).
- **Gestión de dependencias**: `flutter pub get` (`pubspec.yaml` / `pubspec.lock`).

## Documentos

- [Arquitectura](ARCHITECTURE.md) — estructura por capas, navegación, estado, integración con el backend, permisos.

## Comandos básicos

```bash
cd mobile
flutter pub get     # instalar dependencias
flutter run          # ejecutar en dispositivo/emulador conectado
flutter test          # correr pruebas (unit + widget)
flutter analyze      # lint estático (analysis_options.yaml)
```

## Pendiente de documentar

- Proceso de build/firma para distribución (Android APK/AAB, iOS IPA) — no se encontró configuración de firma ni pipeline de build en el repositorio; requiere confirmación del equipo antes de documentarse como oficial.
- Sin pipeline de CI para mobile (ver [infrastructure/CI_CD.md](../infrastructure/CI_CD.md)).
