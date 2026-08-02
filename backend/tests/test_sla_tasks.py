"""
Tests del job de alertas de SLA (tasks/sla_tasks.py).

Estaba en 0%. Es el job que corre en el worker RQ: si falla, nadie recibe
avisos y el fallo no aparece en ninguna respuesta HTTP.

Se mockean la sesión de base de datos y las funciones de envío: aquí interesa
la orquestación (a quién se avisa, cuántas veces, qué pasa si no hay
destinatarios), no el SMTP ni las queries.
"""

from unittest.mock import MagicMock, patch

import pytest

from models.incident import IncidentStatus, PriorityLevel
from models.user import UserRole
from tasks import sla_tasks


def make_incident(incident_id: int, address="Av. Duarte 100", priority=PriorityLevel.ALTA):
    incident = MagicMock()
    incident.id = incident_id
    incident.address = address
    incident.priority = priority
    incident.status = IncidentStatus.IN_PROGRESS
    return incident


def make_user(email: str, role=UserRole.ADMIN, is_active=True):
    user = MagicMock()
    user.email = email
    user.role = role
    user.is_active = is_active
    return user


@pytest.fixture
def fake_db():
    """Sesión mockeada; el job la abre con SessionLocal() y la cierra en finally."""
    return MagicMock()


def run_job(fake_db, admin_users, expiring, overdue):
    """Ejecuta check_sla_alerts con todas sus dependencias mockeadas."""
    fake_db.query.return_value.filter.return_value.all.return_value = admin_users

    with patch("tasks.sla_tasks.SessionLocal", return_value=fake_db), \
         patch("tasks.sla_tasks.get_expiring_incidents", return_value=expiring), \
         patch("tasks.sla_tasks.get_overdue_incidents", return_value=overdue), \
         patch("tasks.sla_tasks.get_sla_info", return_value={"hours_remaining": 2.5}), \
         patch("tasks.sla_tasks.send_sla_warning", return_value=True) as warning, \
         patch("tasks.sla_tasks.send_sla_breach", return_value=True) as breach:
        resultado = sla_tasks.check_sla_alerts()

    return resultado, warning, breach


# ==========================================
# _get_admin_emails
# ==========================================

@pytest.mark.unit
@pytest.mark.incidents
class TestGetAdminEmails:

    def test_devuelve_los_emails_de_los_destinatarios(self, fake_db):
        fake_db.query.return_value.filter.return_value.all.return_value = [
            make_user("admin@example.com"),
            make_user("supervisor@example.com", role=UserRole.SUPERVISOR),
        ]

        emails = sla_tasks._get_admin_emails(fake_db)

        assert emails == ["admin@example.com", "supervisor@example.com"]

    def test_descarta_usuarios_sin_email(self, fake_db):
        fake_db.query.return_value.filter.return_value.all.return_value = [
            make_user("admin@example.com"),
            make_user(None),
            make_user(""),
        ]

        assert sla_tasks._get_admin_emails(fake_db) == ["admin@example.com"]

    def test_sin_destinatarios_devuelve_lista_vacia(self, fake_db):
        fake_db.query.return_value.filter.return_value.all.return_value = []

        assert sla_tasks._get_admin_emails(fake_db) == []


# ==========================================
# check_sla_alerts
# ==========================================

