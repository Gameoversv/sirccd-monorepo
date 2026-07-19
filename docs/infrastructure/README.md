# Infraestructura

[← Volver al índice](../README.md)

## Resumen

La infraestructura de SIRCCD se define casi enteramente con Docker Compose (dos variantes: desarrollo y producción) más una configuración de Nginx como reverse proxy TLS. No hay un orquestador tipo Kubernetes ni infraestructura como código (Terraform/Pulumi) en este repositorio — el despliegue real ocurre en Railway, cuya configuración vive fuera de este repositorio (no versionada aquí).

## Componentes

- [Docker y Docker Compose](DOCKER.md) — servicios, puertos, volúmenes, diferencias dev/prod.
- [CI/CD](CI_CD.md) — pipeline de GitHub Actions existente y su alcance.

Carpetas del repositorio relacionadas: `infra/nginx/` (proxy TLS), `infra/compose/` (MinIO standalone para desarrollo). `infra/ci-cd/` e `infra/docker/` existen pero están vacías (solo `.gitkeep`) — no se documentan hasta tener contenido real.

## No cubierto en este documento

- Configuración específica de Railway (variables de entorno de producción, dominios, escalado) — vive en el panel de Railway, no en este repositorio.
- Monitoreo y alertas de producción — no se encontró configuración de Prometheus/Grafana/alerting en el repositorio más allá del middleware de métricas del backend (`backend/core/metrics.py`, expone métricas Prometheus pero no se confirmó un colector desplegado).
- Backups de base de datos — no se encontró un script o job de backup automatizado en el repositorio.
