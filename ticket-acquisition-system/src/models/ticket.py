from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from src.config.constants import TICKET_STATUS_RESERVED, DATETIME_FORMAT


@dataclass
class Ticket:
    """Representa un ticket adquirido o en proceso de adquisición."""

    ticket_id: str
    event_id: str
    category: str
    price: float
    currency: str = "USD"
    status: str = TICKET_STATUS_RESERVED
    seat: Optional[str] = None
    section: Optional[str] = None
    row: Optional[str] = None
    barcode: Optional[str] = None
    purchase_url: Optional[str] = None
    account_id: Optional[str] = None
    purchased_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None

    # ── Propiedades calculadas ────────────────────────────────────────────────

    @property
    def is_purchased(self) -> bool:
        return self.status == "purchased"

    @property
    def seat_label(self) -> str:
        parts = [p for p in [self.section, self.row, self.seat] if p]
        return " - ".join(parts) if parts else "Sin asiento asignado"

    # ── Serialización ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "ticket_id": self.ticket_id,
            "event_id": self.event_id,
            "category": self.category,
            "price": self.price,
            "currency": self.currency,
            "status": self.status,
            "seat": self.seat,
            "section": self.section,
            "row": self.row,
            "barcode": self.barcode,
            "purchase_url": self.purchase_url,
            "account_id": self.account_id,
            "purchased_at": (
                self.purchased_at.strftime(DATETIME_FORMAT)
                if self.purchased_at
                else None
            ),
            "created_at": self.created_at.strftime(DATETIME_FORMAT),
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Ticket":
        data = data.copy()
        if data.get("purchased_at"):
            data["purchased_at"] = datetime.strptime(data["purchased_at"], DATETIME_FORMAT)
        data["created_at"] = datetime.strptime(data["created_at"], DATETIME_FORMAT)
        return cls(**data)

    def __repr__(self) -> str:
        return (
            f"<Ticket id={self.ticket_id!r} event={self.event_id!r} "
            f"price={self.price} status={self.status!r}>"
        )
