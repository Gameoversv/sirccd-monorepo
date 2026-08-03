"""
Tests del servicio de cola RQ (services/queue_service.py).

Estaba en 0%. Es la puerta de entrada al pipeline asíncrono: si encolar falla,
el reporte se crea igual y responde 201, pero nunca se clasifica ni se
deduplica. Todos los caminos de error devuelven None o un dict con "error", así
que un fallo aquí es invisible desde fuera.

Redis se mockea siempre; ningún test abre una conexión real.
"""

import importlib.util
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _load_real_queue_service():
    """
    Carga el módulo real bajo otro nombre.

    `conftest.py` mete un MagicMock en `sys.modules['services.queue_service']`
    antes de importar la app, para que importar los routers no intente
    conectarse a Redis. Eso deja el módulo permanentemente intesteable por la
    vía normal — es la razón de que lleve 0% de cobertura.

    Cargarlo con un nombre distinto da acceso al código real sin tocar la
    entrada de `sys.modules` de la que dependen el resto de los tests.
    """
    ruta = Path(__file__).resolve().parent.parent / "services" / "queue_service.py"
    spec = importlib.util.spec_from_file_location("queue_service_real", ruta)
    modulo = importlib.util.module_from_spec(spec)
    # El módulo instancia QueueService() al importarse: sin Redis vivo, el
    # constructor cae en su rama de error y deja queue = None.
    spec.loader.exec_module(modulo)
    return modulo


qs = _load_real_queue_service()
QueueService = qs.QueueService
get_queue_service = qs.get_queue_service


@pytest.fixture
def service_sin_redis() -> "qs.QueueService":
    """Servicio construido con Redis caído: queda con queue = None."""
    with patch.object(qs, "Redis", side_effect=ConnectionError("sin redis")):
        return QueueService()


@pytest.fixture
def service_con_cola() -> "qs.QueueService":
    """Servicio con una cola mockeada ya conectada."""
    with patch.object(qs, "Redis") as redis_cls, patch.object(qs, "Queue") as queue_cls:
        redis_cls.return_value.ping.return_value = True
        service = QueueService()
        service.queue = queue_cls.return_value
    return service


# ==========================================
# Conexión
# ==========================================

@pytest.mark.unit
@pytest.mark.ml
class TestConexion:

    def test_si_redis_no_responde_el_servicio_queda_degradado(self, service_sin_redis):
        assert service_sin_redis.queue is None
        assert service_sin_redis.redis_conn is None

    def test_construir_el_servicio_no_lanza_aunque_redis_falle(self):
        """La API arranca aunque Redis esté caído; no debe explotar al importar."""
        with patch.object(qs, "Redis", side_effect=OSError("boom")):
            QueueService()  # no debe lanzar

    def test_con_redis_disponible_crea_la_cola(self):
        with patch.object(qs, "Redis") as redis_cls, patch.object(qs, "Queue") as queue_cls:
            redis_cls.return_value.ping.return_value = True

            service = QueueService()

        assert service.queue is queue_cls.return_value
        redis_cls.return_value.ping.assert_called_once()


# ==========================================
# enqueue_ml_detection
# ==========================================

@pytest.mark.unit
@pytest.mark.ml
class TestEnqueueMlDetection:

    def test_encola_con_los_datos_del_reporte(self, service_con_cola):
        job = service_con_cola.enqueue_ml_detection(report_id=42, focal_scale_factor=1.5)

        assert job is service_con_cola.queue.enqueue.return_value
        kwargs = service_con_cola.queue.enqueue.call_args.kwargs
        assert kwargs["report_id"] == 42
        assert kwargs["focal_scale_factor"] == 1.5

    def test_no_pasa_la_imagen_al_worker(self, service_con_cola):
        """El worker baja la imagen de MinIO: no comparte disco con la API."""
        service_con_cola.enqueue_ml_detection(report_id=1)

        kwargs = service_con_cola.queue.enqueue.call_args.kwargs
        assert "image" not in kwargs
        assert "image_bytes" not in kwargs

    def test_aplica_timeout_y_retencion_de_resultados(self, service_con_cola):
        service_con_cola.enqueue_ml_detection(report_id=1)

        kwargs = service_con_cola.queue.enqueue.call_args.kwargs
        assert kwargs["job_timeout"] == 300
        assert kwargs["result_ttl"] == 3600
        assert kwargs["failure_ttl"] == 86400

    def test_el_factor_de_zoom_es_opcional(self, service_con_cola):
        service_con_cola.enqueue_ml_detection(report_id=7)

        assert service_con_cola.queue.enqueue.call_args.kwargs["focal_scale_factor"] is None

    def test_devuelve_none_si_encolar_falla(self, service_con_cola):
        service_con_cola.queue.enqueue.side_effect = RuntimeError("redis se cayó")

        assert service_con_cola.enqueue_ml_detection(report_id=1) is None

    def test_sin_cola_intenta_reconectar_y_devuelve_none(self, service_sin_redis):
        with patch.object(
            service_sin_redis, "_connect", side_effect=ConnectionError("sigue caído")
        ) as connect:
            resultado = service_sin_redis.enqueue_ml_detection(report_id=1)

        assert resultado is None
        connect.assert_called_once()


