"""
G2 Client - Browser automation for G2 product review scraping.

Requires browser optional dependency: pip install otomata[browser]
"""

import asyncio
import json
import re
from typing import Optional, Dict, Any, List

from ...config import get_sessions_dir


class G2Client:
    """
    G2 automation client for product review scraping.

    Features:
    - Product review extraction with pagination
    - Rating and sentiment extraction
    - Product search
    - Cookie-based session support
    """

    def __init__(
        self,
        headless: bool = True,
        cookies: List[Dict] = None,
        user_agent: str = None,
    ):
        """
        Initialize G2 client.

        Args:
            headless: Run browser in headless mode
            cookies: List of cookies (for authenticated access)
            user_agent: Custom user agent
        """
        self.headless = headless
        self.cookies = cookies or []
        self.user_agent = user_agent or "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

        # Try to load from session file
        if not self.cookies:
            session_file = get_sessions_dir() / "g2.json"
            if session_file.exists():
                data = json.loads(session_file.read_text())
                if data.get("valid"):
                    self.cookies = data.get("cookies", [])
                    self.user_agent = self.user_agent or data.get("user_agent")

        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def __aenter__(self):
        """Start browser."""
        try:
            from patchright.async_api import async_playwright
        except ImportError:
            raise ImportError(
                "Browser automation requires patchright. Install with: pip install otomata[browser]"
            )

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)

        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=self.user_agent
        )

        if self.cookies:
            playwright_cookies = []
            for c in self.cookies:
                cookie = {
                    "name": c["name"],
                    "value": c["value"],
                    "domain": c.get("domain", ".g2.com"),
                    "path": c.get("path", "/"),
                }
                if c.get("sameSite"):
                    same_site = c["sameSite"].lower()
                    if same_site in ["strict", "lax", "none"]:
                        cookie["sameSite"] = same_site.capitalize()
                playwright_cookies.append(cookie)
            await self.context.add_cookies(playwright_cookies)

        self.page = await self.context.new_page()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close browser."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def get_product_reviews(
        self,
        product_url: str,
        max_reviews: int = 50,
    ) -> Dict[str, Any]:
        """
        Scrape reviews from a G2 product page.

        Args:
            product_url: G2 product reviews URL
            max_reviews: Maximum number of reviews to scrape

        Returns:
            Dict with product info and reviews
        """
        await self.page.goto(product_url, wait_until="networkidle", timeout=30000)

        try:
            await self.page.wait_for_selector('[itemprop="review"]', timeout=15000)
        except:
            await asyncio.sleep(3)

        product_info = await self._extract_product_info()

        reviews = []
        page_num = 1

        while len(reviews) < max_reviews:
            page_reviews = await self._extract_reviews_from_page()

            if not page_reviews:
                break

            reviews.extend(page_reviews)

            if len(reviews) >= max_reviews:
                reviews = reviews[:max_reviews]
                break

            # Try next page via URL
            page_num += 1
            base_url = product_url.split("?")[0]
            next_url = f"{base_url}?page={page_num}"
            await self.page.goto(next_url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)

            test_reviews = await self._extract_reviews_from_page()
            if not test_reviews:
                break

        return {
            "product": product_info,
            "reviews": reviews,
            "total_scraped": len(reviews),
            "url": product_url
        }

    async def _extract_product_info(self) -> Dict[str, Any]:
        """Extract product metadata."""
        try:
            name_elem = await self.page.query_selector("h1")
            name = await name_elem.inner_text() if name_elem else "Unknown"

            rating_elem = await self.page.query_selector('[itemprop="ratingValue"]')
            rating = await rating_elem.inner_text() if rating_elem else None

            review_count_elem = await self.page.query_selector('[itemprop="reviewCount"]')
            review_count = await review_count_elem.inner_text() if review_count_elem else None

            return {
                "name": name.strip(),
                "overall_rating": rating.strip() if rating else None,
                "total_reviews": review_count.strip() if review_count else None
            }
        except Exception as e:
            return {"name": "Unknown", "overall_rating": None, "total_reviews": None}

    async def _extract_reviews_from_page(self) -> List[Dict[str, Any]]:
        """Extract all reviews from current page."""
        reviews = []

        selectors = ['[itemprop="review"]', ".review-card", '[data-test="review"]']
        review_containers = []

        for selector in selectors:
            review_containers = await self.page.query_selector_all(selector)
            if review_containers:
                break

        for container in review_containers:
            try:
                review_data = await self._extract_single_review(container)
                if review_data:
                    reviews.append(review_data)
            except:
                continue

        return reviews

    async def _extract_single_review(self, container) -> Optional[Dict[str, Any]]:
        """Extract data from a single review container."""
        try:
            container_text = await container.inner_text()

            # Rating
            rating = None
            rating_elem = await container.query_selector('[itemprop="ratingValue"]')
            if rating_elem:
                rating = await rating_elem.get_attribute("content")

            # Title
            title = ""
            title_elem = await container.query_selector('[itemprop="name"], h3, h4')
            if title_elem:
                title = await title_elem.inner_text()

            # Review text
            text = ""
            text_elem = await container.query_selector('[itemprop="reviewBody"], .review-text')
            if text_elem:
                text = await text_elem.inner_text()

            # Reviewer
            reviewer_name = "Anonymous"
            reviewer_elem = await container.query_selector('[itemprop="author"]')
            if reviewer_elem:
                reviewer_name = await reviewer_elem.inner_text()

            # Date
            date = None
            date_elem = await container.query_selector('[itemprop="datePublished"], time')
            if date_elem:
                date = await date_elem.get_attribute("content") or await date_elem.inner_text()

            if not rating and not text:
                return None

            return {
                "rating": float(rating) if rating else None,
                "title": title.strip(),
                "review_text": text.strip(),
                "reviewer": {"name": reviewer_name.strip()},
                "date": date,
            }
        except:
            return None

    async def search_products(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for products on G2."""
        search_url = f"https://www.g2.com/search?query={query}"

        await self.page.goto(search_url, wait_until="networkidle")

        try:
            await self.page.wait_for_selector(".product-listing", timeout=10000)
        except:
            return []

        products = []
        product_cards = await self.page.query_selector_all(".product-listing")

        for card in product_cards[:limit]:
            try:
                name_elem = await card.query_selector(".product-listing__product-name")
                name = await name_elem.inner_text() if name_elem else ""

                link_elem = await card.query_selector("a.product-listing__product-name")
                link = await link_elem.get_attribute("href") if link_elem else ""

                rating_elem = await card.query_selector(".stars")
                rating = await rating_elem.get_attribute("data-rating") if rating_elem else None

                products.append({
                    "name": name.strip(),
                    "url": f"https://www.g2.com{link}" if link else "",
                    "rating": rating
                })
            except:
                continue

        return products
