# sirccd-monorepo
Sistema Inteligente Urbano para Reporte y Priorización de Daños Viales (SIRCCD)

## Flujo de ramas (Git branching)

El monorepo se organiza con las siguientes ramas:

- `main`  
  - Rama estable.
  - Solo se mergea cuando una funcionalidad está probada y lista.

- `dev`  
  - Rama de integración.
  - Aquí se integran las ramas de features antes de pasar a `main`.

- `feat/*`  
  - Para nuevas funcionalidades.
  - Ejemplos:
    - `feat/frontend-reportes`
    - `feat/backend-incidentes`
    - `feat/ml-yolov8-seg`

- `fix/*`  
  - Para corrección de bugs.
  - Ejemplos:
    - `fix/frontend-filtro-mapa`
    - `fix/backend-endpoint-kpis`

- `doc/*`  
  - Para cambios de documentación.
  - Ejemplo: `doc/diagrama-procesos`, `doc/acta-constitucion`

## Convención de commits

Se sigue una convención de tipo `tipo: descripción corta` en minúsculas.

Tipos permitidos:

- `feat:`  nueva funcionalidad (usuario final o API)
- `fix:`   corrección de error
- `docs:`  cambios solo de documentación
- `style:` formato/cambios estéticos (sin afectar lógica)
- `refactor:` cambios internos sin cambiar comportamiento
- `test:`  agregar o mejorar pruebas
- `chore:` tareas de mantenimiento (config, scripts, dependencias)

Ejemplos:

- `feat: agregar mapa de incidentes por barrio`
- `fix: corregir cálculo de severidad en backend`
- `docs: agregar diagrama de flujo de procesos`
- `refactor: separar servicios de IA en módulo ml`
