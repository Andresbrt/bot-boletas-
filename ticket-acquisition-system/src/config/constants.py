"""Constantes globales del sistema."""

# ── Estados de eventos ───────────────────────────────────────────────────────
EVENT_STATUS_AVAILABLE = "available"
EVENT_STATUS_SOLD_OUT = "sold_out"
EVENT_STATUS_CANCELLED = "cancelled"
EVENT_STATUS_PENDING = "pending"

# ── Estados de tickets ───────────────────────────────────────────────────────
TICKET_STATUS_RESERVED = "reserved"
TICKET_STATUS_PURCHASED = "purchased"
TICKET_STATUS_FAILED = "failed"
TICKET_STATUS_REFUNDED = "refunded"

# ── Categorías de tickets ────────────────────────────────────────────────────
TICKET_CATEGORY_GENERAL = "general"
TICKET_CATEGORY_VIP = "vip"
TICKET_CATEGORY_PREMIUM = "premium"
TICKET_CATEGORY_FLOOR = "floor"

# ── Códigos de resultado de compra ───────────────────────────────────────────
PURCHASE_SUCCESS = "purchase_success"
PURCHASE_FAILED = "purchase_failed"
PURCHASE_TIMEOUT = "purchase_timeout"
PURCHASE_PRICE_EXCEEDED = "purchase_price_exceeded"
PURCHASE_SOLD_OUT = "purchase_sold_out"
PURCHASE_LIMIT_REACHED = "purchase_limit_reached"

# ── Tipos de notificación ────────────────────────────────────────────────────
NOTIFICATION_EMAIL = "email"
NOTIFICATION_SMS = "sms"
NOTIFICATION_PUSH = "push"

# ── Formatos de fecha ────────────────────────────────────────────────────────
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# ── Límites del sistema ───────────────────────────────────────────────────────
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 5
MAX_CONCURRENT_MONITORS = 10
SESSION_EXPIRY_MINUTES = 30
