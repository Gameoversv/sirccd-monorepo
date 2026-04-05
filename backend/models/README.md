# Modelos Backend SIRCCD

Documentacion de las entidades ORM activas del modulo backend.

## Archivos reales en esta carpeta

- `__init__.py`: exportaciones de modelos.
- `user.py`: entidad de usuario y enums asociados de usuario.
- `report.py`: entidad de reporte y enums de reporte/dano/severidad.
- `incident.py`: entidad de incidente y enums de prioridad/estado.
- `poi.py`: entidad de punto de interes geoespacial.
- `metric.py`: entidad de metricas/eventos del sistema.

## Rol de cada modelo

1. `user.py`
   - identidad del usuario,
   - rol/autorizacion,
   - estado activo/inactivo.

2. `report.py`
   - reporte ciudadano,
   - tipo de dano,
   - severidad/confianza,
   - estado de validacion,
   - ubicacion geoespacial.

3. `incident.py`
   - incidente operativo derivado de reportes,
   - prioridad,
   - estado de ciclo de atencion,
   - datos para gestion municipal.

4. `poi.py`
   - puntos de interes para contexto de riesgo.

5. `metric.py`
   - almacenamiento de metricas/eventos de operacion.

## Relacion con otras capas

- `schemas/` refleja contratos API de estas entidades.
- `services/` aplica reglas de negocio sobre estos modelos.
- `api/routes/` expone operaciones CRUD y flujos.
- `db/session.py` gestiona sesion de persistencia.

## Nota

Para arquitectura de backend completa:

- `../README.md`
- `../../docs/backend.md`
