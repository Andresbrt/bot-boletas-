"""Abstracción sobre Playwright para automatizar el navegador web."""

import logging
from typing import Any, Optional

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    sync_playwright,
    TimeoutError as PlaywrightTimeout,
)

from src.config.settings import HEADLESS_BROWSER, BROWSER_TIMEOUT, USER_AGENT
from src.models.user_account import UserAccount

logger = logging.getLogger(__name__)

_TIMEOUT_MS = BROWSER_TIMEOUT * 1000  # Playwright trabaja en milisegundos


class BrowserAutomation:
    """
    Encapsula las interacciones con el navegador mediante Playwright.
    Uso recomendado como context manager:

        with BrowserAutomation() as browser:
            browser.navigate("https://...")
    """

    def __init__(self, headless: bool = HEADLESS_BROWSER) -> None:
        self._headless = headless
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    # ── Context manager ───────────────────────────────────────────────────────

    def __enter__(self) -> "BrowserAutomation":
        self.launch()
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    # ── Ciclo de vida ─────────────────────────────────────────────────────────

    def launch(self) -> None:
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self._headless)
        self._context = self._browser.new_context(user_agent=USER_AGENT)
        self._page = self._context.new_page()
        self._page.set_default_timeout(_TIMEOUT_MS)
        logger.info("Navegador iniciado (headless=%s)", self._headless)

    def close(self) -> None:
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
        logger.info("Navegador cerrado.")

    # ── Navegación ────────────────────────────────────────────────────────────

    def navigate(self, url: str) -> None:
        self._page.goto(url, wait_until="domcontentloaded")  # type: ignore[union-attr]
        logger.debug("Navegando a: %s", url)

    def get_current_url(self) -> str:
        return self._page.url  # type: ignore[union-attr]

    def get_page_text(self) -> str:
        return self._page.inner_text("body")  # type: ignore[union-attr]

    def take_screenshot(self, path: str) -> None:
        self._page.screenshot(path=path)  # type: ignore[union-attr]
        logger.debug("Captura de pantalla guardada: %s", path)

    # ── Interacciones de checkout ─────────────────────────────────────────────

    def select_category(self, category: str) -> None:
        """Selecciona la categoría/tipo de ticket en la página del evento."""
        try:
            self._page.click(f"[data-category='{category}']")  # type: ignore[union-attr]
        except PlaywrightTimeout:
            # Fallback: busca por texto visible
            self._page.get_by_text(category, exact=False).first.click()  # type: ignore[union-attr]
        logger.debug("Categoría seleccionada: %s", category)

    def select_quantity(self, quantity: int) -> None:
        selector = "select[name='quantity'], input[name='quantity']"
        el = self._page.query_selector(selector)  # type: ignore[union-attr]
        if el:
            el.select_option(str(quantity))
        logger.debug("Cantidad seleccionada: %d", quantity)

    def proceed_to_checkout(self) -> None:
        checkout_selectors = [
            "button[data-action='checkout']",
            "button:text('Checkout')",
            "button:text('Comprar')",
            "a:text('Checkout')",
        ]
        for sel in checkout_selectors:
            try:
                self._page.click(sel)  # type: ignore[union-attr]
                logger.debug("Checkout iniciado con selector: %s", sel)
                return
            except PlaywrightTimeout:
                continue
        raise RuntimeError("No se encontró el botón de checkout.")

    def fill_account_credentials(self, account: UserAccount) -> None:
        """Completa el formulario de login / datos de la cuenta."""
        # Ejemplo genérico; adaptar por plataforma
        email_field = self._page.query_selector("input[type='email'], input[name='email']")  # type: ignore[union-attr]
        if email_field:
            email_field.fill(account.email)
        logger.debug("Credenciales completadas para: %s", account.email)

    def confirm_purchase(self, timeout: int) -> dict:
        """
        Hace clic en el botón de confirmación y espera la página de éxito.
        Devuelve un dict con los datos de confirmación extraídos.
        """
        confirm_selectors = [
            "button[data-action='confirm']",
            "button:text('Confirm')",
            "button:text('Confirmar')",
        ]
        for sel in confirm_selectors:
            try:
                self._page.click(sel, timeout=timeout * 1000)  # type: ignore[union-attr]
                break
            except PlaywrightTimeout:
                continue

        # Espera algún indicador de éxito
        self._page.wait_for_selector(  # type: ignore[union-attr]
            "[data-status='success'], .confirmation-code, .order-confirmation",
            timeout=timeout * 1000,
        )

        return self._extract_confirmation()

    def _extract_confirmation(self) -> dict:
        """Extrae datos de la página de confirmación. Personalizar por plataforma."""
        page = self._page  # type: ignore[union-attr]
        barcode = None
        seat = None
        section = None
        row = None

        barcode_el = page.query_selector("[data-barcode], .barcode, .ticket-code")
        if barcode_el:
            barcode = barcode_el.inner_text().strip()

        seat_el = page.query_selector("[data-seat], .seat-number")
        if seat_el:
            seat = seat_el.inner_text().strip()

        return {"barcode": barcode, "seat": seat, "section": section, "row": row}
