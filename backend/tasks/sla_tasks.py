"""
Tarea RQ: monitoreo periódico de SLAs (P-06)

Ejecutar con el worker RQ o encolar manualmente:
  rq enqueue tasks.sla_tasks.check_sla_alerts
"""

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from db.session import SessionLocal
from models.incident import Incident, IncidentStatus
from models.user import User, UserRole
from services.sla_service import get_expiring_incidents, get_overdue_incidents, get_sla_info
from services.notification_service import send_sla_warning, send_sla_breach
from core.config import settings

logger = logging.getLogger(__name__)


def _get_admin_emails(db: Session) -> list[str]:
    users = db.query(User).filter(
        User.role.in_([UserRole.ADMIN, UserRole.SUPERVISOR]),
        User.is_active == True,
    ).all()
    return [u.email for u in users if u.email]


def check_sla_alerts() -> dict:
    """
    Job principal: detecta incidentes en warning u overdue y envía emails.
    Devuelve un resumen de acciones tomadas.
    """
    db: Session = SessionLocal()
    warnings_sent = 0
    breaches_sent = 0

    try:
        admin_emails = _get_admin_emails(db)
        if not admin_emails:
            logger.warning("[SLA] No hay admins/supervisores activos con email.")

        # Incidentes próximos a vencer
        expiring = get_expiring_incidents(db, within_hours=settings.SLA_WARNING_HOURS_BEFORE)
        for incident in expiring:
            info = get_sla_info(incident, db)
            hours_remaining = info.get("hours_remaining") or 0.0
            for email in admin_emails:
                sent = send_sla_warning(
                    to_email=email,
                    incident_id=incident.id,
                    address=incident.address,
                    priority=incident.priority.value,
                    hours_remaining=hours_remaining,
                )
                if sent:
                    warnings_sent += 1

        # Incidentes que ya vencieron el SLA
        overdue = get_overdue_incidents(db)
        for incident in overdue:
            for email in admin_emails:
                sent = send_sla_breach(
                    to_email=email,
                    incident_id=incident.id,
                    address=incident.address,
                    priority=incident.priority.value,
                )
                if sent:
                    breaches_sent += 1

        logger.info(
            "[SLA] check_sla_alerts: %d expiring, %d overdue | emails: %d warnings, %d breaches",
            len(expiring), len(overdue), warnings_sent, breaches_sent,
        )
        return {
            "checked_at": datetime.utcnow().isoformat(),
            "expiring_count": len(expiring),
            "overdue_count": len(overdue),
            "warnings_sent": warnings_sent,
            "breaches_sent": breaches_sent,
        }
    finally:
        db.close()
