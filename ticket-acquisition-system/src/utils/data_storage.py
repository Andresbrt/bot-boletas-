"""Persistencia de eventos, tickets y cuentas en archivos JSON."""

import json
import logging
from pathlib import Path
from typing import Any, Optional

from src.config.settings import EVENTS_DIR, TICKETS_DIR, ANALYTICS_DIR
from src.models.event import Event
from src.models.ticket import Ticket
from src.models.user_account import UserAccount

logger = logging.getLogger(__name__)


class DataStorage:
    """
    Almacena y recupera entidades usando archivos JSON individuales por ID.
    Cada tipo de entidad tiene su propio directorio.
    """

    def __init__(
        self,
        events_dir: Path = EVENTS_DIR,
        tickets_dir: Path = TICKETS_DIR,
        analytics_dir: Path = ANALYTICS_DIR,
        accounts_dir: Optional[Path] = None,
    ) -> None:
        self._events_dir = events_dir
        self._tickets_dir = tickets_dir
        self._analytics_dir = analytics_dir
        self._accounts_dir = accounts_dir or events_dir.parent / "accounts"
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        for d in (
            self._events_dir,
            self._tickets_dir,
            self._analytics_dir,
            self._accounts_dir,
        ):
            d.mkdir(parents=True, exist_ok=True)

    # ── Helpers genéricos ─────────────────────────────────────────────────────

    @staticmethod
    def _write(path: Path, data: dict) -> None:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _read(path: Path) -> Optional[dict]:
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    # ── Eventos ───────────────────────────────────────────────────────────────

    def save_event(self, event: Event) -> None:
        path = self._events_dir / f"{event.event_id}.json"
        self._write(path, event.to_dict())
        logger.debug("Evento guardado: %s", event.event_id)

    def get_event(self, event_id: str) -> Optional[Event]:
        data = self._read(self._events_dir / f"{event_id}.json")
        return Event.from_dict(data) if data else None

    def get_all_events(self) -> list[Event]:
        return [
            Event.from_dict(json.loads(p.read_text(encoding="utf-8")))
            for p in sorted(self._events_dir.glob("*.json"))
        ]

    def delete_event(self, event_id: str) -> bool:
        path = self._events_dir / f"{event_id}.json"
        if path.exists():
            path.unlink()
            return True
        return False

    # ── Tickets ───────────────────────────────────────────────────────────────

    def save_ticket(self, ticket: Ticket) -> None:
        path = self._tickets_dir / f"{ticket.ticket_id}.json"
        self._write(path, ticket.to_dict())
        logger.debug("Ticket guardado: %s", ticket.ticket_id)

    def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        data = self._read(self._tickets_dir / f"{ticket_id}.json")
        return Ticket.from_dict(data) if data else None

    def get_all_tickets(self) -> list[Ticket]:
        return [
            Ticket.from_dict(json.loads(p.read_text(encoding="utf-8")))
            for p in sorted(self._tickets_dir.glob("*.json"))
        ]

    def get_tickets_for_event(self, event_id: str) -> list[Ticket]:
        return [t for t in self.get_all_tickets() if t.event_id == event_id]

    # ── Cuentas ───────────────────────────────────────────────────────────────

    def save_account(self, account: UserAccount) -> None:
        path = self._accounts_dir / f"{account.account_id}.json"
        self._write(path, account.to_dict())
        logger.debug("Cuenta guardada: %s", account.account_id)

    def get_account(self, account_id: str) -> Optional[UserAccount]:
        data = self._read(self._accounts_dir / f"{account_id}.json")
        return UserAccount.from_dict(data) if data else None

    def get_all_accounts(self) -> list[UserAccount]:
        return [
            UserAccount.from_dict(json.loads(p.read_text(encoding="utf-8")))
            for p in sorted(self._accounts_dir.glob("*.json"))
        ]

    def delete_account(self, account_id: str) -> bool:
        path = self._accounts_dir / f"{account_id}.json"
        if path.exists():
            path.unlink()
            return True
        return False

    # ── Analíticas ────────────────────────────────────────────────────────────

    def save_analytics(self, name: str, data: Any) -> None:
        path = self._analytics_dir / f"{name}.json"
        self._write(path, data if isinstance(data, dict) else {"data": data})
        logger.debug("Analítica guardada: %s", name)

    def get_analytics(self, name: str) -> Optional[Any]:
        data = self._read(self._analytics_dir / f"{name}.json")
        return data.get("data", data) if data else None
