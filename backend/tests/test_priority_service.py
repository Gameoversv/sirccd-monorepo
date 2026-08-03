"""
Tests del servicio de priorización (services/priority_service.py).

Estaba en 15.91% de cobertura. Este servicio decide qué se repara primero,
así que un cambio silencioso en los tramos de score reordena la cola de
trabajo real del equipo operativo.

Se cubren las funciones de scoring puro y la validación de transiciones. Lo
que consulta la tabla `incidents` o `pois` (`_count_nearby_pois`,
`_count_nearby_duplicates`, `recalculate_priority`, `update_incident_status`)
queda fuera: esas tablas usan PostGIS y no existen en el entorno SQLite de
tests. Ver docs/backend/TESTING.md.
"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from models.incident import Incident, IncidentStatus, PriorityLevel
from models.priority_setting import PrioritySetting
from models.report import DamageType, SeverityLevel
from services.priority_service import PriorityService, get_priority_service
from tests.conftest import TestingSessionLocal, engine


# ==========================================
# Fixtures
# ==========================================

@pytest.fixture
def priority_db():
    """Sesión con la tabla `priority_settings` creada (no usa PostGIS)."""
    PrioritySetting.__table__.create(bind=engine, checkfirst=True)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        PrioritySetting.__table__.drop(bind=engine, checkfirst=True)


@pytest.fixture
def service(priority_db: Session) -> PriorityService:
    return PriorityService(priority_db)


def make_incident(**overrides) -> Incident:
    """Incidente en memoria; `incidents` no se puede crear en SQLite."""
    defaults = {
        "id": 1,
        "severity": SeverityLevel.MEDIA,
        "damage_type": DamageType.BACHE,
        "created_at": datetime.utcnow(),
        "status": IncidentStatus.OPEN,
        "priority": PriorityLevel.MEDIA,
    }
    defaults.update(overrides)
    incident = Incident()
    for field, value in defaults.items():
        setattr(incident, field, value)
    return incident


# ==========================================
# Scores por tramo
# ==========================================

@pytest.mark.unit
@pytest.mark.incidents
class TestScoresPorTramo:

    @pytest.mark.parametrize(
        "pois,expected",
        [(0, 0.0), (1, 40.0), (2, 40.0), (3, 70.0), (5, 70.0), (6, 100.0), (50, 100.0)],
    )
    def test_score_de_ubicacion_por_cantidad_de_pois(
        self, service: PriorityService, pois: int, expected: float
    ):
        assert service._calculate_location_score(pois) == expected

    @pytest.mark.parametrize(
        "duplicates,expected",
        [(0, 0.0), (1, 30.0), (2, 30.0), (3, 60.0), (5, 60.0), (6, 100.0), (99, 100.0)],
    )
    def test_score_de_duplicados_por_cantidad(
        self, service: PriorityService, duplicates: int, expected: float
    ):
        assert service._calculate_duplicate_score(duplicates) == expected

    def test_el_score_de_edad_crece_con_el_tiempo(self, service: PriorityService):
        reciente = service._calculate_age_score(datetime.utcnow())
        medio = service._calculate_age_score(datetime.utcnow() - timedelta(hours=84))
        viejo = service._calculate_age_score(datetime.utcnow() - timedelta(hours=167))

        assert reciente < medio < viejo
        assert reciente == pytest.approx(0.0, abs=0.5)
        assert medio == pytest.approx(50.0, abs=0.5)

    def test_el_score_de_edad_se_satura_a_los_7_dias(self, service: PriorityService):
        assert service._calculate_age_score(datetime.utcnow() - timedelta(hours=168)) == 100.0
        assert service._calculate_age_score(datetime.utcnow() - timedelta(days=365)) == 100.0


# ==========================================
# Score -> nivel de prioridad
# ==========================================

@pytest.mark.unit
@pytest.mark.incidents
class TestNivelDePrioridad:

    @pytest.mark.parametrize(
        "score,expected",
        [
            (0.0, PriorityLevel.BAJA),
            (24.99, PriorityLevel.BAJA),
            (25.0, PriorityLevel.MEDIA),
            (49.99, PriorityLevel.MEDIA),
            (50.0, PriorityLevel.ALTA),
            (74.99, PriorityLevel.ALTA),
            (75.0, PriorityLevel.CRITICA),
            (100.0, PriorityLevel.CRITICA),
        ],
    )
    def test_los_limites_de_cada_tramo(
        self, service: PriorityService, score: float, expected: PriorityLevel
    ):
        assert service._score_to_priority_level(score) == expected


# ==========================================
# Pesos efectivos
# ==========================================

@pytest.mark.unit
@pytest.mark.incidents
class TestPesosEfectivos:

    def test_sin_config_usa_los_pesos_de_clase(self, service: PriorityService):
        weights = service._effective_weights()

        # approx y no ==: incluso sin config los pesos pasan por la
        # normalización, y 0.35+0.20+0.15+0.20+0.10 no da exactamente 1.0 en
        # coma flotante, así que el resultado arrastra un epsilon.
        assert weights == pytest.approx((0.35, 0.20, 0.15, 0.20, 0.10))
        assert sum(weights) == pytest.approx(1.0)

    def test_los_pesos_de_la_config_se_normalizan_a_1(
        self, service: PriorityService, priority_db: Session
    ):
        # Suman 2.0, no 1.0: el servicio debe normalizarlos
        priority_db.add(
            PrioritySetting(
                weight_severity=0.7,
                weight_age=0.4,
                weight_damage_type=0.3,
                weight_location=0.4,
                weight_duplicates=0.2,
            )
        )
        priority_db.commit()

        weights = service._effective_weights()

        assert sum(weights) == pytest.approx(1.0)
        assert weights[0] == pytest.approx(0.35)

    def test_pesos_en_cero_caen_a_los_defaults(
        self, service: PriorityService, priority_db: Session
    ):
        priority_db.add(
            PrioritySetting(
                weight_severity=0.0,
                weight_age=0.0,
                weight_damage_type=0.0,
                weight_location=0.0,
                weight_duplicates=0.0,
            )
        )
        priority_db.commit()

        assert service._effective_weights() == (0.35, 0.20, 0.15, 0.20, 0.10)


# ==========================================
# calculate_priority_score
# ==========================================

@pytest.mark.unit
@pytest.mark.incidents
class TestCalculatePriorityScore:

    def test_el_peor_caso_da_critica(self, service: PriorityService):
        incident = make_incident(
            severity=SeverityLevel.ALTA,
            damage_type=DamageType.BACHE,
            created_at=datetime.utcnow() - timedelta(days=10),
        )

        score, level = service.calculate_priority_score(
            incident, nearby_pois_count=10, nearby_duplicates_count=10
        )

        # 100*0.35 + 100*0.20 + 80*0.15 + 100*0.20 + 100*0.10 = 97.0
        assert score == pytest.approx(97.0, abs=0.01)
        assert level == PriorityLevel.CRITICA

    def test_el_mejor_caso_da_baja(self, service: PriorityService):
        incident = make_incident(
            severity=SeverityLevel.BAJA,
            damage_type=DamageType.GRIETA,
            created_at=datetime.utcnow(),
        )

        score, level = service.calculate_priority_score(
            incident, nearby_pois_count=0, nearby_duplicates_count=0
        )

        # 25*0.35 + ~0*0.20 + 60*0.15 + 0 + 0 = 17.75
        assert score == pytest.approx(17.75, abs=0.5)
        assert level == PriorityLevel.BAJA

    def test_mas_pois_cercanos_nunca_baja_el_score(self, service: PriorityService):
        incident = make_incident()

        sin_pois, _ = service.calculate_priority_score(
            incident, nearby_pois_count=0, nearby_duplicates_count=0
        )
        con_pois, _ = service.calculate_priority_score(
            incident, nearby_pois_count=8, nearby_duplicates_count=0
        )

        assert con_pois > sin_pois

    def test_un_bache_puntua_mas_que_una_grieta_en_igualdad(self, service: PriorityService):
        base = {"created_at": datetime.utcnow(), "severity": SeverityLevel.MEDIA}
        bache, _ = service.calculate_priority_score(
            make_incident(damage_type=DamageType.BACHE, **base),
            nearby_pois_count=0,
            nearby_duplicates_count=0,
        )
        grieta, _ = service.calculate_priority_score(
            make_incident(damage_type=DamageType.GRIETA, **base),
            nearby_pois_count=0,
            nearby_duplicates_count=0,
        )

        assert bache > grieta

    def test_el_score_siempre_queda_entre_0_y_100(self, service: PriorityService):
        incident = make_incident(
            severity=SeverityLevel.ALTA,
            created_at=datetime.utcnow() - timedelta(days=400),
        )

        score, _ = service.calculate_priority_score(
            incident, nearby_pois_count=999, nearby_duplicates_count=999
        )

        assert 0.0 <= score <= 100.0


# ==========================================
# Transiciones de estado
# ==========================================

@pytest.mark.unit
@pytest.mark.incidents
class TestTransicionesDeEstado:

    @pytest.mark.parametrize(
        "current,new",
        [
            (IncidentStatus.OPEN, IncidentStatus.IN_PROGRESS),
            (IncidentStatus.OPEN, IncidentStatus.CLOSED),
            (IncidentStatus.IN_PROGRESS, IncidentStatus.RESOLVED),
            (IncidentStatus.IN_PROGRESS, IncidentStatus.OPEN),
            (IncidentStatus.RESOLVED, IncidentStatus.VERIFIED),
            (IncidentStatus.RESOLVED, IncidentStatus.IN_PROGRESS),
            (IncidentStatus.VERIFIED, IncidentStatus.CLOSED),
            (IncidentStatus.VERIFIED, IncidentStatus.RESOLVED),
        ],
    )
    def test_transiciones_permitidas(
        self, service: PriorityService, current: IncidentStatus, new: IncidentStatus
    ):
        assert service._is_valid_transition(current, new) is True

    @pytest.mark.parametrize(
        "current,new",
        [
            (IncidentStatus.OPEN, IncidentStatus.RESOLVED),
            (IncidentStatus.OPEN, IncidentStatus.VERIFIED),
            (IncidentStatus.IN_PROGRESS, IncidentStatus.VERIFIED),
            (IncidentStatus.IN_PROGRESS, IncidentStatus.CLOSED),
            (IncidentStatus.RESOLVED, IncidentStatus.OPEN),
            (IncidentStatus.VERIFIED, IncidentStatus.OPEN),
        ],
    )
    def test_transiciones_prohibidas(
        self, service: PriorityService, current: IncidentStatus, new: IncidentStatus
    ):
        assert service._is_valid_transition(current, new) is False

    def test_closed_es_estado_final(self, service: PriorityService):
        for destino in [
            IncidentStatus.OPEN,
            IncidentStatus.IN_PROGRESS,
            IncidentStatus.RESOLVED,
            IncidentStatus.VERIFIED,
        ]:
            assert service._is_valid_transition(IncidentStatus.CLOSED, destino) is False

    def test_reasignar_el_mismo_estado_se_permite(self, service: PriorityService):
        for estado in IncidentStatus:
            assert service._is_valid_transition(estado, estado) is True


# ==========================================
# Factory
# ==========================================

@pytest.mark.unit
def test_get_priority_service_devuelve_el_servicio_con_su_sesion(priority_db: Session):
    service = get_priority_service(priority_db)

    assert isinstance(service, PriorityService)
    assert service.db is priority_db
