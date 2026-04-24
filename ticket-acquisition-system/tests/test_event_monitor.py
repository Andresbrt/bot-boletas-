"""Tests para EventMonitor."""

import time
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from src.config.constants import EVENT_STATUS_AVAILABLE, EVENT_STATUS_SOLD_OUT
from src.core.event_monitor import EventMonitor
from src.models.event import Event


def _make_event(**kwargs) -> Event:
    defaults = dict(
        event_id="evt-001",
        name="Concierto Test",
        venue="Estadio Test",
        city="Madrid",
        date=datetime(2026, 12, 31, 20, 0),
        url="https://example.com/event/1",
        status=EVENT_STATUS_SOLD_OUT,
        min_price=50.0,
        max_price=150.0,
        available_tickets=0,
        total_capacity=1000,
    )
    defaults.update(kwargs)
    return Event(**defaults)


class TestEventMonitor(unittest.TestCase):

    def setUp(self):
        self.storage = MagicMock()
        self.notifier = MagicMock()
        self.monitor = EventMonitor(self.storage, self.notifier, interval=1)

    # ── watch / unwatch ───────────────────────────────────────────────────────

    def test_watch_adds_event(self):
        event = _make_event()
        self.monitor.watch(event)
        self.assertIn("evt-001", self.monitor._watched_events)
        self.storage.save_event.assert_called_once_with(event)

    def test_unwatch_removes_event(self):
        event = _make_event()
        self.monitor.watch(event)
        self.monitor.unwatch("evt-001")
        self.assertNotIn("evt-001", self.monitor._watched_events)

    def test_unwatch_nonexistent_does_not_raise(self):
        self.monitor.unwatch("nonexistent-id")  # no debe lanzar

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def test_callback_fired_when_becomes_available(self):
        callback = MagicMock()
        self.monitor.add_callback(callback)

        old = _make_event(status=EVENT_STATUS_SOLD_OUT)
        new = _make_event(status=EVENT_STATUS_AVAILABLE, available_tickets=10)

        self.monitor._process_update(old, new)

        callback.assert_called_once_with(new)
        self.notifier.send_availability_alert.assert_called_once_with(new)

    def test_callback_not_fired_when_still_sold_out(self):
        callback = MagicMock()
        self.monitor.add_callback(callback)

        old = _make_event(status=EVENT_STATUS_SOLD_OUT)
        new = _make_event(status=EVENT_STATUS_SOLD_OUT)

        self.monitor._process_update(old, new)

        callback.assert_not_called()
        self.notifier.send_availability_alert.assert_not_called()

    def test_callback_not_fired_when_already_available(self):
        callback = MagicMock()
        self.monitor.add_callback(callback)

        old = _make_event(status=EVENT_STATUS_AVAILABLE, available_tickets=5)
        new = _make_event(status=EVENT_STATUS_AVAILABLE, available_tickets=3)

        self.monitor._process_update(old, new)

        callback.assert_not_called()

    # ── create_event ──────────────────────────────────────────────────────────

    def test_create_event_generates_unique_ids(self):
        date = datetime(2026, 12, 31, 20, 0)
        e1 = EventMonitor.create_event("A", "V", "C", date, "https://a.com")
        e2 = EventMonitor.create_event("B", "V", "C", date, "https://b.com")
        self.assertNotEqual(e1.event_id, e2.event_id)

    # ── _parse_event_page ─────────────────────────────────────────────────────

    def test_parse_sold_out_page(self):
        event = _make_event()
        html = "<html><body><p>Sorry, this event is SOLD OUT</p></body></html>"
        result = self.monitor._parse_event_page(event, html)
        self.assertEqual(result.status, EVENT_STATUS_SOLD_OUT)

    def test_parse_available_page(self):
        event = _make_event()
        html = "<html><body><p>Tickets available now!</p></body></html>"
        result = self.monitor._parse_event_page(event, html)
        self.assertEqual(result.status, EVENT_STATUS_AVAILABLE)

    # ── stop ──────────────────────────────────────────────────────────────────

    def test_stop_sets_running_false(self):
        self.monitor._running = True
        self.monitor.stop()
        self.assertFalse(self.monitor._running)


if __name__ == "__main__":
    unittest.main()
