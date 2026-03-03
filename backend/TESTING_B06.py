"""
Guía de Testing B-06 - Sistema de Inferencia ML con Colas
==========================================================

Sigue estos pasos para probar el sistema completo de procesamiento asíncrono.
"""

print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                    GUIA DE TESTING B-06                                   ║
║          Sistema de Inferencia ML Asíncrono con Redis Queue              ║
╚═══════════════════════════════════════════════════════════════════════════╝

📋 REQUISITOS PREVIOS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Redis debe estar corriendo en localhost:6379
2. Base de datos PostgreSQL con PostGIS activa
3. Dependencias instaladas: pip install -r requirements.txt

═══════════════════════════════════════════════════════════════════════════

PASO 1: VERIFICAR REDIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Windows (con Docker):
  > docker ps | findstr redis
  Si no está corriendo:
  > docker run -d -p 6379:6379 --name redis redis:latest

Probar conexión:
  > cd backend
  > python -c "import redis; r=redis.Redis(); print('✅ Redis OK' if r.ping() else '❌ Error')"

═══════════════════════════════════════════════════════════════════════════

PASO 2: TEST RÁPIDO DE COMPONENTES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Este test verifica que todos los componentes funcionen SIN necesidad del servidor:

  Terminal 1:
  ──────────
  > cd backend
  > ..\.venv\Scripts\python.exe test_b06_simple.py

  ✅ Deberías ver:
     • Redis conectado: localhost:6379
     • QueueService inicializado
     • MLService funcionando (MOCK)
     • Task ejecutada directamente
     • Job encolado exitosamente

═══════════════════════════════════════════════════════════════════════════

PASO 3: INICIAR EL WORKER RQ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

El worker procesa los jobs de la cola en segundo plano:

  Terminal 1 (dejar corriendo):
  ──────────────────────────────
  > cd backend
  > ..\.venv\Scripts\python.exe worker.py

  ✅ Output esperado:
     ✅ Conectado a Redis: localhost:6379
     🎧 Escuchando colas: ['ml_inference', 'default']
     🚀 Worker iniciado: sirccd-worker-XXXXX
     ⏳ Esperando tareas...

  ⚠️ NO CERRAR ESTA TERMINAL - El worker debe quedarse corriendo

═══════════════════════════════════════════════════════════════════════════

PASO 4: INICIAR EL SERVIDOR FASTAPI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Terminal 2 (dejar corriendo):
  ──────────────────────────────
  > cd backend
  > ..\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000

  ✅ Output esperado:
     INFO:     Uvicorn running on http://0.0.0.0:8000
     INFO:     Application startup complete

  ⚠️ NO CERRAR ESTA TERMINAL - El servidor debe quedarse corriendo

═══════════════════════════════════════════════════════════════════════════

PASO 5: PROBAR CON CURL / HTTPIE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Terminal 3:
  ───────────
  
  A. Primero necesitas un token de autenticación:
  
     > cd backend
     > ..\.venv\Scripts\python.exe -c "from api.routes.auth import hash_password; print(hash_password('password123'))"
  
  B. O usa un usuario existente (ej: testb04user / testb04pass)
  
  C. Obtener token:
  
     PowerShell:
     > $body = @{username='testb04user'; password='testb04pass'} | ConvertTo-Json
     > $response = Invoke-RestMethod -Uri http://localhost:8000/api/v1/auth/login -Method POST -Body $body -ContentType 'application/json'
     > $token = $response.access_token
     > echo $token
  
  D. Crear reporte con imagen:
  
     > $headers = @{Authorization="Bearer $token"}
     > $form = @{
         latitude='-34.603722'
         longitude='-58.381592'
         description='Bache de prueba B-06'
         image=Get-Item 'test_image.jpg'
       }
     > $result = Invoke-RestMethod -Uri http://localhost:8000/api/v1/reportes -Method POST -Headers $headers -Form $form
     > $result | ConvertTo-Json
  
  ✅ Deberías recibir:
     {
       "id": 10,
       "status": "processing",
       "job_id": "abc123-def456...",
       "damage_type": "bache",
       "severity": "media",
       "confidence": 0.0,
       ...
     }
  
  E. Consultar estado del job:
  
     > $jobId = $result.job_id
     > $jobStatus = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/reportes/jobs/$jobId/status" -Headers $headers
     > $jobStatus | ConvertTo-Json
  
  ✅ Deberías ver:
     {
       "job_id": "abc123-def456...",
       "status": "finished",  // o "queued", "started"
       "result": {
         "report_id": 10,
         "success": true,
         "damage_type": "bache",
         "severity": "alta",
         "confidence": 0.87,
         "num_detections": 3
       }
     }

