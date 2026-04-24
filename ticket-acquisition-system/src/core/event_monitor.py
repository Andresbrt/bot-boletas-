"""Monitorea plataformas de venta de tickets en busca de disponibilidad."""

import logging
import time
import uuid
from datetime import datetime
from typing import Callable, Optional

import requests
from bs4 import BeautifulSoup

from src.config.settings import MONITOR_INTERVAL, BROWSER_TIMEOUT, USER_AGENT
from src.config.constants import (
    EVENT_STATUS_AVAILABLE,
    EVENT_STATUS_SOLD_OUT,
    MAX_RETRY_ATTEMPTS,
    RETRY_DELAY_SECONDS,
)
from src.models.event import Event
from src.utils.data_storage import DataStorage
from src.utils.notification_system import NotificationSystem

logger = logging.getLogger(__name__)


class EventMonitor:
    """
    Monitorea eventos en plataformas de tickets y dispara callbacks
    cuando se detecta disponibilidad.
    """

    def __init__(
        self,
        storage: DataStorage,
        notifier: NotificationSystem,
        interval: int = MONITOR_INTERVAL,
    ) -> None:
        self._storage = storage
        self._notifier = notifier
        self._interval = interval
        self._watched_events: dict[str, Event] = {}
        self._callbacks: list[Callable[[Event], None]] = []
        self._running = False
        self._session = self._build_session()

    # ── Configuración ─────────────────────────────────────────────────────────

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT})
        session.timeout = BROWSER_TIMEOUT
        return session

    def add_callback(self, fn: Callable[[Event], None]) -> None:
        """Registra un callback que se invoca cuando un evento pasa a disponible."""
        self._callbacks.append(fn)

    def watch(self, event: Event) -> None:
        """Agrega un evento a la lista de monitoreo."""
        self._watched_events[event.event_id] = event
        self._storage.save_event(event)
        logger.info("Monitoreando evento: %s", event.name)

    def unwatch(self, event_id: str) -> None:
        """Elimina un evento de la lista de monitoreo."""
        self._watched_events.pop(event_id, None)
        logger.info("Evento eliminado del monitoreo: %s", event_id)

    # ── Ciclo principal ───────────────────────────────────────────────────────

    def start(self) -> None:
        """Inicia el bucle de monitoreo (bloqueante)."""
        self._running = True
        logger.info("Monitor iniciado. Intervalo: %ds", self._interval)
        try:
            while self._running:
                self._check_all()
                time.sleep(self._interval)
        except KeyboardInterrupt:
            logger.info("Monitor detenido por el usuario.")
        finally:
            self._running = False

    def stop(self) -> None:
        self._running = False

    def _check_all(self) -> None:
        for event in list(self._watched_events.values()):
            try:
                updated = self._fetch_status(event)
                self._process_update(event, updated)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Error al verificar evento %s: %s", event.event_id, exc)

    # ── Lógica de verificación ────────────────────────────────────────────────

    def _fetch_status(self, event: Event) -> Event:
        """Obtiene el estado actual del evento desde su URL."""
        for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
            try:
                response = self._session.get(event.url)
                response.raise_for_status()
                return self._parse_event_page(event, response.text)
            except requests.RequestException as exc:
                logger.warning(
                    "Intento %d/%d fallido para %s: %s",
                    attempt, MAX_RETRY_ATTEMPTS, event.event_id, exc,
                )
                if attempt < MAX_RETRY_ATTEMPTS:
                    time.sleep(RETRY_DELAY_SECONDS)
        raise RuntimeError(f"No se pudo obtener el estado del evento {event.event_id}")

    def _parse_event_page(self, event: Event, html: str) -> Event:
        """
        Parsea el HTML de la página del evento.
        Personaliza este método para cada plataforma.
        """
        soup = BeautifulSoup(html, "lxml")

        # Ejemplo genérico: busca texto que indique agotado
        page_text = soup.get_text(separator=" ").lower()
        sold_out_keywords = ["sold out", "agotado", "no disponible", "not available"]
        is_sold_out = any(kw in page_text for kw in sold_out_keywords)

        updated = Event(
            event_id=event.event_id,
            name=event.name,
            venue=event.venue,
            city=event.city,
            date=event.date,
            url=event.url,
            status=EVENT_STATUS_SOLD_OUT if is_sold_out else EVENT_STATUS_AVAILABLE,
            min_price=event.min_price,
            max_price=event.max_price,
            available_tickets=0 if is_sold_out else event.available_tickets,
            total_capacity=event.total_capacity,
            categories=event.categories,
            created_at=event.created_at,
            updated_at=datetime.utcnow(),
        )
        return updated

    def _process_update(self, old: Event, new: Event) -> None:
        """Compara estados y dispara callbacks si el evento pasa a disponible."""
        self._watched_events[new.event_id] = new
        self._storage.save_event(new)

        became_available = (
            old.status != EVENT_STATUS_AVAILABLE
            and new.status == EVENT_STATUS_AVAILABLE
        )
        if became_available:
            logger.info("¡Tickets disponibles para: %s!", new.name)
            self._notifier.send_availability_alert(new)
            for cb in self._callbacks:
                try:
                    cb(new)
                except Exception as exc:  # noqa: BLE001
                    logger.error("Error en callback de disponibilidad: %s", exc)

    # ── Utilidades ────────────────────────────────────────────────────────────

    @staticmethod
    def create_event(
        name: str,
        venue: str,
        city: str,
        date: datetime,
        url: str,
        **kwargs,
    ) -> Event:
        """Factoría conveniente para crear un nuevo Event con ID único."""
        return Event(
            event_id=str(uuid.uuid4()),
            name=name,
            venue=venue,
            city=city,
            date=date,
            url=url,
            **kwargs,
        )