# ==========================================
# get_job_status
# ==========================================

@pytest.mark.unit
@pytest.mark.ml
class TestGetJobStatus:

    def test_sin_cola_devuelve_error(self, service_sin_redis):
        assert service_sin_redis.get_job_status("abc") == {"error": "Cola no disponible"}

    def test_devuelve_el_estado_de_un_job_terminado(self, service_con_cola):
        job = MagicMock()
        job.id = "job-1"
        job.get_status.return_value = "finished"
        job.is_finished = True
        job.is_failed = False
        job.result = {"damage_type": "BACHE"}
        job.created_at = datetime(2026, 1, 1, 10, 0, 0)
        job.started_at = datetime(2026, 1, 1, 10, 0, 5)
        job.ended_at = datetime(2026, 1, 1, 10, 0, 9)

        with patch.object(qs.Job, "fetch", return_value=job):
            estado = service_con_cola.get_job_status("job-1")

        assert estado["job_id"] == "job-1"
        assert estado["status"] == "finished"
        assert estado["result"] == {"damage_type": "BACHE"}
        assert estado["error"] is None
        assert estado["created_at"] == "2026-01-01T10:00:00"

    def test_un_job_fallido_expone_el_error_y_no_el_resultado(self, service_con_cola):
        job = MagicMock()
        job.id = "job-2"
        job.get_status.return_value = "failed"
        job.is_finished = False
        job.is_failed = True
        job.exc_info = "Traceback: modelo no disponible"
        job.created_at = None
        job.started_at = None
        job.ended_at = None

        with patch.object(qs.Job, "fetch", return_value=job):
            estado = service_con_cola.get_job_status("job-2")

        assert estado["result"] is None
        assert "modelo no disponible" in estado["error"]
        assert estado["created_at"] is None

    def test_un_job_inexistente_devuelve_error_en_vez_de_lanzar(self, service_con_cola):
        with patch.object(qs.Job, "fetch", side_effect=Exception("No such job")):
            estado = service_con_cola.get_job_status("no-existe")

        assert "error" in estado
        assert "No such job" in estado["error"]


# ==========================================
# get_queue_stats
# ==========================================

@pytest.mark.unit
@pytest.mark.ml
class TestGetQueueStats:

    def test_sin_cola_devuelve_error(self, service_sin_redis):
        assert service_sin_redis.get_queue_stats() == {"error": "Cola no disponible"}

    def test_devuelve_los_contadores_de_la_cola(self, service_con_cola):
        service_con_cola.queue.name = "ml_inference"
        service_con_cola.queue.count = 3
        service_con_cola.queue.__len__ = MagicMock(return_value=5)

        with patch("rq.registry.StartedJobRegistry") as started, \
             patch("rq.registry.FinishedJobRegistry") as finished, \
             patch("rq.registry.FailedJobRegistry") as failed:
            started.return_value.__len__ = MagicMock(return_value=1)
            finished.return_value.__len__ = MagicMock(return_value=10)
            failed.return_value.__len__ = MagicMock(return_value=2)

            stats = service_con_cola.get_queue_stats()

        assert stats["name"] == "ml_inference"
        assert stats["queued"] == 5
        assert stats["started"] == 1
        assert stats["finished"] == 10
        assert stats["failed"] == 2

    def test_un_fallo_de_redis_devuelve_error_en_vez_de_lanzar(self, service_con_cola):
        service_con_cola.queue.__len__ = MagicMock(side_effect=ConnectionError("redis caído"))

        stats = service_con_cola.get_queue_stats()

        assert "error" in stats


# ==========================================
# Factory
# ==========================================

@pytest.mark.unit
@pytest.mark.ml
def test_get_queue_service_devuelve_siempre_la_misma_instancia():
    assert get_queue_service() is get_queue_service()
