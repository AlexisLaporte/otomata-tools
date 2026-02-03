"""
Crunchbase Client - Browser automation for Crunchbase scraping.

Requires browser optional dependency: pip install otomata[browser]
"""

import asyncio
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from urllib.parse import quote

from ...config import get_sessions_dir


class CrunchbaseClient:
    """
    Crunchbase automation client with:
    - Cookie-based authentication
    - Company and person scraping
    - Search functionality
    - Funding rounds extraction
    """

    def __init__(
        self,
        cookies: List[Dict] = None,
        headless: bool = True,
        user_agent: str = None,
    ):
        """
        Initialize Crunchbase client.

        Args:
            cookies: List of cookies for authentication
            headless: Run browser in headless mode
            user_agent: Custom user agent
        """
        self.headless = headless
        self.user_agent = user_agent
        self.cookies = cookies

        # Try to load from session file if not provided
        if not self.cookies:
            session_file = get_sessions_dir() / "crunchbase.json"
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
        """Start browser and load cookies."""
        try:
            from patchright.async_api import async_playwright
        except ImportError:
            raise ImportError(
                "Browser automation requires patchright. Install with: pip install otomata[browser]"
            )

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )

        context_options = {"viewport": {"width": 1920, "height": 1080}}
        if self.user_agent:
            context_options["user_agent"] = self.user_agent

        self.context = await self.browser.new_context(**context_options)

        if self.cookies:
            formatted_cookies = []
            for c in self.cookies:
                cookie = {
                    "name": c["name"],
                    "value": c["value"],
                    "domain": c["domain"],
                    "path": c.get("path", "/"),
                }
                same_site = c.get("sameSite", "Lax")
                if same_site and same_site.lower() in ("strict", "lax", "none"):
                    cookie["sameSite"] = same_site.capitalize()
                    if same_site.lower() == "none":
                        cookie["sameSite"] = "None"
                else:
                    cookie["sameSite"] = "Lax"
                formatted_cookies.append(cookie)
            await self.context.add_cookies(formatted_cookies)

        self.page = await self.context.new_page()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close browser."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def goto(self, url: str, timeout: int = 30000) -> bool:
        """Navigate to URL."""
        try:
            response = await self.page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            if response:
                status = response.status
                if status == 200 or (300 <= status < 400):
                    return True
            return False
        except Exception as e:
            print(f"Navigation error: {e}")
            return False

    async def is_logged_in(self) -> bool:
        """Check if logged in to Crunchbase."""
        await self.goto("https://www.crunchbase.com/")
        await asyncio.sleep(2)

        logged_in_indicators = [
            'a[href*="/dashboard"]',
            'a[href*="/home"]',
            '[class*="user-menu"]',
        ]

        for selector in logged_in_indicators:
            el = await self.page.query_selector(selector)
            if el:
                return True

        login_btn = await self.page.query_selector('a[href*="/login"]')
        return login_btn is None

    async def get_company(self, company_slug: str) -> Dict[str, Any]:
        """
        Get company details from Crunchbase.

        Args:
            company_slug: Company slug or full URL

        Returns:
            Company data dict
        """
        if "crunchbase.com" in company_slug:
            match = re.search(r"/organization/([^/?]+)", company_slug)
            if match:
                company_slug = match.group(1)

        url = f"https://www.crunchbase.com/organization/{company_slug}"

        if not await self.goto(url):
            return {"error": "Failed to load page", "url": url}

        await asyncio.sleep(3)

        data = {
            "slug": company_slug,
            "url": url,
            "name": None,
            "description": None,
            "founded": None,
            "headquarters": None,
            "company_size": None,
            "website": None,
            "linkedin": None,
            "twitter": None,
            "industries": [],
            "funding": {"total_raised": None},
            "investors": [],
            "key_people": [],
        }

        try:
            name_el = await self.page.query_selector(".entity-name")
            if name_el:
                data["name"] = (await name_el.inner_text()).strip()
            else:
                title = await self.page.title()
                if title and " - Crunchbase" in title:
                    data["name"] = title.split(" - Crunchbase")[0].strip()

            desc_el = await self.page.query_selector(".description")
            if desc_el:
                data["description"] = (await desc_el.inner_text()).strip()

            await self._extract_company_data(data)

        except Exception as e:
            data["error"] = str(e)

        return data

    async def _extract_company_data(self, data: Dict):
        """Extract all company data from the page."""
        try:
            # Funding
            funding_el = await self.page.query_selector(".field-type-money")
            if funding_el:
                text = await funding_el.inner_text()
                if text and "$" in text:
                    data["funding"]["total_raised"] = text.strip()

            # Investors
            investor_links = await self.page.query_selector_all('a[href*="/organization/"]')
            investors_seen = set()
            for link in investor_links[:50]:
                try:
                    href = await link.get_attribute("href")
                    if not href or "/organization/" not in href:
                        continue
                    slug = href.split("/organization/")[-1].split("/")[0].split("?")[0]
                    if slug.lower() == data.get("slug", "").lower():
                        continue
                    label = await link.query_selector(".identifier-label")
                    if label:
                        name = (await label.inner_text()).strip()
                        if name and name not in investors_seen:
                            investors_seen.add(name)
                            data["investors"].append({
                                "name": name,
                                "url": f"https://www.crunchbase.com{href}" if href.startswith("/") else href
                            })
                except:
                    continue

            # Key people
            people_links = await self.page.query_selector_all('a[href*="/person/"]')
            people_seen = set()
            for link in people_links[:30]:
                try:
                    href = await link.get_attribute("href")
                    label = await link.query_selector(".identifier-label")
                    if label:
                        name = (await label.inner_text()).strip()
                        if name and name not in people_seen:
                            people_seen.add(name)
                            data["key_people"].append({
                                "name": name,
                                "url": f"https://www.crunchbase.com{href}" if href.startswith("/") else href
                            })
                except:
                    continue

            # Industries
            chips = await self.page.query_selector_all('a[href*="/hub/"] .chip-text, a[href*="/search/"] .chip-text')
            industries = []
            for chip in chips[:15]:
                text = (await chip.inner_text()).strip()
                if text and not text.isdigit() and "$" not in text and 2 < len(text) < 50:
                    if text not in industries:
                        industries.append(text)
            data["industries"] = industries

            # Social links
            linkedin_el = await self.page.query_selector('a[title="View on LinkedIn"]')
            if linkedin_el:
                href = await linkedin_el.get_attribute("href")
                if href:
                    data["linkedin"] = href

            twitter_el = await self.page.query_selector('a[title="View on Twitter"], a[title="View on X"]')
            if twitter_el:
                href = await twitter_el.get_attribute("href")
                if href:
                    data["twitter"] = href

            # Founded
            founded_el = await self.page.query_selector(".field-type-date_precision")
            if founded_el:
                text = await founded_el.inner_text()
                year_match = re.search(r"\b(19\d{2}|20[0-2]\d)\b", text)
                if year_match:
                    data["founded"] = year_match.group(1)

            # Employee count
            emp_links = await self.page.query_selector_all('a[href*="num_employees"]')
            for link in emp_links[:1]:
                text = await link.inner_text()
                if re.search(r"\d+-\d+|\d+\+", text):
                    data["company_size"] = text.strip()
                    break

            # Headquarters
            location_links = await self.page.query_selector_all('a[href*="/location_identifiers/"]')
            locations = []
            for link in location_links[:3]:
                text = (await link.inner_text()).strip()
                if text and text not in locations:
                    locations.append(text)
            if locations:
                data["headquarters"] = ", ".join(locations)

        except Exception as e:
            print(f"Data extraction error: {e}")

    async def get_person(self, person_slug: str) -> Dict[str, Any]:
        """Get person details from Crunchbase."""
        if "crunchbase.com" in person_slug:
            match = re.search(r"/person/([^/?]+)", person_slug)
            if match:
                person_slug = match.group(1)

        url = f"https://www.crunchbase.com/person/{person_slug}"

        if not await self.goto(url):
            return {"error": "Failed to load page", "url": url}

        await asyncio.sleep(3)

        data = {
            "slug": person_slug,
            "url": url,
            "name": None,
            "bio": None,
            "linkedin": None,
            "twitter": None,
            "companies": [],
        }

        try:
            name_el = await self.page.query_selector(".entity-name")
            if name_el:
                data["name"] = (await name_el.inner_text()).strip()

            bio_el = await self.page.query_selector(".description")
            if bio_el:
                data["bio"] = (await bio_el.inner_text()).strip()

            # Companies
            company_links = await self.page.query_selector_all('a[href*="/organization/"]')
            companies_seen = set()
            for link in company_links[:20]:
                try:
                    href = await link.get_attribute("href")
                    label = await link.query_selector(".identifier-label")
                    if label:
                        name = (await label.inner_text()).strip()
                        if name and name not in companies_seen:
                            companies_seen.add(name)
                            data["companies"].append({
                                "name": name,
                                "url": f"https://www.crunchbase.com{href}" if href.startswith("/") else href
                            })
                except:
                    continue

        except Exception as e:
            data["error"] = str(e)

        return data

    async def search_companies(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for companies on Crunchbase."""
        url = f"https://www.crunchbase.com/textsearch?q={quote(query)}"

        if not await self.goto(url):
            return []

        await asyncio.sleep(3)

        results = []
        try:
            items = await self.page.query_selector_all('a[href*="/organization/"]')
            seen = set()

            for item in items[:limit * 2]:
                try:
                    href = await item.get_attribute("href")
                    if not href or "/organization/" not in href:
                        continue

                    slug = href.split("/organization/")[-1].split("/")[0].split("?")[0]
                    if slug in seen:
                        continue
                    seen.add(slug)

                    label = await item.query_selector(".identifier-label")
                    name = (await label.inner_text()).strip() if label else None

                    if name:
                        results.append({
                            "name": name,
                            "slug": slug,
                            "url": f"https://www.crunchbase.com/organization/{slug}"
                        })

                        if len(results) >= limit:
                            break
                except:
                    continue

        except Exception as e:
            print(f"Search error: {e}")

        return results

    async def search_people(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for people on Crunchbase."""
        url = f"https://www.crunchbase.com/textsearch?q={quote(query)}&type=people"

        if not await self.goto(url):
            return []

        await asyncio.sleep(3)

        results = []
        try:
            items = await self.page.query_selector_all('a[href*="/person/"]')
            seen = set()

            for item in items[:limit * 2]:
                try:
                    href = await item.get_attribute("href")
                    if not href or "/person/" not in href:
                        continue

                    slug = href.split("/person/")[-1].split("/")[0].split("?")[0]
                    if slug in seen:
                        continue
                    seen.add(slug)

                    label = await item.query_selector(".identifier-label")
                    name = (await label.inner_text()).strip() if label else None

                    if name:
                        results.append({
                            "name": name,
                            "slug": slug,
                            "url": f"https://www.crunchbase.com/person/{slug}"
                        })

                        if len(results) >= limit:
                            break
                except:
                    continue

        except Exception as e:
            print(f"People search error: {e}")

        return results

    async def get_funding_rounds(self, company_slug: str) -> List[Dict[str, Any]]:
        """Get funding rounds for a company."""
        url = f"https://www.crunchbase.com/organization/{company_slug}/company_financials"

        if not await self.goto(url):
            return []

        await asyncio.sleep(3)

        rounds = []
        try:
            rows = await self.page.query_selector_all('grid-row, [class*="funding-round"]')

            for row in rows[:20]:
                try:
                    round_data = {}

                    labels = await row.query_selector_all(".identifier-label")
                    if labels:
                        first_label = (await labels[0].inner_text()).strip()
                        round_data["round_type"] = first_label

                    money = await row.query_selector(".field-type-money")
                    if money:
                        round_data["amount"] = (await money.inner_text()).strip()

                    date = await row.query_selector(".field-type-date")
                    if date:
                        round_data["date"] = (await date.inner_text()).strip()

                    if round_data:
                        rounds.append(round_data)
                except:
                    continue

        except Exception as e:
            print(f"Funding rounds error: {e}")

        return rounds
