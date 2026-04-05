# Modulo Mobile

## 1. Proposito del modulo

El modulo Mobile sera la aplicacion ciudadana de SIRCCD para dispositivos Android e iOS. Permitira a los ciudadanos reportar danos viales directamente desde el campo con captura de foto y ubicacion GPS.

### 1.1 Objetivos funcionales

1. **Autenticacion ciudadana**: login y registro integrado con el backend.
2. **Captura de imagen**: toma de foto con camara del dispositivo o seleccion desde galeria.
3. **Captura de ubicacion**: obtencion automatica de coordenadas GPS con posibilidad de ajuste manual en mapa.
4. **Envio de reporte**: submission del reporte con foto, ubicacion y descripcion opcional al backend.
5. **Seguimiento**: consulta del estado de reportes propios (pending, processing, classified, resolved).
6. **Operacion offline**: encolamiento de reportes sin conexion con sincronizacion automatica al recuperar red.

### 1.2 Usuarios objetivo

Ciudadanos que transitan por la ciudad y encuentran danos viales. La app debe ser intuitiva, rapida y funcionar con conectividad intermitente.

## 2. Stack tecnologico (planificado)

| Componente | Tecnologia | Proposito |
|-----------|------------|-----------|
| Framework | Flutter | UI nativa cross-platform (Android + iOS) |
| Lenguaje | Dart | Lenguaje de Flutter |
| Estado | GetX o Provider | Gestion de estado reactiva |
| HTTP | dio o http | Comunicacion con backend REST API |
| Storage local | sqflite / shared_preferences | Cache y cola offline |
| Mapas | google_maps_flutter / flutter_map | Visualizacion y seleccion de ubicacion |
| Camara | camera / image_picker | Captura y seleccion de imagenes |
| GPS | geolocator | Obtencion de coordenadas |
| Auth | JWT (access + refresh tokens) | Sesion del usuario |

## 3. Estado actual

**Scaffold minimo**: el modulo existe como estructura de directorios pero no tiene un proyecto Flutter inicializado.

```
mobile/
├── assets/      # Recursos estaticos (placeholder, vacio)
└── lib/         # Espacio para codigo fuente Dart (placeholder, vacio)
```

No hay `pubspec.yaml`, ni configuracion de Android/iOS, ni codigo Dart.

## 4. Arquitectura planificada

### 4.1 Estructura de directorios recomendada

```
mobile/
├── android/                     # Configuracion nativa Android
├── ios/                         # Configuracion nativa iOS
├── lib/
│   ├── main.dart                # Entry point de la app
│   ├── app.dart                 # MaterialApp, routing, theme
│   ├── features/
│   │   ├── auth/
│   │   │   ├── screens/
│   │   │   │   ├── login_screen.dart
│   │   │   │   └── register_screen.dart
│   │   │   ├── controllers/
│   │   │   │   └── auth_controller.dart
│   │   │   └── widgets/
│   │   │       └── auth_form.dart
│   │   ├── reports/
│   │   │   ├── screens/
│   │   │   │   ├── create_report_screen.dart
│   │   │   │   ├── report_detail_screen.dart
│   │   │   │   └── my_reports_screen.dart
│   │   │   ├── controllers/
│   │   │   │   └── reports_controller.dart
│   │   │   └── widgets/
│   │   │       ├── image_capture.dart
│   │   │       ├── location_picker.dart
│   │   │       └── report_card.dart
│   │   └── profile/
│   │       ├── screens/
│   │       │   └── profile_screen.dart
│   │       └── controllers/
│   │           └── profile_controller.dart
│   ├── shared/
│   │   ├── services/
│   │   │   ├── api_service.dart      # Cliente HTTP base
│   │   │   ├── auth_service.dart     # Autenticacion
│   │   │   ├── reports_service.dart  # CRUD de reportes
│   │   │   ├── location_service.dart # GPS
│   │   │   ├── camera_service.dart   # Camara
│   │   │   └── offline_service.dart  # Cola offline
│   │   ├── models/
│   │   │   ├── user.dart
│   │   │   ├── report.dart
│   │   │   └── api_response.dart
│   │   ├── widgets/
│   │   │   ├── loading_indicator.dart
│   │   │   ├── error_widget.dart
│   │   │   ├── custom_button.dart
│   │   │   └── custom_input.dart
│   │   ├── state/
│   │   │   ├── auth_state.dart
│   │   │   └── connectivity_state.dart
│   │   ├── utils/
│   │   │   ├── validators.dart
│   │   │   ├── formatters.dart
│   │   │   └── constants.dart
│   │   └── theme/
│   │       └── app_theme.dart
│   └── config/
│       ├── routes.dart
│       └── environment.dart
├── assets/
│   ├── images/              # Iconos e imagenes
│   └── translations/        # Archivos de traduccion ES/EN
├── test/                    # Tests unitarios y de widgets
├── pubspec.yaml             # Dependencias y metadata
└── README.md
```

### 4.2 Patron arquitectonico

Se recomienda **Feature-first** con separacion de:
- **Screens**: vistas/paginas completas.
- **Controllers**: logica de estado y negocio por feature.
- **Widgets**: componentes UI reutilizables por feature.
- **Services**: acceso a recursos externos (API, GPS, camara, storage).
- **Models**: DTOs desacoplados de modelos de UI.

