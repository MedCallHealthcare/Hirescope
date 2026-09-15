# backend/browser/manager.py

from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright, BrowserContext, Page


class BrowserManager:
    """
    Owns Playwright lifecycle.
    One browser context per scraper run.
    """

    def __init__(
        self,
        *,
        headless: bool = True,
        profile_dir: Optional[Path] = None,
        proxy: Optional[dict] = None,
    ):
        self.headless = headless
        self.profile_dir = profile_dir
        self.proxy = proxy

        self._playwright = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

        self._launch()

    # -------------------------
    # Public properties
    # -------------------------
    @property
    def page(self) -> Page:
        if not self._page:
            raise RuntimeError("Browser page not initialized")
        return self._page

    # -------------------------
    # Lifecycle
    # -------------------------
    def _launch(self) -> None:
        self._playwright = sync_playwright().start()

        chromium = self._playwright.chromium

        launch_args = {
            "headless": self.headless,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        }

        if self.proxy:
            launch_args["proxy"] = self.proxy

        # Use persistent context if profile_dir is provided
        if self.profile_dir:
            self._context = chromium.launch_persistent_context(
                user_data_dir=str(self.profile_dir),
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
                **launch_args,
            )
        else:
            browser = chromium.launch(**launch_args)
            self._context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
            )

        self._page = self._context.new_page()

        # Stealth: hide webdriver flag
        self._page.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            """
        )

    def close(self) -> None:
        """
        Safe to call multiple times.
        """
        try:
            if self._context:
                self._context.close()
        except Exception:
            pass

        try:
            if self._playwright:
                self._playwright.stop()
        except Exception:
            pass

        self._context = None
        self._page = None
        self._playwright = None
