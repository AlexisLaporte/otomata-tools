"""
Browser automation client using Patchright (undetectable Playwright).

Supports persistent sessions via profile directories.
"""

import asyncio
from pathlib import Path
from typing import Optional
from patchright.async_api import async_playwright, BrowserContext, Page


class BrowserClient:
    """Async browser client with session persistence."""

    def __init__(
        self,
        profile_path: Optional[str] = None,
        headless: bool = True,
        viewport: tuple[int, int] = (1400, 900),
    ):
        """
        Initialize browser client.

        Args:
            profile_path: Path to browser profile directory for session persistence.
                          If None, uses ephemeral session.
            headless: Run browser in headless mode.
            viewport: Browser viewport size (width, height).
        """
        self.profile_path = Path(profile_path).expanduser() if profile_path else None
        self.headless = headless
        self.viewport = {"width": viewport[0], "height": viewport[1]}
        self._playwright = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def start(self) -> "BrowserClient":
        """Start browser and return self."""
        self._playwright = await async_playwright().start()

        if self.profile_path:
            if not self.profile_path.exists():
                raise FileNotFoundError(f"Profile not found: {self.profile_path}")
            self._context = await self._playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.profile_path),
                headless=self.headless,
                channel="chrome",
                viewport=self.viewport,
            )
            self._page = self._context.pages[0] if self._context.pages else await self._context.new_page()
        else:
            browser = await self._playwright.chromium.launch(
                headless=self.headless,
                channel="chrome",
            )
            self._context = await browser.new_context(viewport=self.viewport)
            self._page = await self._context.new_page()

        return self

    async def close(self):
        """Close browser and cleanup."""
        if self._context:
            await self._context.close()
        if self._playwright:
            await self._playwright.stop()

    @property
    def page(self) -> Page:
        """Get current page."""
        if not self._page:
            raise RuntimeError("Browser not started. Call start() first.")
        return self._page

    async def goto(self, url: str, wait_until: str = "domcontentloaded", timeout: int = 30000) -> None:
        """Navigate to URL."""
        await self.page.goto(url, wait_until=wait_until, timeout=timeout)

    async def get_text(self) -> str:
        """Get page text content."""
        return await self.page.evaluate("() => document.body.innerText")

    async def get_html(self) -> str:
        """Get page HTML."""
        return await self.page.content()

    async def screenshot(self, path: str, full_page: bool = True) -> str:
        """Take screenshot and return path."""
        await self.page.screenshot(path=path, full_page=full_page)
        return path

    async def scroll_to_bottom(self, times: int = 3, delay: float = 2.0) -> None:
        """Scroll to bottom of page multiple times to load dynamic content."""
        for _ in range(times):
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(delay)

    async def scroll_element(self, selector: str, times: int = 3, delay: float = 2.0) -> None:
        """Scroll inside a specific element (for infinite scroll containers)."""
        for _ in range(times):
            await self.page.evaluate(f"""
                const el = document.querySelector('{selector}');
                if (el) el.scrollTop = el.scrollHeight;
            """)
            await asyncio.sleep(delay)

    async def wait_for_content(self, min_length: int = 500, max_attempts: int = 10, delay: float = 2.0) -> bool:
        """Wait for page content to load (not showing 'Loading...')."""
        for _ in range(max_attempts):
            text = await self.get_text()
            if "Loading" not in text and len(text) > min_length:
                return True
            await asyncio.sleep(delay)
        return False

    async def click(self, selector: str) -> None:
        """Click element by selector."""
        await self.page.click(selector)

    async def fill(self, selector: str, value: str) -> None:
        """Fill input field."""
        await self.page.fill(selector, value)

    async def query_selector_all(self, selector: str):
        """Query all elements matching selector."""
        return await self.page.query_selector_all(selector)
