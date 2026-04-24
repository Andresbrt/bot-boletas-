"""
Punto de entrada para comprar tickets de un evento específico.

Uso:
    python scripts/run_purchaser.py --event-id <id> --account-id <id> \
        --category general --quantity 2

Variables de entorno relevantes:
    MAX_TICKET_PRICE, MAX_TICKETS_PER_EVENT, HEADLESS_BROWSER, LOG_LEVEL
"""

import argparse
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
load_dotenv()

from src.config.settings import LOG_LEVEL, LOG_FILE, MAX_TICKET_PRICE, MAX_TICKETS_PER_EVENT
from src.core.account_manager import AccountManager
from src.core.ticket_purchaser import TicketPurchaser
from src.utils.browser_automation import BrowserAutomation
from src.utils.data_storage import DataStorage
from src.utils.notification_system import NotificationSystem


def configure_logging() -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
        ],
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Comprador automático de tickets")
    parser.add_argument("--event-id", required=True, help="ID del evento")
    parser.add_argument("--account-id", required=True, help="ID de la cuenta a usar")
    parser.add_argument("--category", default="general", help="Categoría de tickets")
    parser.add_argument("--quantity", type=int, default=1, help="Cantidad a comprar")
    return parser.parse_args()


def main() -> None:
    configure_logging()
    args = parse_args()
    logger = logging.getLogger(__name__)

    storage = DataStorage()
    notifier = NotificationSystem()
    account_manager = AccountManager(storage)

    event = storage.get_event(args.event_id)
    if not event:
        logger.error("Evento no encontrado: %s", args.event_id)
        sys.exit(1)

    account = account_manager.get(args.account_id)
    if not account:
        logger.error("Cuenta no encontrada: %s", args.account_id)
        sys.exit(1)

    logger.info(
        "Comprando %d ticket(s) para '%s' con cuenta '%s'...",
        args.quantity, event.name, account.email,
    )

    with BrowserAutomation() as browser:
        purchaser = TicketPurchaser(
            browser=browser,
            storage=storage,
            notifier=notifier,
            max_price=MAX_TICKET_PRICE,
            max_per_event=MAX_TICKETS_PER_EVENT,
        )
        tickets = purchaser.purchase(event, account, args.category, args.quantity)

    purchased = [t for t in tickets if t.is_purchased]
    failed = [t for t in tickets if not t.is_purchased]

    logger.info("Resultado: %d comprados, %d fallidos", len(purchased), len(failed))
    for t in purchased:
        logger.info("  ✓ Ticket %s | Asiento: %s", t.ticket_id, t.seat_label)
    for t in failed:
        logger.warning("  ✗ Ticket %s | Error: %s", t.ticket_id, t.error_message)

    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    main()
