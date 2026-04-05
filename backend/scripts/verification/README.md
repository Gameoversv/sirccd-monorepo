# Scripts de Verificacion

Scripts para comprobar estado tecnico de piezas del backend.

## Archivos

- verify_b02.py: verifica esquema/migracion y capacidades geoespaciales.
- verify_b03.py: verifica componentes base de autenticacion.
- verify_migration.py: validacion general de tablas, PostGIS e indices.

## Ejecucion

```powershell
cd backend
python scripts/verification/verify_b02.py
python scripts/verification/verify_b03.py
python scripts/verification/verify_migration.py
```