═══════════════════════════════════════════════════════════════════════════

PASO 6: OBSERVAR EL WORKER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Vuelve a la Terminal 1 (worker) y deberías ver algo como:

  🚀 [Task] Procesando reporte ID=10
  🤖 Ejecutando inferencia ML...
  📊 Usando detección MOCK
  ✅ Detección completada: bache (alta) - 3 detecciones
  ✅ [Task] Reporte 10 procesado exitosamente

═══════════════════════════════════════════════════════════════════════════

PASO 7: VER ESTADÍSTICAS DE LA COLA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  > $stats = Invoke-RestMethod -Uri http://localhost:8000/api/v1/reportes/queue/stats -Headers $headers
  > $stats | ConvertTo-Json

  ✅ Verás:
     {
       "name": "ml_inference",
       "queued": 0,       // Jobs esperando
       "started": 0,      // Jobs procesándose ahora
       "finished": 5,     // Jobs completados
       "failed": 0        // Jobs fallidos
     }

═══════════════════════════════════════════════════════════════════════════

PASO 8: TEST AUTOMATIZADO COMPLETO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Si tienes el servidor Y el worker corriendo, ejecuta:

  Terminal 3:
  ───────────
  > cd backend
  > ..\.venv\Scripts\python.exe test_b06_queue_inference.py

  Este test ejecuta:
  1. Verificar estadísticas de cola
  2. Crear reporte con imagen
  3. Obtener job_id
  4. Polling de estado (espera hasta que termine)
  5. Verificar que el reporte se actualizó en BD
  6. Test de ejecución directa de task

═══════════════════════════════════════════════════════════════════════════

🎯 FLUJO COMPLETO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Cliente → POST /reportes (con imagen)
              ↓
2. FastAPI → Guarda imagen + Crea reporte (status=PROCESSING)
              ↓
3. FastAPI → Encola job en Redis Queue
              ↓
4. FastAPI → Retorna inmediatamente {id, job_id, ...}
              ↓
5. Worker → Toma job de la cola
              ↓
6. Worker → Ejecuta MLInferenceService.detect()
              ↓
7. Worker → Actualiza reporte en BD con resultados
              ↓
8. Cliente → GET /reportes/jobs/{job_id}/status (polling)
              ↓
9. Cliente → Recibe resultado final

═══════════════════════════════════════════════════════════════════════════

⚡ TROUBLESHOOTING:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Problema: "Error conectando a Redis"
→ Solución: docker run -d -p 6379:6379 redis:latest

Problema: "Job queda en 'queued' forever"
→ Solución: Verificar que el worker esté corriendo (Terminal 1)

Problema: "Import errors en worker"
→ Solución: Usar el Python correcto: ..\.venv\Scripts\python.exe

Problema: "No se encuentra la imagen"
→ Solución: Usar ruta absoluta o verificar que test_image.jpg exista

Problema: "Job status 'failed'"
→ Solución: Ver logs del worker para el stack trace

═══════════════════════════════════════════════════════════════════════════

📊 MONITOREO EN REDIS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Si tienes redis-cli instalado:

  > redis-cli LLEN rq:queue:ml_inference  # Jobs en cola
  > redis-cli KEYS "rq:job:*"             # Todos los jobs
  > redis-cli FLUSHDB                     # Limpiar todo (cuidado!)

Desde Python:

  > python -c "from services.queue_service import queue_service; print(queue_service.get_queue_stats())"

═══════════════════════════════════════════════════════════════════════════

🎉 ¡ÉXITO!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Si todos los pasos funcionan, tienes un sistema de procesamiento ML asíncrono
completamente funcional, escalable y tolerante a fallos.

Próximos pasos:
• Entrenar modelo YOLO real
• Configurar múltiples workers
• Implementar retry automático
• Agregar webhooks de notificación

═══════════════════════════════════════════════════════════════════════════
""")
