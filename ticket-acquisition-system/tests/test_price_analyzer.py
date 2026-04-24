"""Tests para PriceAnalyzer."""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from src.config.constants import EVENT_STATUS_AVAILABLE, TICKET_STATUS_PURCHASED
from src.core.price_analyzer import PriceAnalyzer
from src.models.event import Event
from src.models.ticket import Ticket


def _make_event(min_price: float = 50.0, max_price: float = 200.0) -> Event:
    return Event(
        event_id="evt-001",
        name="Concierto Test",
        venue="Estadio Test",
        city="Madrid",
        date=datetime(2026, 12, 31, 20, 0),
        url="https://example.com/event/1",
        status=EVENT_STATUS_AVAILABLE,
        min_price=min_price,
        max_price=max_price,
        available_tickets=100,
        total_capacity=1000,
    )


def _make_ticket(price: float, purchased: bool = True, days_ago: int = 0) -> Ticket:
    purchased_at = datetime.utcnow() - timedelta(days=days_ago) if purchased else None
    return Ticket(
        ticket_id=f"t-{price}-{days_ago}",
        event_id="evt-001",
        category="general",
        price=price,
        status=TICKET_STATUS_PURCHASED if purchased else "failed",
        purchased_at=purchased_at,
    )


class TestPriceAnalyzer(unittest.TestCase):

    def setUp(self):
        self.storage = MagicMock()
        self.analyzer = PriceAnalyzer(storage=self.storage, max_price=300.0)

    # ── is_price_acceptable ───────────────────────────────────────────────────

    def test_price_below_max_is_acceptable(self):
        self.storage.get_tickets_for_event.return_value = []
        event = _make_event()
        self.assertTrue(self.analyzer.is_price_acceptable(event, 100.0))

    def test_price_above_max_is_not_acceptable(self):
        self.storage.get_tickets_for_event.return_value = []
        event = _make_event()
        self.assertFalse(self.analyzer.is_price_acceptable(event, 350.0))

    def test_price_above_150_percent_avg_is_not_acceptable(self):
        tickets = [_make_ticket(100.0), _make_ticket(100.0), _make_ticket(100.0)]
        self.storage.get_tickets_for_event.return_value = tickets
        event = _make_event()
        # 100 * 1.5 = 150 → 160 debería fallar
        self.assertFalse(self.analyzer.is_price_acceptable(event, 160.0))

    # ── get_average_price ─────────────────────────────────────────────────────

    def test_average_price_no_history(self):
        self.storage.get_tickets_for_event.return_value = []
        self.assertIsNone(self.analyzer.get_average_price("evt-001"))

    def test_average_price_with_history(self):
        tickets = [_make_ticket(100.0), _make_ticket(200.0), _make_ticket(150.0)]
        self.storage.get_tickets_for_event.return_value = tickets
        avg = self.analyzer.get_average_price("evt-001")
        self.assertAlmostEqual(avg, 150.0)

    def test_average_ignores_failed_tickets(self):
        tickets = [_make_ticket(100.0), _make_ticket(999.0, purchased=False)]
        self.storage.get_tickets_for_event.return_value = tickets
        avg = self.analyzer.get_average_price("evt-001")
        self.assertAlmostEqual(avg, 100.0)

    # ── get_price_stats ───────────────────────────────────────────────────────

    def test_price_stats_empty(self):
        self.storage.get_tickets_for_event.return_value = []
        stats = self.analyzer.get_price_stats("evt-001")
        self.assertEqual(stats["count"], 0)
        self.assertIsNone(stats["mean"])

    def test_price_stats_with_data(self):
        tickets = [_make_ticket(p) for p in [50, 100, 150, 200, 250]]
        self.storage.get_tickets_for_event.return_value = tickets
        stats = self.analyzer.get_price_stats("evt-001")
        self.assertEqual(stats["count"], 5)
        self.assertAlmostEqual(stats["mean"], 150.0)
        self.assertEqual(stats["min"], 50)
        self.assertEqual(stats["max"], 250)

    # ── recommend_max_bid ─────────────────────────────────────────────────────

    def test_recommend_max_bid_no_history(self):
        self.storage.get_tickets_for_event.return_value = []
        event = _make_event(min_price=50.0, max_price=200.0)
        bid = self.analyzer.recommend_max_bid(event)
        self.assertLessEqual(bid, 300.0)

    def test_recommend_max_bid_with_history(self):
        tickets = [_make_ticket(100.0)] * 3
        self.storage.get_tickets_for_event.return_value = tickets
        event = _make_event()
        bid = self.analyzer.recommend_max_bid(event)
        self.assertAlmostEqual(bid, 120.0)  # 100 * 1.2

    # ── detect_price_spike ────────────────────────────────────────────────────

    def test_detect_spike_with_anomaly(self):
        # Precios normales alrededor de 100, el precio actual es 300 (spike)
        tickets = [_make_ticket(float(p)) for p in [95, 100, 105, 98, 102, 101, 99, 100, 97, 103]]
        self.storage.get_tickets_for_event.return_value = tickets
        event = _make_event()
        self.assertTrue(self.analyzer.detect_price_spike(event, 300.0))

    def test_no_spike_for_normal_price(self):
        tickets = [_make_ticket(float(p)) for p in [95, 100, 105, 98, 102, 101, 99, 100, 97, 103]]
        self.storage.get_tickets_for_event.return_value = tickets
        event = _make_event()
        self.assertFalse(self.analyzer.detect_price_spike(event, 105.0))


if __name__ == "__main__":
    unittest.main()
