# Documentacion Tecnica SIRCCD

Esta carpeta concentra la documentacion oficial del monorepo SIRCCD (Sistema Inteligente Urbano para Reporte y Priorizacion de Danos Viales).

## Que es SIRCCD

SIRCCD es una plataforma integral que permite a ciudadanos reportar danos viales (baches, grietas, hundimientos) mediante fotografias geolocalizadas, y a operadores municipales gestionar, priorizar y resolver dichos reportes de forma eficiente mediante inteligencia artificial.

## Guia de lectura

1. Comienza por `monorepo.md` para entender la arquitectura global, el flujo funcional y las reglas de organizacion.
2. Lee luego el documento del modulo que estes tocando (`backend.md`, `frontend.md`, `ml.md`, etc.).
3. Si necesitas una vision completa y detallada de todo el sistema, consulta `DOCUMENTACION_COMPLETA.md`.
4. Si cambias estructura de carpetas, actualiza primero el documento del modulo afectado.

## Documentos disponibles

| Documento | Descripcion | Audiencia |
|-----------|-------------|-----------|
| [Monorepo](monorepo.md) | Arquitectura transversal, flujo funcional, reglas de organizacion y mapa de raiz | Todos |
| [Backend](backend.md) | API REST, servicios de negocio, modelos de datos, deduplicacion, workers y pruebas | Desarrolladores backend |
| [Frontend](frontend.md) | Dashboard web, componentes, stores, servicios API, mapas e internacionalizacion | Desarrolladores frontend |
| [ML](ml.md) | Pipeline de ML, entrenamiento, inferencia, embeddings, anonimizacion y notebooks | Data scientists / ML engineers |
| [Infra](infra.md) | Docker, orquestacion, CI/CD, ambientes y plan de consolidacion | DevOps / SRE |
| [Mobile](mobile.md) | App ciudadana Flutter, estado actual y arquitectura planificada | Desarrolladores mobile |
| [Documentacion Completa](DOCUMENTACION_COMPLETA.md) | Referencia extensiva de todo el sistema en un solo documento | Todos |

## Regla editorial

Cada documento de modulo debe incluir siempre:

1. **Proposito**: que hace el modulo y por que existe.
2. **Stack tecnologico**: tecnologias, frameworks y versiones usadas.
3. **Arquitectura**: capas, patrones y decisiones de diseno.
4. **Mapa de archivos**: donde esta cada subcomponente con descripcion.
5. **Flujos funcionales**: como se procesan las operaciones principales.
6. **Endpoints / Interfaces**: contratos de comunicacion (si aplica).
7. **Modelos de datos**: entidades y relaciones (si aplica).
8. **Configuracion**: variables de entorno y archivos de config.
9. **Comandos operativos**: como ejecutar, probar y desplegar.
10. **Integraciones**: como se conecta con otros modulos.

## Estado actual de la documentacion

- Documentacion historica dispersa eliminada.
- Documentacion consolidada por modulo en `docs/*.md`.
- `backend/docs/` vaciado para evitar duplicidad.
- Documentacion especifica de ML se mantiene en `ml/docs/` para guias operativas de entrenamiento.
- Documentacion especifica de frontend en `frontend/docs/` para implementacion de mapa.
- Documento de referencia completa (`DOCUMENTACION_COMPLETA.md`) agregado como fuente unica extensiva.
