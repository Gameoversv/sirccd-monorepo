# ADR-001: Arquitectura actual del sistema

[← Volver al índice de decisiones](README.md)

## Estado

Existente (documentada retroactivamente — la decisión ya estaba tomada e implementada al momento de escribir este ADR).

## Contexto

SIRCCD necesita servir a tres clientes distintos (dashboard web operativo, portal ciudadano web, app móvil) con una única fuente de verdad de datos, e incorporar detección automática de daños viales mediante visión por computadora, sin contar con un equipo grande de infraestructura dedicado.

## Decisión

- Backend único (FastAPI) como monolito modular, organizado por capas (`api/` → `services/` → `models/`), sirviendo a los tres clientes vía REST versionado (`/api/v1`).
- Autenticación stateless con JWT (HS256), sin servidor de sesiones.
- Cola de tareas (Redis + RQ) para desacoplar el procesamiento pesado (inferencia ML, envío de alertas) del ciclo de request/response del API.
- Detección de daños delegada a un servicio SaaS externo (Roboflow) en vez de servir un modelo propio, mientras el modelo propio (`ml/`) sigue en fase de entrenamiento/experimentación offline (Google Colab).
- Almacenamiento de objetos (imágenes) en MinIO (S3-compatible), con fallback a disco local para desarrollo sin MinIO levantado.
- Tres bases de código de cliente completamente independientes (Next.js para web, Flutter para mobile), sin capa compartida de tipos/contratos.

## Alternativas consideradas

No hay evidencia en el repositorio de que se hayan evaluado formalmente alternativas (ej. microservicios separados por dominio, GraphQL en vez de REST, modelo propio servido desde el día uno). Este ADR documenta la arquitectura tal como existe, no un proceso de decisión registrado en su momento.

## Consecuencias positivas

- Un solo backend simplifica el despliegue y el razonamiento sobre el sistema para un equipo pequeño.
- JWT stateless permite escalar el backend horizontalmente sin coordinación de sesiones.
- Delegar la detección de daños a Roboflow permitió tener funcionalidad de detección en producción sin esperar a que el modelo propio estuviera listo.
- Los fallbacks locales (MinIO, Roboflow) permiten desarrollo local sin tener todos los servicios externos disponibles.

## Consecuencias negativas

- El backend acopla dependencias de ML pesadas (`torch`, `transformers`, `faiss-cpu`) al mismo proceso que sirve la API REST, incrementando el tamaño de la imagen de despliegue y el acoplamiento entre lógica de negocio e inferencia local (usada actualmente solo para deduplicación visual y anonimización, no para la detección principal).
- Sin capa compartida entre los clientes web y móvil, cualquier cambio de contrato de API debe replicarse manualmente en TypeScript y Dart.
- Sin lista de revocación de tokens JWT, la única forma de invalidar una sesión activa es esperar su expiración natural.
- Dependencia de un servicio SaaS externo (Roboflow) para la funcionalidad central del producto (detección de daños) introduce un punto de falla y costo fuera del control directo del equipo.

## Riesgos

Ver el detalle completo, con severidad, en [../REPOSITORY_AUDIT.md](../REPOSITORY_AUDIT.md#8-riesgos-detectados). Los más directamente ligados a esta decisión arquitectónica: ausencia de CI/CD para frontend/mobile/ml, `SECRET_KEY` con default hardcodeado pendiente de confirmar en producción, y protección de rutas del dashboard únicamente en el cliente.

## Fecha

Documentado el 2026-07-18, reflejando el estado del repositorio en el commit `794bb05` (2026-07-17).
