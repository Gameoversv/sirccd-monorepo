"""
Servicio de monitoreo de SLAs (P-06)

Calcula deadlines, estados de SLA y detecta incidentes próximos a vencer.
"""

from datetime import datetime, timedelta
from typing import Literal, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models.incident import Incident, IncidentStatus, PriorityLevel
from models.sla_config import SLAConfig

SLAStatus = Literal["not_started", "on_track", "warning", "overdue", "completed"]

# Defaults usados cuando no hay SLAConfig en base de datos
DEFAULT_SLA_HOURS: dict[str, float] = {
    PriorityLevel.BAJA: 72.0,
    PriorityLevel.MEDIA: 48.0,
    PriorityLevel.ALTA: 24.0,
    PriorityLevel.CRITICA: 8.0,
}
DEFAULT_WARNING_THRESHOLD = 0.8


def _get_config(db: Session) -> Optional[SLAConfig]:
    return db.query(SLAConfig).order_by(SLAConfig.id.asc()).first()


def get_sla_hours(db: Session, priority: PriorityLevel) -> float:
    cfg = _get_config(db)
    if cfg is None:
        return DEFAULT_SLA_HOURS.get(priority, 48.0)
    mapping = {
        PriorityLevel.BAJA: cfg.sla_hours_baja,
        PriorityLevel.MEDIA: cfg.sla_hours_media,
        PriorityLevel.ALTA: cfg.sla_hours_alta,
        PriorityLevel.CRITICA: cfg.sla_hours_critica,
    }
    return mapping.get(priority, 48.0)


def compute_sla_deadline(started_at: datetime, sla_hours: float) -> datetime:
    return started_at + timedelta(hours=sla_hours)


def get_sla_status(incident: Incident, db: Session) -> SLAStatus:
    """Devuelve el estado SLA actual de un incidente."""
    terminal = {IncidentStatus.RESOLVED, IncidentStatus.VERIFIED, IncidentStatus.CLOSED}
    if incident.status in terminal:
        return "completed"

    if incident.started_at is None:
        return "not_started"

    cfg = _get_config(db)
    sla_hours = get_sla_hours(db, incident.priority)
    threshold = cfg.warning_threshold_pct if cfg else DEFAULT_WARNING_THRESHOLD

    deadline = incident.sla_deadline or compute_sla_deadline(incident.started_at, sla_hours)
    now = datetime.utcnow()

    if now >= deadline:
        return "overdue"

    elapsed = (now - incident.started_at).total_seconds() / 3600
    total = sla_hours
    if elapsed / total >= threshold:
        return "warning"

    return "on_track"


def get_sla_info(incident: Incident, db: Session) -> dict:
    """Devuelve info completa de SLA para un incidente."""
    sla_hours = get_sla_hours(db, incident.priority)
    sla_status = get_sla_status(incident, db)

    hours_remaining: Optional[float] = None
    deadline = incident.sla_deadline
    if deadline and incident.started_at and incident.status not in {
        IncidentStatus.RESOLVED, IncidentStatus.VERIFIED, IncidentStatus.CLOSED
    }:
        remaining = (deadline - datetime.utcnow()).total_seconds() / 3600
        hours_remaining = round(remaining, 2)

    return {
        "incident_id": incident.id,
        "status": sla_status,
        "sla_deadline": deadline,
        "hours_remaining": hours_remaining,
        "sla_hours": sla_hours,
        "priority": incident.priority.value,
        "started_at": incident.started_at,
    }


def get_expiring_incidents(db: Session, within_hours: float) -> list[Incident]:
    """Incidentes activos cuyo deadline vence en las próximas `within_hours` horas."""
    now = datetime.utcnow()
    cutoff = now + timedelta(hours=within_hours)

    return (
        db.query(Incident)
        .filter(
            and_(
                Incident.status == IncidentStatus.IN_PROGRESS,
                Incident.sla_deadline.isnot(None),
                Incident.sla_deadline > now,
                Incident.sla_deadline <= cutoff,
            )
        )
        .all()
    )


def get_overdue_incidents(db: Session) -> list[Incident]:
    """Incidentes activos que ya superaron su deadline SLA."""
    now = datetime.utcnow()
    active = {IncidentStatus.OPEN, IncidentStatus.IN_PROGRESS}
    return (
        db.query(Incident)
        .filter(
            and_(
                Incident.status.in_(list(active)),
                Incident.sla_deadline.isnot(None),
                Incident.sla_deadline < now,
            )
        )
        .all()
    )


def set_sla_deadline(incident: Incident, db: Session) -> None:
    """Calcula y asigna el sla_deadline a partir de started_at."""
    if incident.started_at is None:
        return
    sla_hours = get_sla_hours(db, incident.priority)
    incident.sla_deadline = compute_sla_deadline(incident.started_at, sla_hours)
