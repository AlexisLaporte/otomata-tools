"""
Indeed Client - Browser automation for job scraping.

Inherits from BrowserClient for browser management.
"""

import random
from typing import List, Dict, Any
from urllib.parse import urlencode

from .lib.browser_client import BrowserClient


class IndeedClient(BrowserClient):
    """
    Indeed job scraping client.

    Features:
    - Public job search (no auth needed)
    - Multiple country support (fr, us, uk, de)
    - Rate limiting to avoid detection
    - Job details extraction
    """

    BASE_URLS = {
        "fr": "https://fr.indeed.com",
        "us": "https://www.indeed.com",
        "uk": "https://uk.indeed.com",
        "de": "https://de.indeed.com",
    }

    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    def __init__(
        self,
        country: str = "fr",
        headless: bool = True,
    ):
        """
        Initialize Indeed client.

        Args:
            country: Country code (fr, us, uk, de)
            headless: Run browser in headless mode
        """
        super().__init__(
            headless=headless,
            user_agent=self.DEFAULT_USER_AGENT,
        )

        self.country = country
        self.base_url = self.BASE_URLS.get(country, self.BASE_URLS["fr"])
        self._request_count = 0

    async def _rate_limit_wait(self):
        """Wait between requests."""
        self._request_count += 1
        if self._request_count > 1:
            wait = random.uniform(2, 4)
            await self.wait(wait)

    async def _handle_cookie_consent(self):
        """Dismiss cookie consent popup."""
        try:
            selectors = [
                "button#onetrust-accept-btn-handler",
                'button:has-text("Accepter")',
                'button:has-text("Accept")',
            ]
            for selector in selectors:
                try:
                    btn = await self.wait_for_selector(selector, timeout=2000)
                    if btn:
                        await btn.click()
                        await self.wait(1)
                        return
                except:
                    continue
        except:
            pass

    async def search_jobs(
        self,
        query: str,
        location: str = "",
        radius: int = 25,
        max_results: int = 25,
        date_posted: str = "",
        job_type: str = "",
    ) -> List[Dict[str, Any]]:
        """
        Search for jobs on Indeed.

        Args:
            query: Job search query
            location: Location
            radius: Search radius in km
            max_results: Maximum results
            date_posted: Filter by date (1=24h, 3=3days, 7=week)
            job_type: Filter by type (fulltime, parttime, contract)

        Returns:
            List of job dicts
        """
        await self._rate_limit_wait()

        params = {"q": query, "l": location, "radius": radius}
        if date_posted:
            params["fromage"] = date_posted
        if job_type:
            params["jt"] = job_type

        search_url = f"{self.base_url}/jobs?{urlencode(params)}"

        await self.goto(search_url)
        await self.wait(2)
        await self._handle_cookie_consent()

        jobs = []
        pages_scraped = 0
        max_pages = (max_results // 15) + 1

        while len(jobs) < max_results and pages_scraped < max_pages:
            try:
                await self.wait_for_selector('[data-testid="jobTitle"], .jobTitle', timeout=10000)
            except:
                break

            await self._scroll_page()
            page_jobs = await self._extract_jobs_from_page()

            if not page_jobs:
                break

            jobs.extend(page_jobs)
            pages_scraped += 1

            if len(jobs) >= max_results:
                break

            has_next = await self._goto_next_page()
            if not has_next:
                break

            await self._rate_limit_wait()

        return jobs[:max_results]

    async def _scroll_page(self):
        """Scroll page to load lazy content."""
        for i in range(5):
            await self.scroll_by((i + 1) * 500)
            await self.wait(0.5)
        await self.evaluate("window.scrollTo(0, 0)")
        await self.wait(0.5)

    async def _extract_jobs_from_page(self) -> List[Dict[str, Any]]:
        """Extract job listings from current page."""
        jobs = []

        card_selectors = [".job_seen_beacon", "[data-jk]", ".resultContent"]
        cards = []

        for selector in card_selectors:
            cards = await self.query_selector_all(selector)
            if cards:
                break

        for card in cards:
            try:
                job = await self._extract_job_from_card(card)
                if job and job.get("title"):
                    jobs.append(job)
            except:
                continue

        return jobs

    async def _extract_job_from_card(self, card) -> Dict[str, Any]:
        """Extract job info from a single card."""
        job = {}

        job_id = await card.get_attribute("data-jk")
        if job_id:
            job["job_id"] = job_id
            job["url"] = f"{self.base_url}/viewjob?jk={job_id}"

        # Title
        title_selectors = ['[data-testid="jobTitle"]', ".jobTitle a", ".jobTitle span"]
        for selector in title_selectors:
            title_el = await card.query_selector(selector)
            if title_el:
                job["title"] = (await title_el.inner_text()).strip()
                if not job.get("url"):
                    href = await title_el.get_attribute("href")
                    if href:
                        job["url"] = f"{self.base_url}{href}" if href.startswith("/") else href
                break

        # Company
        company_selectors = ['[data-testid="company-name"]', ".companyName"]
        for selector in company_selectors:
            company_el = await card.query_selector(selector)
            if company_el:
                job["company"] = (await company_el.inner_text()).strip()
                break

        # Location
        location_selectors = ['[data-testid="text-location"]', ".companyLocation"]
        for selector in location_selectors:
            location_el = await card.query_selector(selector)
            if location_el:
                job["location"] = (await location_el.inner_text()).strip()
                break

        # Salary
        salary_el = await card.query_selector(".salary-snippet-container")
        if salary_el:
            salary_text = (await salary_el.inner_text()).strip()
            if any(c in salary_text.lower() for c in ["€", "$", "£", "an", "mois"]):
                job["salary"] = salary_text

        # Description
        desc_el = await card.query_selector(".job-snippet")
        if desc_el:
            job["description"] = (await desc_el.inner_text()).strip()

        return job

    async def _goto_next_page(self) -> bool:
        """Navigate to next page."""
        try:
            next_selectors = [
                '[data-testid="pagination-page-next"]',
                'a[aria-label="Next Page"]',
                'a[aria-label="Page suivante"]',
            ]

            for selector in next_selectors:
                try:
                    next_btn = await self.query_selector(selector)
                    if next_btn:
                        await next_btn.click()
                        await self.wait(2)
                        return True
                except:
                    continue

            return False
        except:
            return False

    async def get_job_details(self, job_url: str) -> Dict[str, Any]:
        """Get full job details."""
        await self._rate_limit_wait()

        await self.goto(job_url)
        await self.wait(2)
        await self._handle_cookie_consent()

        job = {"url": job_url}

        title_el = await self.query_selector('[data-testid="jobsearch-JobInfoHeader-title"]')
        if title_el:
            job["title"] = (await title_el.inner_text()).strip()

        company_el = await self.query_selector('[data-testid="inlineHeader-companyName"]')
        if company_el:
            job["company"] = (await company_el.inner_text()).strip()

        location_el = await self.query_selector('[data-testid="job-location"]')
        if location_el:
            job["location"] = (await location_el.inner_text()).strip()

        desc_el = await self.query_selector("#jobDescriptionText")
        if desc_el:
            job["full_description"] = (await desc_el.inner_text()).strip()

        return job
