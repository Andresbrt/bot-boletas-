from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from src.config.constants import DATETIME_FORMAT


@dataclass
class UserAccount:
    """Credenciales y perfil de una cuenta de usuario en una plataforma de tickets."""

    account_id: str
    platform: str
    email: str
    username: str
    is_active: bool = True
    is_verified: bool = False
    tickets_purchased: int = 0
    total_spent: float = 0.0
    last_used: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

    # Las credenciales sensibles se almacenan fuera del modelo
    # y se inyectan en tiempo de ejecución desde un gestor de secretos.
    _password_hash: str = field(default="", repr=False)

    # ── Propiedades calculadas ────────────────────────────────────────────────

    @property
    def can_purchase(self) -> bool:
        return self.is_active and self.is_verified

    @property
    def average_ticket_price(self) -> float:
        if self.tickets_purchased == 0:
            return 0.0
        return round(self.total_spent / self.tickets_purchased, 2)

    # ── Métodos de estado ─────────────────────────────────────────────────────

    def record_purchase(self, amount: float) -> None:
        self.tickets_purchased += 1
        self.total_spent += amount
        self.last_used = datetime.utcnow()

    def deactivate(self) -> None:
        self.is_active = False

    # ── Serialización ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Serializa la cuenta SIN datos sensibles."""
        return {
            "account_id": self.account_id,
            "platform": self.platform,
            "email": self.email,
            "username": self.username,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "tickets_purchased": self.tickets_purchased,
            "total_spent": self.total_spent,
            "last_used": (
                self.last_used.strftime(DATETIME_FORMAT) if self.last_used else None
            ),
            "created_at": self.created_at.strftime(DATETIME_FORMAT),
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserAccount":
        data = data.copy()
        if data.get("last_used"):
            data["last_used"] = datetime.strptime(data["last_used"], DATETIME_FORMAT)
        data["created_at"] = datetime.strptime(data["created_at"], DATETIME_FORMAT)
        return cls(**data)

    def __repr__(self) -> str:
        return (
            f"<UserAccount id={self.account_id!r} platform={self.platform!r} "
            f"email={self.email!r} active={self.is_active}>"
        )
