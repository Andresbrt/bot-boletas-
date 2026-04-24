import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ── Rutas de datos ──────────────────────────────────────────────────────────
DATA_DIR = BASE_DIR / "data"
EVENTS_DIR = DATA_DIR / "events"
TICKETS_DIR = DATA_DIR / "tickets"
ANALYTICS_DIR = DATA_DIR / "analytics"

# ── Intervalos de monitoreo (segundos) ──────────────────────────────────────
MONITOR_INTERVAL = int(os.getenv("MONITOR_INTERVAL", 30))
PURCHASE_TIMEOUT = int(os.getenv("PURCHASE_TIMEOUT", 60))

# ── Límites de precios ───────────────────────────────────────────────────────
MAX_TICKET_PRICE = float(os.getenv("MAX_TICKET_PRICE", 500.0))
MAX_TICKETS_PER_EVENT = int(os.getenv("MAX_TICKETS_PER_EVENT", 4))

# ── Notificaciones ───────────────────────────────────────────────────────────
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
NOTIFICATION_EMAIL = os.getenv("NOTIFICATION_EMAIL", "")

# ── Navegador ────────────────────────────────────────────────────────────────
HEADLESS_BROWSER = os.getenv("HEADLESS_BROWSER", "true").lower() == "true"
BROWSER_TIMEOUT = int(os.getenv("BROWSER_TIMEOUT", 15))
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# ── Logging ──────────────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = BASE_DIR / "logs" / "app.log"
