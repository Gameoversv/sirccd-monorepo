# Auditoría de seguridad completa

[← Volver al índice](README.md)

**Fecha**: 2026-07-19. **Alcance**: backend (FastAPI), frontend (Next.js), mobile (Flutter), infraestructura (Docker/Nginx), dependencias de terceros. Metodología: escaneo automatizado de vulnerabilidades conocidas (`pip-audit`, `npm audit`) + revisión manual de código en las áreas de mayor riesgo (autenticación, autorización, inyección, manejo de archivos, secretos, XSS/CSRF).

Este documento complementa a [SECURITY.md](SECURITY.md) (que describe los mecanismos de seguridad existentes) con hallazgos concretos, severidad y remediación. Ningún hallazgo de aquí fue corregido automáticamente — se presentan para que el equipo decida.

## Tabla de contenido

- [Resumen de severidad](#resumen-de-severidad)
- [Alto: vulnerabilidades de dependencias](#alto-vulnerabilidades-de-dependencias)
- [Medio](#medio)
- [Bajo](#bajo)
- [Verificado sin hallazgos](#verificado-sin-hallazgos)
- [Recomendaciones priorizadas](#recomendaciones-priorizadas)

## Resumen de severidad

| Severidad | Cantidad | Ítems |
|---|---|---|
| Alto | 2 | Dependencias backend (36 CVEs en 7 paquetes), dependencias frontend (12 CVEs, principalmente Next.js) |
| Medio | 4 | Validación de imágenes sin verificación de contenido real, `/metrics` público, ausencia de rate limiting, Swagger/Redoc expuestos en producción |
| Bajo | 3 | Reutilización de `SECRET_KEY` para firmas de imagen, `dangerouslySetInnerHTML` con contenido hoy estático, límite de payload solo en Nginx (no en el backend directamente) |

No se encontraron: inyección SQL, XSS explotable actualmente, secretos hardcodeados, bypass de autenticación/autorización (IDOR), ni CSRF explotable. Ver [sección de verificaciones sin hallazgos](#verificado-sin-hallazgos) para el detalle de qué se revisó.

## Alto: vulnerabilidades de dependencias

### Backend — 36 vulnerabilidades conocidas en 7 paquetes (`pip-audit`, 2026-07-19)

| Paquete | Versión actual | Fix disponible | Relevancia |
|---|---|---|---|
| **`python-jose`** | 3.3.0 | **3.4.0** | **Alta** — es la librería de firma/verificación de JWT (`core/security.py`). Incluye DoS por JWE con alta compresión y confusión de algoritmo con claves ECDSA/OpenSSH. **Mitigado en este código**: `decode_access_token` fija explícitamente `algorithms=[settings.ALGORITHM]` (HS256), no lee el algoritmo del header del token — el vector de confusión de algoritmo no es explotable aquí. Aun así, actualizar es la práctica correcta. |
| **`starlette`** | 0.38.6 | 0.40.0 – 1.3.1 (viene con FastAPI, no pinnear suelto) | Base ASGI de FastAPI. Incluye: no validación del header `Host` al reconstruir `request.url`, SSRF vía UNC path en `StaticFiles` en Windows, DoS por partes de `multipart/form-data` sin límite de tamaño/cantidad. |
| **`python-multipart`** | 0.0.20 | 0.0.22 – 0.0.31 | Parsea todos los uploads (`UploadFile`). Incluye path traversal (solo si se usan `UPLOAD_DIR`/`UPLOAD_KEEP_FILENAME`, **no usados en este código** — no explotable aquí) y varios DoS de parsing. |
| **`pillow`** | 11.0.0 | 12.1.1 – 12.3.0 | Procesa todas las imágenes subidas (EXIF, anonimización, redimensionado). 12 CVEs — superficie de ataque real dado que procesa contenido subido por usuarios no confiables. |
| `ecdsa` | 0.19.2 | Sin fix publicado | Dependencia transitiva de `python-jose`. Monitorear. |
| `python-dotenv` | 1.0.1 | 1.2.2 | Solo carga `.env` en desarrollo local, no se ejecuta en producción con esta config. |
| `pytest` | 8.3.4 | 9.0.3 | Solo testing, no corre en producción. |

**Remediación recomendada**: actualizar `python-jose` a 3.4.0, `python-multipart` y `pillow` a sus últimas versiones dentro de `requirements.txt`, y `fastapi` (que arrastra una versión más nueva de `starlette` compatible) en vez de fijar `starlette` suelto. Requiere correr la suite de tests completa después (`pytest`) por el riesgo de breaking changes menores.

### Frontend — 12 vulnerabilidades conocidas (`npm audit`, 2026-07-19)

| Paquete | Vulnerabilidad | Severidad | Notas |
|---|---|---|---|
| **`next`** 14.2.35 | 10 CVEs: DoS en Server Components, cache poisoning, XSS en App Router con CSP nonces, XSS en scripts `beforeInteractive`, SSRF vía upgrade de WebSocket, bypass de Middleware con i18n | Alto | **Ya es la última versión estable de la rama 14.x** — no hay parche disponible sin saltar a Next.js 15/16 (breaking change, requiere plan de migración y testing dedicado). No aplicar `npm audit fix --force` sin evaluar el impacto. |
| `picomatch` (transitiva, vía `tinyglobby`) | ReDoS, method injection en clases POSIX | Alto | Solo usada en tooling de build, no en runtime de producción. |
| `postcss` (transitiva, vía `next`) | XSS vía `</style>` sin escapar en la salida | Moderado | Se resuelve junto con el upgrade de Next.js. |

**Remediación recomendada**: planificar la migración a Next.js 15 o 16 como iniciativa separada (breaking change real, no es parte de esta limpieza) — evaluar `next.config.js`, el uso de `app/` router, y las páginas dinámicas antes de actualizar. Mientras tanto, el riesgo real de explotación depende de qué tan expuestas estén las funcionalidades afectadas (Server Components, WebSockets) — este proyecto no usa WebSockets ni Server Actions actualmente, lo que reduce la superficie práctica de varias de estas CVEs.

## Medio

### Validación de imágenes solo por metadata, no por contenido real

`services/storage.py::_validate_image` valida `file.content_type` (header HTTP controlado por el cliente, falsificable) y la extensión del nombre de archivo (también controlada por el cliente) — no abre el archivo con Pillow ni verifica los "magic bytes" antes de aceptarlo. Un atacante podría subir un archivo con extensión `.jpg` y `Content-Type: image/jpeg` cuyo contenido real no sea una imagen válida.

**Mitigación existente**: el pipeline de anonimización y extracción EXIF (`services/anonymizer.py`, `services/exif_service.py`) procesa la imagen con Pillow/YOLO después de la subida — un archivo que no sea una imagen real probablemente falle ahí, aunque como un error 500 en vez de un rechazo limpio en el momento de la subida, y no está garantizado para todos los casos (ej. un polyglot válido como imagen y como otro formato).

**Recomendación**: verificar el contenido abriendo el archivo con `PIL.Image.open()` (o `python-magic`) inmediatamente en `_validate_image`, antes de continuar el pipeline.

### `GET /api/v1/metrics` público sin autenticación

`api/routes/health.py` expone métricas Prometheus (conteo de requests por endpoint/método/status, duración) sin ningún `Depends` de autenticación. No expone PII ni secretos, pero sí revela la superficie completa de la API y patrones de tráfico a cualquiera que la consulte.

**Recomendación**: restringir por red (solo accesible desde el colector de Prometheus interno) o requerir autenticación básica/token dedicado — no debería ser parte de la superficie pública de la API.

### Ausencia de rate limiting

Ya documentado en [SECURITY.md](SECURITY.md). Reconfirmado en esta auditoría: no hay `slowapi` ni middleware equivalente en `requirements.txt` ni en `main.py`. `/auth/login` y `/reportes` (creación) son los endpoints de mayor riesgo (fuerza bruta de credenciales, spam de reportes).

### Documentación interactiva de la API expuesta en producción

`main.py` no condiciona `docs_url`/`redoc_url` por entorno — `/api/v1/docs` (Swagger UI) y `/api/v1/redoc` están accesibles públicamente en producción, exponiendo el esquema completo de la API (rutas, parámetros, modelos de request/response) a cualquiera. Es una práctica común y no es en sí mismo un exploit, pero facilita el reconocimiento a un atacante y muchos equipos optan por deshabilitarlo en producción.

## Bajo

- **Reutilización de `SECRET_KEY`** para firmar tanto JWT (`core/security.py`) como URLs de imagen firmadas (`core/image_tokens.py`, HMAC-SHA256). Usar la misma clave para dos propósitos criptográficos distintos no es un exploit directo, pero es una desviación de buenas prácticas (idealmente una clave derivada o dedicada por propósito) — si una firma de imagen se filtrara con información suficiente para inferir la clave (poco probable con HMAC-SHA256 bien implementado), comprometería también los JWT.
- **`dangerouslySetInnerHTML`** en `frontend/src/app/dashboard/reports/new/page.tsx:219` renderiza una cadena de i18next (`t('reports.new.addressHint')`) como HTML crudo. Hoy es seguro porque las traducciones son archivos JSON estáticos bundleados en build (`src/i18n/locales/`), no contenido dinámico — pero es un patrón frágil: si en el futuro las traducciones pasan a cargarse desde un CMS o servicio externo, esto se vuelve una XSS inmediata. Recomendación: usar interpolación de texto plano o `<Trans>` de `react-i18next` en vez de `dangerouslySetInnerHTML`, salvo que el HTML sea realmente necesario.
- **Límite de tamaño de payload solo a nivel de Nginx** (`client_max_body_size 11M` en `infra/nginx/nginx.conf`, producción) y a nivel de aplicación en `_validate_image` (10 MB) — pero no hay un límite general de tamaño de body a nivel de FastAPI/Starlette para otros endpoints (ej. JSON grandes en `PATCH`/`PUT`). Bajo riesgo dado que la mayoría de los endpoints tienen payloads pequeños y tipados por Pydantic, pero vale la pena confirmar que ningún endpoint acepta listas/arrays sin límite de tamaño.

## Verificado sin hallazgos

Áreas revisadas explícitamente donde **no se encontraron problemas**:

- **Inyección SQL**: todo el acceso a datos usa el ORM de SQLAlchemy (`.query()`, `.filter()`), parametrizado por defecto. La única interpolación de string en SQL crudo (`services/health_service.py:60`, tamaño de la BD) usa `settings.POSTGRES_DB` — configuración del servidor, no input de usuario.
- **IDOR (Insecure Direct Object Reference)**: `GET /reportes/{id}` y `GET /reportes/{id}/image` verifican explícitamente que un ciudadano solo pueda acceder a sus propios reportes (`report.user_id != current_user.id` → 403). Mismo patrón esperado y confirmado en incidentes.
- **Firma de URLs de imagen**: HMAC-SHA256 correctamente implementado, con `hmac.compare_digest` (comparación en tiempo constante, evita timing attacks) y expiración validada antes de la comparación.
- **Algoritmo JWT**: fijado explícitamente a `HS256` en la decodificación, no confía en el header `alg` del token — inmune al ataque de confusión de algoritmo pese a que la CVE existe en la librería.
- **CORS**: `allow_origins` en producción es una lista específica de dominios (no wildcard), combinado correctamente con `allow_credentials=True` (Starlette rechaza esa combinación con wildcard, así que tampoco sería posible configurarlo mal por accidente).
- **CSRF**: no aplica de forma práctica — la autenticación es por Bearer token en el header `Authorization` (no por cookie), que el navegador no adjunta automáticamente en peticiones cross-site.
- **Secretos hardcodeados**: sin coincidencias de patrones de claves de AWS/Slack/API keys tipo `sk-...`, ni contraseñas reales embebidas en código (solo contraseñas de prueba obvias en scripts de verificación, ej. `"testpassword123"`).
- **Mobile (Flutter)**: sin secretos hardcodeados (usa `String.fromEnvironment` vía `--dart-define`), timeouts configurados en el cliente Dio (10s conexión / 30s recepción), sin bypass de validación de certificados TLS (`badCertificateCallback` no presente), tokens en `flutter_secure_storage` (Keychain/EncryptedSharedPreferences).
- **XSS en frontend**: sin uso de `innerHTML`/`eval`/`document.write`; los dos usos de `dangerouslySetInnerHTML` encontrados son seguros hoy (ver sección Bajo).

## Recomendaciones priorizadas

1. **Actualizar `python-jose` a 3.4.0** — mitiga CVEs de DoS aunque el vector de algoritmo-confusión ya esté neutralizado por el código actual. Bajo riesgo de breaking change (API estable entre 3.3→3.4).
2. **Actualizar `python-multipart` y `pillow`** dentro de `requirements.txt`, correr suite completa después.
3. **Agregar verificación de contenido real en `_validate_image`** (abrir con Pillow antes de aceptar) — cierra el gap de subida de archivos falsificados.
4. **Restringir o autenticar `/api/v1/metrics`** — no debería ser parte de la superficie pública.
5. Evaluar planificar la migración de Next.js 14 → 15/16 como iniciativa aparte (no forma parte de esta limpieza; requiere su propio proceso de testing).
6. Rate limiting en `/auth/login` y `POST /reportes` — ya recomendado en `SECURITY.md`, reconfirmado aquí con mayor urgencia dado el volumen de CVEs relacionadas a DoS encontradas en las dependencias.
7. Evaluar deshabilitar `docs_url`/`redoc_url` en producción, o protegerlos con autenticación básica.
