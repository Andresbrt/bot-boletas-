"""Analiza precios históricos y determina si un precio es aceptable."""

import logging
import statistics
from datetime import datetime, timedelta
from typing import Optional

from src.models.event import Event
from src.models.ticket import Ticket
from src.utils.data_storage import DataStorage

logger = logging.getLogger(__name__)


class PriceAnalyzer:
    """
    Evalúa precios de tickets comparando con históricos y umbrales configurados.
    """

    def __init__(self, storage: DataStorage, max_price: float) -> None:
        self._storage = storage
        self._max_price = max_price

    # ── Evaluación principal ──────────────────────────────────────────────────

    def is_price_acceptable(self, event: Event, price: float) -> bool:
        """Devuelve True si el precio está dentro de los límites aceptables."""
        if price > self._max_price:
            logger.info(
                "Precio %.2f supera el máximo configurado %.2f", price, self._max_price
            )
            return False

        avg = self.get_average_price(event.event_id)
        if avg and price > avg * 1.5:
            logger.info(
                "Precio %.2f supera 1.5x la media histórica %.2f", price, avg
            )
            return False

        return True

    # ── Estadísticas ──────────────────────────────────────────────────────────

    def get_average_price(self, event_id: str) -> Optional[float]:
        """Calcula el precio medio de tickets comprados previamente para el evento."""
        tickets = self._storage.get_tickets_for_event(event_id)
        prices = [t.price for t in tickets if t.is_purchased]
        if not prices:
            return None
        return round(statistics.mean(prices), 2)

    def get_price_stats(self, event_id: str) -> dict:
        """Devuelve estadísticas descriptivas del precio para el evento."""
        tickets = self._storage.get_tickets_for_event(event_id)
        prices = [t.price for t in tickets if t.is_purchased]

        if not prices:
            return {"count": 0, "mean": None, "median": None, "min": None, "max": None, "stdev": None}

        return {
            "count": len(prices),
            "mean": round(statistics.mean(prices), 2),
            "median": round(statistics.median(prices), 2),
            "min": min(prices),
            "max": max(prices),
            "stdev": round(statistics.stdev(prices), 2) if len(prices) > 1 else 0.0,
        }

    def get_price_trend(self, event_id: str, days: int = 30) -> list[dict]:
        """
        Devuelve la evolución diaria del precio promedio en los últimos `days` días.
        """
        tickets = self._storage.get_tickets_for_event(event_id)
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent = [
            t for t in tickets
            if t.is_purchased and t.purchased_at and t.purchased_at >= cutoff
        ]

        daily: dict[str, list[float]] = {}
        for ticket in recent:
            day = ticket.purchased_at.strftime("%Y-%m-%d")  # type: ignore[union-attr]
            daily.setdefault(day, []).append(ticket.price)

        return [
            {"date": day, "avg_price": round(statistics.mean(prices), 2)}
            for day, prices in sorted(daily.items())
        ]

    # ── Recomendaciones ───────────────────────────────────────────────────────

    def recommend_max_bid(self, event: Event) -> float:
        """
        Sugiere un precio máximo razonable basado en el historial y el límite global.
        """
        avg = self.get_average_price(event.event_id)
        if avg is None:
            return min(event.max_price, self._max_price)
        suggested = min(avg * 1.2, self._max_price)
        return round(suggested, 2)

    def detect_price_spike(self, event: Event, current_price: float) -> bool:
        """
        Detecta si el precio actual es una anomalía respecto al histórico.
        Un spike se define como > 2 desviaciones estándar sobre la media.
        """
        stats = self.get_price_stats(event.event_id)
        if stats["count"] < 5 or stats["stdev"] == 0:
            return False
        z_score = (current_price - stats["mean"]) / stats["stdev"]
        return z_score > 2.0
