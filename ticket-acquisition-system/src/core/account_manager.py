"""Gestiona el ciclo de vida de las cuentas de usuario en las plataformas."""

import logging
from typing import Optional

from src.models.user_account import UserAccount
from src.utils.data_storage import DataStorage

logger = logging.getLogger(__name__)


class AccountManager:
    """
    Mantiene un pool de cuentas de usuario, selecciona la más adecuada
    para cada compra y registra el uso.
    """

    def __init__(self, storage: DataStorage) -> None:
        self._storage = storage
        self._accounts: dict[str, UserAccount] = {}
        self._load_accounts()

    # ── Carga y persistencia ──────────────────────────────────────────────────

    def _load_accounts(self) -> None:
        for account in self._storage.get_all_accounts():
            self._accounts[account.account_id] = account
        logger.info("Cuentas cargadas: %d", len(self._accounts))

    def save(self, account: UserAccount) -> None:
        self._accounts[account.account_id] = account
        self._storage.save_account(account)

    # ── Consultas ─────────────────────────────────────────────────────────────

    def get(self, account_id: str) -> Optional[UserAccount]:
        return self._accounts.get(account_id)

    def list_active(self) -> list[UserAccount]:
        return [a for a in self._accounts.values() if a.is_active]

    def list_available(self, max_tickets_per_event: int) -> list[UserAccount]:
        """Devuelve cuentas activas que aún pueden comprar más tickets."""
        return [
            a for a in self.list_active()
            if a.can_purchase and a.tickets_purchased < max_tickets_per_event
        ]

    # ── Selección de cuenta ───────────────────────────────────────────────────

    def select_best_account(self, max_tickets_per_event: int) -> Optional[UserAccount]:
        """
        Elige la cuenta con menos tickets comprados entre las disponibles.
        Estrategia: balanceo de carga uniforme entre cuentas.
        """
        candidates = self.list_available(max_tickets_per_event)
        if not candidates:
            logger.warning("No hay cuentas disponibles para compra.")
            return None
        return min(candidates, key=lambda a: a.tickets_purchased)

    # ── Gestión de cuentas ────────────────────────────────────────────────────

    def add_account(self, account: UserAccount) -> None:
        if account.account_id in self._accounts:
            raise ValueError(f"La cuenta {account.account_id!r} ya existe.")
        self.save(account)
        logger.info("Cuenta añadida: %s", account.account_id)

    def deactivate(self, account_id: str) -> bool:
        account = self.get(account_id)
        if not account:
            return False
        account.deactivate()
        self.save(account)
        logger.info("Cuenta desactivada: %s", account_id)
        return True

    def remove_account(self, account_id: str) -> bool:
        if account_id not in self._accounts:
            return False
        del self._accounts[account_id]
        self._storage.delete_account(account_id)
        logger.info("Cuenta eliminada: %s", account_id)
        return True

    # ── Estadísticas ──────────────────────────────────────────────────────────

    def summary(self) -> dict:
        accounts = list(self._accounts.values())
        return {
            "total": len(accounts),
            "active": sum(1 for a in accounts if a.is_active),
            "verified": sum(1 for a in accounts if a.is_verified),
            "total_purchased": sum(a.tickets_purchased for a in accounts),
            "total_spent": round(sum(a.total_spent for a in accounts), 2),
        }
