"""Orquesta el proceso de compra de tickets."""

import logging
import uuid
from datetime import datetime
from typing import Optional

from src.config.settings import MAX_TICKET_PRICE, MAX_TICKETS_PER_EVENT, PURCHASE_TIMEOUT
from src.config.constants import (
    PURCHASE_FAILED,
    PURCHASE_LIMIT_REACHED,
    PURCHASE_PRICE_EXCEEDED,
    PURCHASE_SOLD_OUT,
    PURCHASE_SUCCESS,
    TICKET_STATUS_FAILED,
    TICKET_STATUS_PURCHASED,
)
from src.models.event import Event
from src.models.ticket import Ticket
from src.models.user_account import UserAccount
from src.utils.browser_automation import BrowserAutomation
from src.utils.data_storage import DataStorage
from src.utils.notification_system import NotificationSystem

logger = logging.getLogger(__name__)


class TicketPurchaser:
    """
    Gestiona el flujo completo de compra:
    validación de precio → selección de cuenta → checkout → registro.
    """

    def __init__(
        self,
        browser: BrowserAutomation,
        storage: DataStorage,
        notifier: NotificationSystem,
        max_price: float = MAX_TICKET_PRICE,
        max_per_event: int = MAX_TICKETS_PER_EVENT,
        timeout: int = PURCHASE_TIMEOUT,
    ) -> None:
        self._browser = browser
        self._storage = storage
        self._notifier = notifier
        self._max_price = max_price
        self._max_per_event = max_per_event
        self._timeout = timeout

    # ── Punto de entrada principal ────────────────────────────────────────────

    def purchase(
        self,
        event: Event,
        account: UserAccount,
        category: str,
        quantity: int = 1,
    ) -> list[Ticket]:
        """
        Intenta comprar `quantity` tickets del `event` con la `account`.
        Devuelve la lista de tickets resultantes (comprados o fallidos).
        """
        logger.info(
            "Iniciando compra: evento=%s cuenta=%s cantidad=%d",
            event.event_id, account.account_id, quantity,
        )

        tickets: list[Ticket] = []

        # Validaciones previas
        result_code = self._pre_validate(event, account, quantity)
        if result_code != PURCHASE_SUCCESS:
            logger.warning("Validación fallida: %s", result_code)
            ticket = self._make_failed_ticket(event, category, result_code)
            self._storage.save_ticket(ticket)
            return [ticket]

        for i in range(quantity):
            ticket = self._attempt_purchase(event, account, category, i + 1, quantity)
            tickets.append(ticket)
            self._storage.save_ticket(ticket)

            if ticket.status == TICKET_STATUS_PURCHASED:
                account.record_purchase(ticket.price)
                self._notifier.send_purchase_confirmation(ticket, event)
            else:
                logger.error("Compra fallida para ticket %d/%d", i + 1, quantity)
                break

        return tickets

    # ── Validaciones ──────────────────────────────────────────────────────────

    def _pre_validate(self, event: Event, account: UserAccount, quantity: int) -> str:
        if not event.is_available:
            return PURCHASE_SOLD_OUT
        if not account.can_purchase:
            return PURCHASE_FAILED
        if account.tickets_purchased + quantity > self._max_per_event:
            return PURCHASE_LIMIT_REACHED
        if event.min_price > self._max_price:
            return PURCHASE_PRICE_EXCEEDED
        return PURCHASE_SUCCESS

    # ── Flujo de checkout ─────────────────────────────────────────────────────

    def _attempt_purchase(
        self,
        event: Event,
        account: UserAccount,
        category: str,
        index: int,
        total: int,
    ) -> Ticket:
        ticket = Ticket(
            ticket_id=str(uuid.uuid4()),
            event_id=event.event_id,
            category=category,
            price=event.min_price,
            account_id=account.account_id,
        )

        try:
            self._browser.navigate(event.url)
            self._browser.select_category(category)
            self._browser.select_quantity(1)
            self._browser.proceed_to_checkout()
            self._browser.fill_account_credentials(account)
            confirmation = self._browser.confirm_purchase(timeout=self._timeout)

            ticket.status = TICKET_STATUS_PURCHASED
            ticket.barcode = confirmation.get("barcode")
            ticket.seat = confirmation.get("seat")
            ticket.section = confirmation.get("section")
            ticket.row = confirmation.get("row")
            ticket.purchased_at = datetime.utcnow()
            logger.info(
                "Ticket %d/%d comprado exitosamente: %s", index, total, ticket.ticket_id
            )
        except Exception as exc:  # noqa: BLE001
            ticket.status = TICKET_STATUS_FAILED
            ticket.error_message = str(exc)
            logger.error("Error durante compra %d/%d: %s", index, total, exc)

        return ticket

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _make_failed_ticket(event: Event, category: str, reason: str) -> Ticket:
        return Ticket(
            ticket_id=str(uuid.uuid4()),
            event_id=event.event_id,
            category=category,
            price=event.min_price,
            status=TICKET_STATUS_FAILED,
            error_message=reason,
        )
