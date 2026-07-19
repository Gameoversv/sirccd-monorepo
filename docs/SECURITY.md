# Seguridad

[← Volver al índice](README.md)

> Este documento describe únicamente controles de seguridad **confirmados en el código**. No se afirma la existencia de protecciones que no se pudieron verificar.

> Ver [SECURITY_AUDIT.md](SECURITY_AUDIT.md) para la auditoría completa con hallazgos concretos, severidad y remediación (vulnerabilidades de dependencias, validación de archivos, superficie de la API) — este documento es la referencia de mecanismos existentes, aquel es el reporte de auditoría.

## Autenticación

- JWT (HS256) emitido por `backend/core/security.py`: `create_access_token` (expira en `ACCESS_TOKEN_EXPIRE_MINUTES`, default 30) y `create_refresh_token` (7 días).
- Contraseñas hasheadas con bcrypt vía `passlib`.
- Login: `POST /api/v1/auth/login`, acepta username o email como identificador (`backend/api/routes/auth.py`).
- El frontend guarda el token en `localStorage` (clave `sirccd-auth-storage`), no en cookie httpOnly — expone el token a lectura vía JavaScript (XSS en el frontend implicaría robo de token).
- Mobile guarda el token con `flutter_secure_storage` (almacenamiento cifrado nativo), un mecanismo más robusto que el usado en el frontend web.

## Autorización

- RBAC por rol (`UserRole` en `backend/models/user.py`), aplicado por dependencia FastAPI en `backend/api/deps.py`: `require_role`, `require_admin`, `require_supervisor`.
- Cada router decide explícitamente qué dependencia de autorización usar; no hay una capa transversal que aplique el RBAC automáticamente a todos los endpoints — **una ruta nueva sin la dependencia correcta quedaría accesible sin el control esperado**. No se auditó endpoint por endpoint en esta fase (pendiente en `backend/API.md`, Fase 3).

## Manejo de sesiones o tokens

- No hay lista de revocación de tokens (blacklist) documentada — un JWT válido sigue siendo aceptado hasta su expiración natural, incluso si el usuario cierra sesión o es desactivado. Confirmar si esto es una limitación aceptada o pendiente de mitigar.
- `get_optional_user` en `api/deps.py` es una variante que no lanza error si no hay token — usada para acceso a imágenes mediante URLs firmadas (`core/image_tokens.py`), un patrón razonable siempre que la firma de esas URLs tenga su propia expiración (no verificado en esta fase).

## Protección de rutas

- **Backend**: cada endpoint protegido depende explícitamente de `get_current_user`/`require_role` — protección real a nivel de servidor.
- **Frontend**: la protección de `/dashboard/*` es **enteramente del lado cliente**, vía el hook `useAuth()`. No existe `middleware.ts` de Next.js. Esto significa que el HTML/JS de las páginas del dashboard se sirve al navegador antes de que se verifique la sesión — los datos reales siguen protegidos porque provienen de llamadas autenticadas al backend, pero la existencia de las rutas y su estructura no está oculta a un cliente no autenticado.

## Validación de entradas

- Backend: Pydantic v2 (`backend/schemas/`) valida el cuerpo de cada request contra un esquema tipado — rechazo automático de tipos/campos inválidos antes de llegar a la lógica de negocio.
- No se confirmó en esta fase el uso de límites explícitos de tamaño de payload (ej. tamaño máximo de imagen subida) a nivel de FastAPI/Nginx — revisar `infra/nginx/nginx.conf` y la configuración de `python-multipart` si esto es un requisito.

## Manejo de archivos

- Imágenes de reportes se suben a MinIO (`backend/services/storage.py`), con fallback a disco local si MinIO no está disponible.
- Pipeline de anonimización (`backend/services/anonymizer.py`) usa YOLO localmente para difuminar rostros y placas antes de exponer la imagen — confirmado en código, pero no se verificó en esta fase si se aplica a **todas** las imágenes subidas o solo a un subconjunto de flujos.
- Servido de imágenes vía proxy del backend (no URLs directas y anónimas de MinIO), según el propio `README.md` del proyecto ("servir las imagenes por un proxy en vez de URLs de MinIO").
- La validación de subida (`_validate_image` en `storage.py`) solo verifica `content_type` (header del cliente, falsificable) y extensión — no abre el archivo para confirmar que el contenido real sea una imagen válida. Ver hallazgo detallado en [SECURITY_AUDIT.md](SECURITY_AUDIT.md#medio).

## Variables sensibles

- `SECRET_KEY` (firma JWT) tiene un **valor por defecto hardcodeado** en `backend/core/config.py`, con comentario explícito `# CAMBIAR en producción!` — es el fallback usado solo si no hay variable de entorno. **Verificado contra Railway**: la variable real en producción difiere del default (64 caracteres, no coincide) — el riesgo en código sigue ahí como posibilidad si algún entorno futuro olvida configurarla, pero producción actual no depende de él.
- `FIELD_ENCRYPTION_KEY` cifra campos sensibles en base de datos (ej. teléfono) con Fernet (AES-128-CBC + HMAC-SHA256). Importante: `backend/core/field_encryption.py` está diseñado para **degradar silenciosamente a texto plano si la clave no está configurada** ("Retorna texto plano si no hay clave"). Esto es una decisión de disponibilidad sobre seguridad — confirmar que es intencional y que hay alerta operativa si ocurre en producción.
- Ningún secreto real fue incluido en esta documentación ni se copiaron valores del `.env` local.

## CORS

- Configurado vía `CORSMiddleware` de FastAPI en `backend/main.py`, usando la lista de `ALLOWED_ORIGINS` (variable de entorno, formato JSON). En desarrollo local incluye `localhost:3000/3001/5173/8080`; en producción debe limitarse estrictamente al dominio real del frontend.

## Rate limiting

**No se encontró implementación de rate limiting** en el backend (no hay `slowapi` ni middleware equivalente en `requirements.txt` ni en `main.py`). Los endpoints de autenticación y creación de reportes no tienen límite de tasa a nivel de aplicación — si se requiere, debe implementarse a nivel de Nginx/proxy o añadirse como mejora futura.

## Riesgos identificados

Ver tabla completa con severidad en [REPOSITORY_AUDIT.md](REPOSITORY_AUDIT.md#8-riesgos-detectados). Resumen de los relevantes a seguridad:

- ~~`SECRET_KEY` con default hardcodeado~~ — verificado en producción, no aplica (ver arriba).
- Ausencia de rate limiting en endpoints públicos (login, creación de reportes).
- Degradación silenciosa a texto plano si falta `FIELD_ENCRYPTION_KEY`.
- Protección de rutas del dashboard únicamente en cliente.
- Token JWT en `localStorage` (frontend web) en vez de cookie httpOnly.

## Recomendaciones

- ✅ Confirmado: `SECRET_KEY`, `FIELD_ENCRYPTION_KEY`, `POSTGRES_PASSWORD`, `REDIS_PASSWORD` y `MINIO_SECRET_KEY` están configurados como secretos reales en Railway y no dependen de los defaults del código.
- Evaluar rate limiting básico en `/api/v1/auth/login` y `/api/v1/reportes` para mitigar abuso.
- Evaluar migrar el almacenamiento del token JWT en el frontend web de `localStorage` a una cookie httpOnly + `SameSite`, si el riesgo de XSS se considera relevante para este proyecto.
- Añadir alerta/log explícito cuando `FIELD_ENCRYPTION_KEY` no está configurada, dado que el comportamiento actual es degradar sin fallar.