### 4.3 Diagrama de flujo de datos

```
UI (Screens + Widgets)
    |
    v
Controllers (estado reactivo)
    |
    v
Services (API, GPS, camara, storage)
    |
    ├──→ Backend REST API (remoto)
    ├──→ SQLite (local, cola offline)
    ├──→ GPS (dispositivo)
    └──→ Camara (dispositivo)
```

## 5. Flujos funcionales planificados

### 5.1 Flujo de autenticacion

```
1. App abre → verifica token almacenado en SharedPreferences
2. Si token valido → navega a pantalla principal
3. Si no → muestra login
4. Login: email + password → POST /api/auth/login
5. Almacena access_token + refresh_token localmente
6. Interceptor HTTP adjunta token a cada request
7. Refresh automatico antes de expiracion
```

### 5.2 Flujo de creacion de reporte

```
1. Ciudadano toca "Nuevo reporte"
2. Captura imagen:
   a. Camara: abre viewfinder, toma foto
   b. Galeria: selecciona imagen existente
3. Captura ubicacion:
   a. GPS automatico (solicita permiso si necesario)
   b. Mapa para ajuste manual (drag marker)
4. Descripcion opcional (campo de texto)
5. Preview de reporte (foto + mapa + texto)
6. Confirmar envio:
   a. Con conexion: POST /api/reports (multipart)
   b. Sin conexion: encolar en SQLite local
7. Confirmacion visual (toast/snackbar)
8. Redireccion a "Mis reportes"
```

### 5.3 Flujo offline

```
1. App detecta que no hay conexion (connectivity_state)
2. Reporte se almacena en SQLite con status="queued"
3. UI muestra indicador de "pendiente de envio"
4. Al recuperar conexion:
   a. offline_service detecta cambio de connectivity
   b. Procesa cola FIFO: envia cada reporte pendiente
   c. Actualiza status local a "sent"
   d. Muestra notificacion de sincronizacion completada
```

### 5.4 Flujo de seguimiento

```
1. Ciudadano accede a "Mis reportes"
2. GET /api/reports?user_id=me → lista de reportes propios
3. Cada reporte muestra: foto thumbnail, estado, fecha, tipo (si clasificado)
4. Tap en reporte → detalle completo
5. Pull-to-refresh para actualizar estados
```

## 6. Permisos del dispositivo requeridos

| Permiso | Uso | Obligatorio |
|---------|-----|-------------|
| Camara | Captura de foto del dano | Si (para reportar) |
| Galeria / Fotos | Seleccion de imagen existente | Si (alternativa a camara) |
| Ubicacion (GPS) | Geolocalizacion del reporte | Si (para reportar) |
| Internet | Comunicacion con backend | Si (offline-first cuando no disponible) |
| Notificaciones | Avisos de estado de reportes (futuro) | Opcional |

## 7. Integraciones

### 7.1 Con backend

| Endpoint | Uso en mobile |
|----------|--------------|
| `POST /api/auth/login` | Login de ciudadano |
| `POST /api/auth/register` | Registro de ciudadano |
| `POST /api/auth/refresh` | Refresh de token |
| `GET /api/auth/me` | Perfil del usuario |
| `POST /api/reports` | Envio de reporte (multipart: imagen + datos) |
| `GET /api/reports` | Lista de reportes propios |
| `GET /api/reports/{id}` | Detalle de reporte |

### 7.2 Con infra

- Build de APK/IPA en pipeline CI/CD (futuro)
- Distribucion via Firebase App Distribution o TestFlight (futuro)

## 8. Consideraciones de implementacion

### 8.1 Diseno UX

- **Flujo minimo**: el ciudadano debe poder reportar en 3 toques (foto → ubicacion → enviar).
- **Feedback inmediato**: confirmacion visual de envio exitoso o encolamiento offline.
- **Tamano de imagen**: comprimir antes de enviar para reducir uso de datos moviles.
- **Modo oscuro**: soporte opcional desde el inicio.

### 8.2 Seguridad

- Tokens JWT almacenados en secure storage (flutter_secure_storage), no en SharedPreferences plano.
- Certificado SSL pinning para comunicacion con backend en produccion.
- No almacenar datos sensibles en SQLite sin encriptacion.

### 8.3 Performance

- Lazy loading de imagenes en listas.
- Compresion de imagenes antes de upload (max 1MB).
- Cache de respuestas frecuentes (perfil, categorias).
- Paginacion en lista de reportes.

## 9. Proximos pasos tecnicos

1. **Inicializar proyecto Flutter**:
   ```bash
   cd mobile
   flutter create --org com.sirccd .
   ```

2. **Definir dependencias** en `pubspec.yaml`:
   ```yaml
   dependencies:
     flutter:
       sdk: flutter
     dio: ^5.0.0
     get: ^4.6.0        # o provider/riverpod
     geolocator: ^10.0.0
     image_picker: ^1.0.0
     google_maps_flutter: ^2.5.0
     sqflite: ^2.3.0
     flutter_secure_storage: ^9.0.0
     connectivity_plus: ^5.0.0
   ```

3. **Implementar primer vertical**: login → crear reporte → ver reportes propios.

4. **Configurar CI**: build de APK en GitHub Actions.

5. **Testing**: unit tests para services, widget tests para screens.
