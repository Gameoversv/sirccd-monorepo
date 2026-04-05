# Modulo Infra

## 1) Proposito del modulo

Infra define el espacio oficial para infraestructura del proyecto:

1. CI/CD,
2. compose por entorno,
3. artefactos docker reutilizables,
4. estandares de despliegue.

## 2) Estado actual de implementacion

Se dejo una estructura base lista para evolucionar:

- `infra/ci-cd/`
- `infra/compose/`
- `infra/docker/`

Actualmente estas carpetas tienen placeholders (`.gitkeep`), lo que indica que la estructura esta creada pero aun no poblada con definiciones productivas.

## 3) Donde esta cada cosa

### Dentro de infra

- `infra/ci-cd/`: destino de pipelines, checks y jobs.
- `infra/compose/`: destino de compose separados por ambiente.
- `infra/docker/`: destino de Dockerfiles y templates base.

### Fuera de infra (estado transitorio)

- `docker-compose.yml`: compose principal a nivel raiz.
- `docker-compose.minio.yml`: compose de MinIO en raiz.
- `backend/docker-compose.db.yml`: compose para servicios de backend.

## 4) Como debe evolucionar

1. mover compose dispersos hacia `infra/compose/`.
2. crear convencion de nombres por ambiente.
3. publicar pipelines de build/test/deploy en `infra/ci-cd/`.
4. centralizar Dockerfiles reutilizables en `infra/docker/`.
5. documentar secretos, variables y perfiles de despliegue.

## 5) Resultado esperado

Infra debe convertirse en la referencia unica para operacion y despliegue, reduciendo dependencias de archivos sueltos fuera del modulo.
