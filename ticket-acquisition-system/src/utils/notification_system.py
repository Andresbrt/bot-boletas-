"""Sistema de notificaciones multi-canal: email y consola."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from src.config.settings import (
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
    NOTIFICATION_EMAIL,
)
from src.models.event import Event
from src.models.ticket import Ticket

logger = logging.getLogger(__name__)


class NotificationSystem:
    """
    Envía alertas de disponibilidad y confirmaciones de compra.
    Actualmente soporta email (SMTP) y logging. Extensible a SMS/webhooks.
    """

    def __init__(
        self,
        smtp_host: str = SMTP_HOST,
        smtp_port: int = SMTP_PORT,
        smtp_user: str = SMTP_USER,
        smtp_password: str = SMTP_PASSWORD,
        recipient: str = NOTIFICATION_EMAIL,
    ) -> None:
        self._smtp_host = smtp_host
        self._smtp_port = smtp_port
        self._smtp_user = smtp_user
        self._smtp_password = smtp_password
        self._recipient = recipient
        self._email_enabled = bool(smtp_user and smtp_password and recipient)

    # ── Alertas de disponibilidad ─────────────────────────────────────────────

    def send_availability_alert(self, event: Event) -> None:
        subject = f"[ALERTA] Tickets disponibles: {event.name}"
        body = (
            f"Se han detectado tickets disponibles para:\n\n"
            f"  Evento : {event.name}\n"
            f"  Lugar  : {event.venue}, {event.city}\n"
            f"  Fecha  : {event.date}\n"
            f"  Precio : desde ${event.min_price:.2f}\n"
            f"  URL    : {event.url}\n"
        )
        logger.info("ALERTA DISPONIBILIDAD — %s", event.name)
        self._send_email(subject, body)

    # ── Confirmaciones de compra ──────────────────────────────────────────────

    def send_purchase_confirmation(self, ticket: Ticket, event: Event) -> None:
        subject = f"[COMPRA] Ticket adquirido: {event.name}"
        body = (
            f"Ticket comprado exitosamente:\n\n"
            f"  ID Ticket : {ticket.ticket_id}\n"
            f"  Evento    : {event.name}\n"
            f"  Categoría : {ticket.category}\n"
            f"  Asiento   : {ticket.seat_label}\n"
            f"  Precio    : ${ticket.price:.2f} {ticket.currency}\n"
            f"  Código    : {ticket.barcode or 'Pendiente'}\n"
        )
        logger.info("COMPRA CONFIRMADA — ticket=%s evento=%s", ticket.ticket_id, event.name)
        self._send_email(subject, body)

    def send_purchase_failure(self, ticket: Ticket, event: Event) -> None:
        subject = f"[ERROR] Compra fallida: {event.name}"
        body = (
            f"No se pudo completar la compra:\n\n"
            f"  ID Ticket : {ticket.ticket_id}\n"
            f"  Evento    : {event.name}\n"
            f"  Motivo    : {ticket.error_message or 'Desconocido'}\n"
        )
        logger.error("COMPRA FALLIDA — ticket=%s motivo=%s", ticket.ticket_id, ticket.error_message)
        self._send_email(subject, body)

    # ── Transporte SMTP ───────────────────────────────────────────────────────

    def _send_email(self, subject: str, body: str) -> None:
        if not self._email_enabled:
            logger.debug("Email deshabilitado. Mensaje: %s", subject)
            return
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self._smtp_user
            msg["To"] = self._recipient
            msg.attach(MIMEText(body, "plain", "utf-8"))

            with smtplib.SMTP(self._smtp_host, self._smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.login(self._smtp_user, self._smtp_password)
                server.sendmail(self._smtp_user, self._recipient, msg.as_string())
            logger.info("Email enviado: %s", subject)
        except smtplib.SMTPException as exc:
            logger.error("Error enviando email: %s", exc)
