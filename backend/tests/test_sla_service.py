"""
Tests del servicio de SLA (services/sla_service.py).

Este módulo estaba en 0% de cobertura: las alertas de vencimiento son de las
pocas piezas del sistema donde un fallo silencioso no lo nota nadie hasta que
un incidente ya venció.

Las funciones de consulta (`get_expiring_incidents`, `get_overdue_incidents`)
no se cubren aquí: construyen queries sobre la tabla `incidents`, que no
existe en el entorno SQLite de tests porque usa columnas PostGIS. Ver
docs/backend/TESTING.md.
"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from models.incident import Incident, IncidentStatus, PriorityLevel
from models.sla_config import SLAConfig
from services import sla_service
from tests.conftest import TestingSessionLocal, engine


# ==========================================
# Fixtures
# ==========================================

@pytest.fixture
def sla_db():
    """Sesión con la tabla `sla_configs` creada (no usa PostGIS)."""
    SLAConfig.__table__.create(bind=engine, checkfirst=True)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        SLAConfig.__table__.drop(bind=engine, checkfirst=True)


def make_incident(**overrides) -> Incident:
    """
    Incidente en memoria, sin persistir.

    No se puede insertar en SQLite porque `incidents.location` es Geography,
    pero el servicio solo lee atributos, así que basta con el objeto.
    """
    defaults = {
        "id": 1,
        "priority": PriorityLevel.MEDIA,
        "status": IncidentStatus.IN_PROGRESS,
        "started_at": datetime.utcnow() - timedelta(hours=1),
        "sla_deadline": None,
    }
    defaults.update(overrides)
    incident = Incident()
    for field, value in defaults.items():
        setattr(incident, field, value)
    return incident


# ==========================================
# get_sla_hours
# ==========================================

@pytest.mark.unit
@pytest.mark.incidents
class TestGetSlaHours:

    @pytest.mark.parametrize(
        "priority,expected_hours",
        [
            (PriorityLevel.BAJA, 72.0),
            (PriorityLevel.MEDIA, 48.0),
            (PriorityLevel.ALTA, 24.0),
            (PriorityLevel.CRITICA, 8.0),
        ],
    )
    def test_usa_los_defaults_cuando_no_hay_config(
        self, sla_db: Session, priority: PriorityLevel, expected_hours: float
    ):
        assert sla_service.get_sla_hours(sla_db, priority) == expected_hours

    def test_la_config_en_base_de_datos_gana_sobre_los_defaults(self, sla_db: Session):
        sla_db.add(
            SLAConfig(
                sla_hours_baja=100.0,
                sla_hours_media=10.0,
                sla_hours_alta=5.0,
                sla_hours_critica=1.0,
                warning_threshold_pct=0.5,
            )
        )
        sla_db.commit()

        assert sla_service.get_sla_hours(sla_db, PriorityLevel.MEDIA) == 10.0
        assert sla_service.get_sla_hours(sla_db, PriorityLevel.CRITICA) == 1.0

    def test_toma_la_primera_config_por_id_cuando_hay_varias(self, sla_db: Session):
        sla_db.add(SLAConfig(sla_hours_media=11.0))
        sla_db.add(SLAConfig(sla_hours_media=99.0))
        sla_db.commit()

        assert sla_service.get_sla_hours(sla_db, PriorityLevel.MEDIA) == 11.0


# ==========================================
# compute_sla_deadline / set_sla_deadline
# ==========================================

@pytest.mark.unit
@pytest.mark.incidents
class TestDeadline:

    def test_suma_las_horas_de_sla_al_inicio(self):
        started = datetime(2026, 1, 1, 12, 0, 0)
        assert sla_service.compute_sla_deadline(started, 24.0) == datetime(2026, 1, 2, 12, 0, 0)

    def test_admite_horas_fraccionarias(self):
        started = datetime(2026, 1, 1, 12, 0, 0)
        assert sla_service.compute_sla_deadline(started, 1.5) == datetime(2026, 1, 1, 13, 30, 0)

    def test_set_sla_deadline_asigna_segun_prioridad(self, sla_db: Session):
        started = datetime(2026, 1, 1, 0, 0, 0)
        incident = make_incident(priority=PriorityLevel.ALTA, started_at=started)

        sla_service.set_sla_deadline(incident, sla_db)

        # ALTA por defecto son 24h
        assert incident.sla_deadline == started + timedelta(hours=24)

    def test_set_sla_deadline_no_hace_nada_sin_started_at(self, sla_db: Session):
        incident = make_incident(started_at=None, sla_deadline=None)

        sla_service.set_sla_deadline(incident, sla_db)

        assert incident.sla_deadline is None


# ==========================================
# get_sla_status
# ==========================================

@pytest.mark.unit
@pytest.mark.incidents
class TestGetSlaStatus:

    @pytest.mark.parametrize(
        "terminal_status",
        [IncidentStatus.RESOLVED, IncidentStatus.VERIFIED, IncidentStatus.CLOSED],
    )
    def test_los_estados_terminales_son_completed(
        self, sla_db: Session, terminal_status: IncidentStatus
    ):
        incident = make_incident(status=terminal_status)

        assert sla_service.get_sla_status(incident, sla_db) == "completed"

    def test_completed_tiene_prioridad_sobre_un_deadline_vencido(self, sla_db: Session):
        incident = make_incident(
            status=IncidentStatus.CLOSED,
            started_at=datetime.utcnow() - timedelta(days=30),
            sla_deadline=datetime.utcnow() - timedelta(days=20),
        )

        assert sla_service.get_sla_status(incident, sla_db) == "completed"

    def test_sin_started_at_es_not_started(self, sla_db: Session):
        incident = make_incident(status=IncidentStatus.OPEN, started_at=None)

        assert sla_service.get_sla_status(incident, sla_db) == "not_started"

    def test_recien_empezado_es_on_track(self, sla_db: Session):
        # MEDIA = 48h; 1h transcurrida está muy por debajo del umbral de 80%
        incident = make_incident(started_at=datetime.utcnow() - timedelta(hours=1))

        assert sla_service.get_sla_status(incident, sla_db) == "on_track"

    def test_pasado_el_umbral_de_aviso_es_warning(self, sla_db: Session):
        # MEDIA = 48h, umbral 0.8 => a partir de 38.4h transcurridas
        started = datetime.utcnow() - timedelta(hours=40)
        incident = make_incident(
            started_at=started,
            sla_deadline=started + timedelta(hours=48),
        )

        assert sla_service.get_sla_status(incident, sla_db) == "warning"

    def test_deadline_superado_es_overdue(self, sla_db: Session):
        started = datetime.utcnow() - timedelta(hours=50)
        incident = make_incident(
            started_at=started,
            sla_deadline=started + timedelta(hours=48),
        )

        assert sla_service.get_sla_status(incident, sla_db) == "overdue"

    def test_sin_deadline_persistido_lo_calcula_al_vuelo(self, sla_db: Session):
        # Sin sla_deadline en el incidente, el estado se deduce de started_at
        incident = make_incident(
            started_at=datetime.utcnow() - timedelta(hours=60),
            sla_deadline=None,
        )

        assert sla_service.get_sla_status(incident, sla_db) == "overdue"

    def test_el_umbral_de_aviso_configurable_se_respeta(self, sla_db: Session):
        sla_db.add(SLAConfig(sla_hours_media=48.0, warning_threshold_pct=0.25))
        sla_db.commit()

        # 20h de 48h = 41%: on_track con el umbral por defecto (80%),
        # warning con el umbral configurado (25%)
        started = datetime.utcnow() - timedelta(hours=20)
        incident = make_incident(
            started_at=started,
            sla_deadline=started + timedelta(hours=48),
        )

        assert sla_service.get_sla_status(incident, sla_db) == "warning"


# ==========================================
# get_sla_info
# ==========================================

@pytest.mark.unit
@pytest.mark.incidents
class TestGetSlaInfo:

    def test_devuelve_el_resumen_completo(self, sla_db: Session):
        started = datetime.utcnow() - timedelta(hours=1)
        incident = make_incident(
            id=42,
            priority=PriorityLevel.ALTA,
            started_at=started,
            sla_deadline=started + timedelta(hours=24),
        )

        info = sla_service.get_sla_info(incident, sla_db)

        assert info["incident_id"] == 42
        assert info["status"] == "on_track"
        assert info["sla_hours"] == 24.0
        assert info["priority"] == PriorityLevel.ALTA.value
        assert info["started_at"] == started

    def test_las_horas_restantes_son_positivas_dentro_del_plazo(self, sla_db: Session):
        started = datetime.utcnow() - timedelta(hours=2)
        incident = make_incident(
            started_at=started,
            sla_deadline=datetime.utcnow() + timedelta(hours=10),
        )

        info = sla_service.get_sla_info(incident, sla_db)

        assert info["hours_remaining"] == pytest.approx(10.0, abs=0.1)

    def test_las_horas_restantes_son_negativas_si_ya_vencio(self, sla_db: Session):
        started = datetime.utcnow() - timedelta(hours=50)
        incident = make_incident(
            started_at=started,
            sla_deadline=datetime.utcnow() - timedelta(hours=5),
        )

        info = sla_service.get_sla_info(incident, sla_db)

        assert info["hours_remaining"] == pytest.approx(-5.0, abs=0.1)
        assert info["status"] == "overdue"

    def test_no_calcula_horas_restantes_en_incidentes_cerrados(self, sla_db: Session):
        incident = make_incident(
            status=IncidentStatus.CLOSED,
            started_at=datetime.utcnow() - timedelta(hours=2),
            sla_deadline=datetime.utcnow() + timedelta(hours=10),
        )

        info = sla_service.get_sla_info(incident, sla_db)

        assert info["hours_remaining"] is None
        assert info["status"] == "completed"

    def test_no_calcula_horas_restantes_sin_deadline(self, sla_db: Session):
        incident = make_incident(sla_deadline=None)

        info = sla_service.get_sla_info(incident, sla_db)

        assert info["hours_remaining"] is None
