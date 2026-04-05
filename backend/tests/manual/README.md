# Tests Manuales Backend

Esta carpeta contiene pruebas y scripts de validacion manual no orientados a CI.

## Contenido

- test_auth_manual.py: validaciones manuales de autenticacion.
- test_b04_reports.py: flujo manual de creacion de reportes.
- test_b05_anonymization.py: pruebas de anonimizado con fixtures de imagen.
- test_b06_*.py: validacion de cola/asincronia e inferencia.
- test_b07_*.py: validacion manual de deduplicacion.
- test_b08_*.py: validacion manual de priorizacion.
- test_b09_export.py: validacion de exportaciones.
- test_b10_observability.py: validacion de observabilidad.
- test_geospatial.py: validaciones geoespaciales directas.
- TESTING_B06.py: guia operativa de pruebas B-06.

## Fixtures

- fixtures/test_image_noface.jpg
- fixtures/test_image_with_face.jpg
- fixtures/test_anonymized_output.jpg
- fixtures/test_image.jpg (se crea bajo demanda en test_b04_reports.py)

## Ejecucion

```powershell
cd backend
pytest tests/manual/test_b07_deduplication.py -q
```

Para scripts de smoke completos, leer cada archivo antes de ejecutar: varios requieren API, Redis y DB activos.
