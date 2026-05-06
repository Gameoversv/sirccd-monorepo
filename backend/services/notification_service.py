"""
Servicio de notificaciones por email (P-06)

Envía alertas de SLA a administradores y supervisores.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from core.config import settings

logger = logging.getLogger(__name__)


def _build_message(to_email: str, subject: str, body_html: str) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg.attach(MIMEText(body_html, "html", "utf-8"))
    return msg


def _send(to_email: str, subject: str, body_html: str) -> bool:
    if not settings.SMTP_ENABLED:
        logger.info("[NOTIFY] SMTP desactivado — no se envió email a %s: %s", to_email, subject)
        return False
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM, to_email, _build_message(to_email, subject, body_html).as_string())
        logger.info("[NOTIFY] Email enviado a %s: %s", to_email, subject)
        return True
    except Exception as exc:
        logger.error("[NOTIFY] Falló envío a %s: %s", to_email, exc)
        return False


def send_sla_warning(
    to_email: str,
    incident_id: int,
    address: Optional[str],
    priority: str,
    hours_remaining: float,
) -> bool:
    subject = f"[SIRCCD] Alerta SLA — Incidente #{incident_id} vence en {hours_remaining:.1f}h"
    body = f"""
    <h2>⚠️ Alerta de SLA próximo a vencer</h2>
    <p>El incidente <strong>#{incident_id}</strong> ({priority.upper()}) vencerá su SLA en
    <strong>{hours_remaining:.1f} horas</strong>.</p>
    <ul>
      <li><b>Ubicación:</b> {address or 'Sin dirección'}</li>
      <li><b>Prioridad:</b> {priority}</li>
      <li><b>Tiempo restante:</b> {hours_remaining:.1f} h</li>
    </ul>
    <p>Por favor, tome acción inmediata.</p>
    """
    return _send(to_email, subject, body)


def send_sla_breach(
    to_email: str,
    incident_id: int,
    address: Optional[str],
    priority: str,
) -> bool:
    subject = f"[SIRCCD] ❌ SLA VENCIDO — Incidente #{incident_id}"
    body = f"""
    <h2>❌ SLA Vencido</h2>
    <p>El incidente <strong>#{incident_id}</strong> ({priority.upper()}) ha superado su tiempo
    máximo de resolución.</p>
    <ul>
      <li><b>Ubicación:</b> {address or 'Sin dirección'}</li>
      <li><b>Prioridad:</b> {priority}</li>
    </ul>
    <p>Requiere atención urgente y posible escalamiento.</p>
    """
    return _send(to_email, subject, body)