@pytest.mark.unit
@pytest.mark.incidents
class TestCheckSlaAlerts:

    def test_sin_incidentes_no_envia_nada(self, fake_db):
        resultado, warning, breach = run_job(
            fake_db, [make_user("admin@example.com")], expiring=[], overdue=[]
        )

        assert resultado["expiring_count"] == 0
        assert resultado["overdue_count"] == 0
        assert resultado["warnings_sent"] == 0
        assert resultado["breaches_sent"] == 0
        warning.assert_not_called()
        breach.assert_not_called()

    def test_avisa_por_cada_incidente_proximo_a_vencer(self, fake_db):
        resultado, warning, _ = run_job(
            fake_db,
            [make_user("admin@example.com")],
            expiring=[make_incident(1), make_incident(2)],
            overdue=[],
        )

        assert warning.call_count == 2
        assert resultado["warnings_sent"] == 2
        assert resultado["expiring_count"] == 2

    def test_avisa_por_cada_incidente_vencido(self, fake_db):
        resultado, _, breach = run_job(
            fake_db,
            [make_user("admin@example.com")],
            expiring=[],
            overdue=[make_incident(9)],
        )

        assert breach.call_count == 1
        assert resultado["breaches_sent"] == 1
        assert resultado["overdue_count"] == 1

    def test_notifica_a_todos_los_destinatarios(self, fake_db):
        """2 incidentes x 3 destinatarios = 6 emails."""
        resultado, warning, _ = run_job(
            fake_db,
            [
                make_user("admin@example.com"),
                make_user("sup1@example.com", role=UserRole.SUPERVISOR),
                make_user("sup2@example.com", role=UserRole.SUPERVISOR),
            ],
            expiring=[make_incident(1), make_incident(2)],
            overdue=[],
        )

        assert warning.call_count == 6
        assert resultado["warnings_sent"] == 6

    def test_sin_destinatarios_no_revienta_y_no_cuenta_envios(self, fake_db):
        resultado, warning, breach = run_job(
            fake_db, [], expiring=[make_incident(1)], overdue=[make_incident(2)]
        )

        assert resultado["expiring_count"] == 1
        assert resultado["overdue_count"] == 1
        assert resultado["warnings_sent"] == 0
        assert resultado["breaches_sent"] == 0
        warning.assert_not_called()
        breach.assert_not_called()

    def test_los_envios_fallidos_no_se_cuentan_como_enviados(self, fake_db):
        fake_db.query.return_value.filter.return_value.all.return_value = [
            make_user("admin@example.com")
        ]

        with patch("tasks.sla_tasks.SessionLocal", return_value=fake_db), \
             patch("tasks.sla_tasks.get_expiring_incidents", return_value=[make_incident(1)]), \
             patch("tasks.sla_tasks.get_overdue_incidents", return_value=[]), \
             patch("tasks.sla_tasks.get_sla_info", return_value={"hours_remaining": 1.0}), \
             patch("tasks.sla_tasks.send_sla_warning", return_value=False):
            resultado = sla_tasks.check_sla_alerts()

        assert resultado["expiring_count"] == 1
        assert resultado["warnings_sent"] == 0

    def test_pasa_los_datos_del_incidente_al_email(self, fake_db):
        _, warning, _ = run_job(
            fake_db,
            [make_user("admin@example.com")],
            expiring=[make_incident(55, address="Calle Luna 8", priority=PriorityLevel.CRITICA)],
            overdue=[],
        )

        kwargs = warning.call_args.kwargs
        assert kwargs["incident_id"] == 55
        assert kwargs["address"] == "Calle Luna 8"
        assert kwargs["priority"] == PriorityLevel.CRITICA.value
        assert kwargs["hours_remaining"] == 2.5

    def test_hours_remaining_nulo_se_normaliza_a_cero(self, fake_db):
        fake_db.query.return_value.filter.return_value.all.return_value = [
            make_user("admin@example.com")
        ]

        with patch("tasks.sla_tasks.SessionLocal", return_value=fake_db), \
             patch("tasks.sla_tasks.get_expiring_incidents", return_value=[make_incident(1)]), \
             patch("tasks.sla_tasks.get_overdue_incidents", return_value=[]), \
             patch("tasks.sla_tasks.get_sla_info", return_value={"hours_remaining": None}), \
             patch("tasks.sla_tasks.send_sla_warning", return_value=True) as warning:
            sla_tasks.check_sla_alerts()

        assert warning.call_args.kwargs["hours_remaining"] == 0.0

    def test_siempre_cierra_la_sesion(self, fake_db):
        run_job(fake_db, [make_user("admin@example.com")], expiring=[], overdue=[])

        fake_db.close.assert_called_once()

    def test_cierra_la_sesion_aunque_el_job_falle(self, fake_db):
        fake_db.query.return_value.filter.return_value.all.return_value = []

        with patch("tasks.sla_tasks.SessionLocal", return_value=fake_db), \
             patch("tasks.sla_tasks.get_expiring_incidents", side_effect=RuntimeError("db caída")):
            with pytest.raises(RuntimeError):
                sla_tasks.check_sla_alerts()

        fake_db.close.assert_called_once()

    def test_el_resumen_incluye_marca_de_tiempo(self, fake_db):
        resultado, _, _ = run_job(
            fake_db, [make_user("admin@example.com")], expiring=[], overdue=[]
        )

        assert "checked_at" in resultado
        # ISO 8601: parseable de vuelta
        from datetime import datetime
        datetime.fromisoformat(resultado["checked_at"])
