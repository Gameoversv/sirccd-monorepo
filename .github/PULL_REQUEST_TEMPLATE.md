## Descripción

<!-- Qué cambia y por qué. Si cierra un issue: Closes #NN -->

## Tipo de cambio

- [ ] `feat` — nueva funcionalidad
- [ ] `fix` — corrección de bug
- [ ] `refactor` — cambio interno sin alterar comportamiento
- [ ] `docs` — solo documentación
- [ ] `test` — solo pruebas
- [ ] `chore` / `ci` / `perf`

## Componentes afectados

- [ ] backend
- [ ] frontend
- [ ] mobile
- [ ] ml
- [ ] database / migraciones
- [ ] infra / CI

## Cómo se probó

<!-- Comandos ejecutados y resultado. Ej: cd backend && ./run_tests.sh unit -->

## Checklist

- [ ] Los tests del componente tocado pasan localmente
- [ ] Linter y type-check en verde
- [ ] Sin secretos, tokens ni credenciales en el diff
- [ ] Sin `console.log` ni `print()` de depuración
- [ ] Cambios de esquema acompañados de su migración de Alembic
- [ ] Variables de entorno nuevas en `.env.example` y `docs/ENVIRONMENT_VARIABLES.md`
- [ ] Documentación actualizada (ver tabla en [CONTRIBUTING.md](../CONTRIBUTING.md#documentación))
- [ ] Rama actualizada con `main`, sin conflictos

## Notas para el revisor

<!-- Áreas de riesgo, decisiones discutibles, pendientes conocidos -->
