"""
Script de configuración inicial del proyecto.
Crea los directorios necesarios, verifica dependencias y genera un .env de ejemplo.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def create_directories() -> None:
    dirs = [
        ROOT / "data" / "events",
        ROOT / "data" / "tickets",
        ROOT / "data" / "analytics",
        ROOT / "data" / "accounts",
        ROOT / "logs",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Directorios creados en: {ROOT / 'data'}")


def create_env_file() -> None:
    env_path = ROOT / ".env"
    if env_path.exists():
        print("[SKIP] .env ya existe. No se sobreescribirá.")
        return

    template = """\
# ── Monitor ────────────────────────────────────────────────
MONITOR_INTERVAL=30
PURCHASE_TIMEOUT=60

# ── Precios ────────────────────────────────────────────────
MAX_TICKET_PRICE=500.0
MAX_TICKETS_PER_EVENT=4

# ── Notificaciones SMTP ────────────────────────────────────
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_email@gmail.com
SMTP_PASSWORD=tu_contraseña_de_app
NOTIFICATION_EMAIL=destino@gmail.com

# ── Navegador ──────────────────────────────────────────────
HEADLESS_BROWSER=true
BROWSER_TIMEOUT=15

# ── Logging ────────────────────────────────────────────────
LOG_LEVEL=INFO
"""
    env_path.write_text(template, encoding="utf-8")
    print(f"[OK] Archivo .env creado en: {env_path}")


def check_python_version() -> None:
    major, minor = sys.version_info[:2]
    if (major, minor) < (3, 10):
        print(f"[ERROR] Se requiere Python 3.10+. Versión actual: {major}.{minor}")
        sys.exit(1)
    print(f"[OK] Python {major}.{minor}")


def install_playwright_browsers() -> None:
    import subprocess  # noqa: PLC0415
    print("[INFO] Instalando navegadores de Playwright...")
    result = subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print("[OK] Playwright Chromium instalado.")
    else:
        print("[WARN] No se pudo instalar Playwright:", result.stderr.strip())


def main() -> None:
    print("=== Configuración del sistema de adquisición de tickets ===\n")
    check_python_version()
    create_directories()
    create_env_file()
    install_playwright_browsers()
    print("\n[LISTO] Configuración completada. Edita el archivo .env antes de ejecutar.")


if __name__ == "__main__":
    main()
