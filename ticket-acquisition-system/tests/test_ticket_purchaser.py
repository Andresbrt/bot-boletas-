"""Tests para TicketPurchaser."""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from src.config.constants import (
    EVENT_STATUS_AVAILABLE,
    EVENT_STATUS_SOLD_OUT,
    PURCHASE_LIMIT_REACHED,
    PURCHASE_PRICE_EXCEEDED,
    PURCHASE_SOLD_OUT,
    TICKET_STATUS_FAILED,
    TICKET_STATUS_PURCHASED,
)
from src.core.ticket_purchaser import TicketPurchaser
from src.models.event import Event
from src.models.user_account import UserAccount


def _make_event(**kwargs) -> Event:
    defaults = dict(
        event_id="evt-001",
        name="Concierto Test",
        venue="Estadio Test",
        city="Madrid",
        date=datetime(2026, 12, 31, 20, 0),
        url="https://example.com/event/1",
        status=EVENT_STATUS_AVAILABLE,
        min_price=50.0,
        max_price=150.0,
        available_tickets=100,
        total_capacity=1000,
    )
    defaults.update(kwargs)
    return Event(**defaults)


def _make_account(**kwargs) -> UserAccount:
    defaults = dict(
        account_id="acc-001",
        platform="ticketmaster",
        email="test@example.com",
        username="testuser",
        is_active=True,
        is_verified=True,
        tickets_purchased=0,
        total_spent=0.0,
    )
    defaults.update(kwargs)
    return UserAccount(**defaults)


class TestTicketPurchaser(unittest.TestCase):

    def setUp(self):
        self.browser = MagicMock()
        self.storage = MagicMock()
        self.notifier = MagicMock()
        self.purchaser = TicketPurchaser(
            browser=self.browser,
            storage=self.storage,
            notifier=self.notifier,
            max_price=200.0,
            max_per_event=4,
            timeout=10,
        )

    # ── Validaciones previas ──────────────────────────────────────────────────

    def test_fails_when_event_sold_out(self):
        event = _make_event(status=EVENT_STATUS_SOLD_OUT, available_tickets=0)
        account = _make_account()
        tickets = self.purchaser.purchase(event, account, "general")
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0].status, TICKET_STATUS_FAILED)
        self.assertEqual(tickets[0].error_message, PURCHASE_SOLD_OUT)

    def test_fails_when_price_exceeded(self):
        event = _make_event(min_price=300.0)  # mayor que max_price=200
        account = _make_account()
        tickets = self.purchaser.purchase(event, account, "vip")
        self.assertEqual(tickets[0].error_message, PURCHASE_PRICE_EXCEEDED)

    def test_fails_when_account_limit_reached(self):
        event = _make_event()
        account = _make_account(tickets_purchased=4)  # igual que max_per_event
        tickets = self.purchaser.purchase(event, account, "general", quantity=1)
        self.assertEqual(tickets[0].error_message, PURCHASE_LIMIT_REACHED)

    def test_fails_when_account_not_verified(self):
        event = _make_event()
        account = _make_account(is_verified=False)
        tickets = self.purchaser.purchase(event, account, "general")
        self.assertEqual(tickets[0].status, TICKET_STATUS_FAILED)

    # ── Flujo exitoso ─────────────────────────────────────────────────────────

    def test_successful_purchase(self):
        event = _make_event()
        account = _make_account()
        self.browser.confirm_purchase.return_value = {
            "barcode": "ABC123",
            "seat": "A1",
            "section": "Platea",
            "row": "A",
        }

        tickets = self.purchaser.purchase(event, account, "general", quantity=1)

        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0].status, TICKET_STATUS_PURCHASED)
        self.assertEqual(tickets[0].barcode, "ABC123")
        self.storage.save_ticket.assert_called_once()
        self.notifier.send_purchase_confirmation.assert_called_once()

    def test_purchase_multiple_tickets(self):
        event = _make_event()
        account = _make_account()
        self.browser.confirm_purchase.return_value = {"barcode": None, "seat": None, "section": None, "row": None}

        tickets = self.purchaser.purchase(event, account, "general", quantity=3)

        self.assertEqual(len(tickets), 3)
        self.assertTrue(all(t.status == TICKET_STATUS_PURCHASED for t in tickets))
        self.assertEqual(account.tickets_purchased, 3)

    # ── Fallos durante checkout ───────────────────────────────────────────────

    def test_browser_error_marks_ticket_failed(self):
        event = _make_event()
        account = _make_account()
        self.browser.navigate.side_effect = RuntimeError("Connection refused")

        tickets = self.purchaser.purchase(event, account, "general")

        self.assertEqual(tickets[0].status, TICKET_STATUS_FAILED)
        self.assertIn("Connection refused", tickets[0].error_message)
        self.notifier.send_purchase_confirmation.assert_not_called()


if __name__ == "__main__":
    unittest.main()
