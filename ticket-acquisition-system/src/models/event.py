from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from src.config.constants import EVENT_STATUS_PENDING, DATETIME_FORMAT


@dataclass
class Event:
    """Representa un evento con disponibilidad de tickets."""

    event_id: str
    name: str
    venue: str
    city: str
    date: datetime
    url: str
    status: str = EVENT_STATUS_PENDING
    min_price: float = 0.0
    max_price: float = 0.0
    available_tickets: int = 0
    total_capacity: int = 0
    categories: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

    # ── Propiedades calculadas ────────────────────────────────────────────────

    @property
    def is_available(self) -> bool:
        return self.status == "available" and self.available_tickets > 0

    @property
    def occupancy_rate(self) -> float:
        if self.total_capacity == 0:
            return 0.0
        sold = self.total_capacity - self.available_tickets
        return round(sold / self.total_capacity * 100, 2)

    # ── Serialización ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "name": self.name,
            "venue": self.venue,
            "city": self.city,
            "date": self.date.strftime(DATETIME_FORMAT),
            "url": self.url,
            "status": self.status,
            "min_price": self.min_price,
            "max_price": self.max_price,
            "available_tickets": self.available_tickets,
            "total_capacity": self.total_capacity,
            "categories": self.categories,
            "created_at": self.created_at.strftime(DATETIME_FORMAT),
            "updated_at": self.updated_at.strftime(DATETIME_FORMAT),
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Event":
        data = data.copy()
        data["date"] = datetime.strptime(data["date"], DATETIME_FORMAT)
        data["created_at"] = datetime.strptime(data["created_at"], DATETIME_FORMAT)
        data["updated_at"] = datetime.strptime(data["updated_at"], DATETIME_FORMAT)
        return cls(**data)

    def __repr__(self) -> str:
        return (
            f"<Event id={self.event_id!r} name={self.name!r} "
            f"status={self.status!r} available={self.available_tickets}>"
        )
