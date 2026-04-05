# Scripts Backend

Organizacion de scripts operativos del backend.

## Estructura

- evaluate_dedup_embeddings.py: evaluacion M-11 de embeddings de deduplicacion.
- maintenance/: scripts de mantenimiento y tareas operativas.
- verification/: scripts de verificacion tecnica de componentes.

## Politica

1. No colocar scripts sueltos en la raiz de backend.
2. Todo script nuevo debe incluir descripcion de uso en README de su carpeta.
3. Si un script se vuelve parte de CI, moverlo a tests/ o pipeline correspondiente.
