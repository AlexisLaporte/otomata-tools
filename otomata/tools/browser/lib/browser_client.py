"""
Browser automation client using Patchright (undetectable Playwright).

Supports:
- Profile-based persistent sessions
- Cookie-based authentication
- Response interception
- Extensible for domain-specific clients
"""

import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Callable, Any


class BrowserClient:
    """
    Async browser client - base class for all browser automation.

    Can be used standalone or inherited by domain-specific clients.
    """

    def __init__(
        self,
        profile_path: Optional[str] = None,
        headless: bool = True,
        viewport: tuple[int, int] = (1920, 1080),
        user_agent: str = None,
        cookies: List[Dict] = None,
        locale: str = None,
        timezone_id: str = None,
        browser_args: List[str] = None,
    ):
        """
        Initialize browser client.

        Args:
            profile_path: Path to browser profile directory for persistent sessions.
                          If None, uses ephemeral session (can still inject cookies).
            headless: Run browser in headless mode.
            viewport: Browser viewport size (width, height).
            user_agent: Custom user agent string.
            cookies: List of cookies to inject after browser starts.
            locale: Browser locale (e.g., "fr-FR").
            timezone_id: Timezone (e.g., "Europe/Paris").
            browser_args: Additional Chromium args.
        """
        self.profile_path = Path(profile_path).expanduser() if profile_path else None
        self.headless = headless
        self.viewport = {"width": viewport[0], "height": viewport[1]}
        self.user_agent = user_agent
        self.cookies = cookies or []
        self.locale = locale
        self.timezone_id = timezone_id
        self.browser_args = browser_args or []

        # Browser instances (lazy init)
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

        # Response interception
        self._response_handlers: List[Callable] = []

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def start(self) -> "BrowserClient":
        """Start browser and return self."""
        try:
            from patchright.async_api import async_playwright
        except ImportError:
            raise ImportError(
                "Browser automation requires patchright. Install with: pip install otomata[browser]"
            )

        self._playwright = await async_playwright().start()

        # Default browser args for stealth
        default_args = [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
        ]
        launch_args = list(set(default_args + self.browser_args))

        if self.profile_path:
            # Persistent context with profile
            if not self.profile_path.exists():
                self.profile_path.mkdir(parents=True, exist_ok=True)

            context_options = {
                "user_data_dir": str(self.profile_path),
                "headless": self.headless,
                "channel": "chrome",
                "viewport": self.viewport,
                "args": launch_args,
            }
            if self.user_agent:
                context_options["user_agent"] = self.user_agent
            if self.locale:
                context_options["locale"] = self.locale
            if self.timezone_id:
                context_options["timezone_id"] = self.timezone_id

            self._context = await self._playwright.chromium.launch_persistent_context(
                **context_options
            )
            self._page = self._context.pages[0] if self._context.pages else await self._context.new_page()
        else:
            # Ephemeral context
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless,
                channel="chrome",
                args=launch_args,
            )

            context_options = {"viewport": self.viewport}
            if self.user_agent:
                context_options["user_agent"] = self.user_agent
            if self.locale:
                context_options["locale"] = self.locale
            if self.timezone_id:
                context_options["timezone_id"] = self.timezone_id

            self._context = await self._browser.new_context(**context_options)
            self._page = await self._context.new_page()

        # Inject cookies if provided
        if self.cookies:
            await self.add_cookies(self.cookies)

        # Setup response handlers
        if self._response_handlers:
            self._page.on("response", self._on_response)

        return self

    async def close(self):
        """Close browser and cleanup."""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    @property
    def page(self):
        """Get current page."""
        if not self._page:
            raise RuntimeError("Browser not started. Use 'async with' or call start() first.")
        return self._page

    @property
    def context(self):
        """Get browser context."""
        if not self._context:
            raise RuntimeError("Browser not started. Use 'async with' or call start() first.")
        return self._context

    # === Cookie Management ===

    async def add_cookies(self, cookies: List[Dict]):
        """
        Add cookies to browser context.

        Args:
            cookies: List of cookie dicts with at least 'name', 'value', 'domain'
        """
        if not self._context:
            raise RuntimeError("Browser not started")

        # Normalize cookies
        formatted = []
        for cookie in cookies:
            c = {
                "name": cookie["name"],
                "value": cookie["value"],
                "domain": cookie.get("domain", ""),
                "path": cookie.get("path", "/"),
            }
            if "httpOnly" in cookie:
                c["httpOnly"] = cookie["httpOnly"]
            if "secure" in cookie:
                c["secure"] = cookie["secure"]
            if "sameSite" in cookie:
                c["sameSite"] = cookie["sameSite"]
            formatted.append(c)

        await self._context.add_cookies(formatted)

    async def get_cookies(self) -> List[Dict]:
        """Get all cookies from context."""
        if not self._context:
            return []
        return await self._context.cookies()

    # === Response Interception ===

    def on_response(self, handler: Callable):
        """
        Register response handler for intercepting network responses.

        Handler signature: async def handler(response) -> None
        """
        self._response_handlers.append(handler)
        if self._page:
            self._page.on("response", self._on_response)

    async def _on_response(self, response):
        """Internal response handler dispatcher."""
        for handler in self._response_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(response)
                else:
                    handler(response)
            except Exception:
                pass

    # === Navigation ===

    async def goto(self, url: str, wait_until: str = "domcontentloaded", timeout: int = 30000) -> bool:
        """
        Navigate to URL.

        Returns:
            True if navigation succeeded (status 200), False otherwise
        """
        try:
            response = await self.page.goto(url, wait_until=wait_until, timeout=timeout)
            return response and response.status == 200
        except Exception:
            return False

    async def wait(self, seconds: float):
        """Wait for specified seconds."""
        await asyncio.sleep(seconds)

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

    # === Scrolling ===

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

    async def scroll_by(self, y: int):
        """Scroll page by Y pixels."""
        await self.page.evaluate(f"window.scrollBy(0, {y})")

    # === Waiting ===

    async def wait_for_content(self, min_length: int = 500, max_attempts: int = 10, delay: float = 2.0) -> bool:
        """Wait for page content to load (not showing 'Loading...')."""
        for _ in range(max_attempts):
            text = await self.get_text()
            if "Loading" not in text and len(text) > min_length:
                return True
            await asyncio.sleep(delay)
        return False

    async def wait_for_selector(self, selector: str, timeout: int = 30000):
        """Wait for element to appear."""
        return await self.page.wait_for_selector(selector, timeout=timeout)

    # === Interactions ===

    async def click(self, selector: str) -> None:
        """Click element by selector."""
        await self.page.click(selector)

    async def fill(self, selector: str, value: str) -> None:
        """Fill input field."""
        await self.page.fill(selector, value)

    async def type(self, selector: str, text: str, delay: int = 50) -> None:
        """Type text with realistic delay between keystrokes."""
        await self.page.type(selector, text, delay=delay)

    async def press(self, key: str) -> None:
        """Press a key (e.g., 'Enter', 'Tab')."""
        await self.page.keyboard.press(key)

    # === Selectors ===

    async def query_selector(self, selector: str):
        """Query single element."""
        return await self.page.query_selector(selector)

    async def query_selector_all(self, selector: str):
        """Query all elements matching selector."""
        return await self.page.query_selector_all(selector)

    async def evaluate(self, expression: str) -> Any:
        """Evaluate JavaScript expression."""
        return await self.page.evaluate(expression)
