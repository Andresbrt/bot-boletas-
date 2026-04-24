"""
Punto de entrada para el monitor de eventos.

Uso:
    python scripts/run_monitor.py --url https://... --name "Nombre del evento" \
        --venue "Venue" --city "Ciudad" --date "2026-12-31 20:00:00"

Variables de entorno relevantes:
    MONITOR_INTERVAL, MAX_TICKET_PRICE, LOG_LEVEL
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Permite ejecutar desde la raíz del proyecto
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
load_dotenv()

from src.config.constants import DATETIME_FORMAT
from src.config.settings import LOG_LEVEL, LOG_FILE, MONITOR_INTERVAL
from src.core.event_monitor import EventMonitor
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
    parser = argparse.ArgumentParser(description="Monitor de disponibilidad de tickets")
    parser.add_argument("--url", required=True, help="URL del evento a monitorear")
    parser.add_argument("--name", required=True, help="Nombre del evento")
    parser.add_argument("--venue", required=True, help="Nombre del venue")
    parser.add_argument("--city", required=True, help="Ciudad del evento")
    parser.add_argument(
        "--date",
        required=True,
        help=f"Fecha del evento ({DATETIME_FORMAT})",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=MONITOR_INTERVAL,
        help=f"Intervalo de verificación en segundos (default: {MONITOR_INTERVAL})",
    )
    return parser.parse_args()


def main() -> None:
    configure_logging()
    args = parse_args()

    logger = logging.getLogger(__name__)
    logger.info("Iniciando monitor de eventos...")

    storage = DataStorage()
    notifier = NotificationSystem()
    monitor = EventMonitor(storage, notifier, interval=args.interval)

    try:
        event_date = datetime.strptime(args.date, DATETIME_FORMAT)
    except ValueError:
        logger.error("Formato de fecha inválido. Use: %s", DATETIME_FORMAT)
        sys.exit(1)

    event = EventMonitor.create_event(
        name=args.name,
        venue=args.venue,
        city=args.city,
        date=event_date,
        url=args.url,
    )
    monitor.watch(event)
    logger.info("Monitoreando: %s | URL: %s", event.name, event.url)

    monitor.start()


if __name__ == "__main__":
    main()
