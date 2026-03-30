"""LinkedIn scraping mixins: profile, company, posts."""

import random
import re
from typing import List

from ._js import JS_PROFILE, JS_COMPANY_ABOUT, JS_POSTS


class ProfileMixin:
    """Scrape LinkedIn profiles and activity feeds."""

    async def scrape_profile(self, url: str) -> dict:
        """
        Scrape LinkedIn profile page.

        Returns:
            {url, name, headline, location, about}
        """
        await self.check_rate_limit("profile_visit")

        await self.goto(url)
        await self.wait(3)

        data = {"url": url}

        extracted = await self.page.evaluate(JS_PROFILE)

        if extracted.get("name"):
            data["name"] = extracted["name"]
        if extracted.get("about"):
            data["about"] = extracted["about"]

        # Parse topcard texts: filter out pronouns, connection degree, buttons
        skip_patterns = re.compile(
            r"^(·\s*\d|she/|he/|they/|coordonn|contact|message$|suivre$|follow$|"
            r"se connecter$|connect$|\d+\s*(relations?|connections?|abonnés|followers))",
            re.IGNORECASE,
        )
        topcard_texts = [
            t for t in extracted.get("_topcard_texts", [])
            if not skip_patterns.search(t) and t != data.get("name")
        ]
        if topcard_texts:
            data["headline"] = topcard_texts[0]
        for t in topcard_texts[1:]:
            if "," in t or any(kw in t.lower() for kw in [
                "france", "états-unis", "united", "paris", "london", "berlin",
                "région", "area", "metro", "périphérie",
            ]):
                data["location"] = t
                break

        return data

    async def scrape_profile_posts(self, url: str, max_posts: int = 10) -> List[dict]:
        """
        Scrape posts from a LinkedIn profile's activity feed.

        Args:
            url: Profile URL (e.g. https://www.linkedin.com/in/alexislaporte/)
            max_posts: Maximum number of posts to retrieve

        Returns:
            List of {content, date, url, is_repost, engagement: {reactions, comments}}
        """
        await self.check_rate_limit("profile_visit")

        activity_url = url.rstrip("/") + "/recent-activity/all/"
        await self.goto(activity_url)
        await self.wait(4)

        # Scroll to load posts
        last_count = 0
        stale_rounds = 0
        for i in range(max_posts // 2 + 3):
            await self.scroll_by(random.randint(400, 700))
            await self.wait(random.uniform(1.5, 2.5))

            count = await self.page.evaluate(
                'document.querySelectorAll("[data-urn*=\\"urn:li:activity\\"]").length'
            )
            if count >= max_posts:
                break
            if count == last_count:
                stale_rounds += 1
                if stale_rounds >= 3:
                    break
            else:
                stale_rounds = 0
                last_count = count

        return await self.page.evaluate(JS_POSTS, max_posts)


class CompanyMixin:
    """Scrape LinkedIn company pages."""

    async def scrape_company(self, url: str) -> dict:
        """
        Scrape LinkedIn company page.

        Returns:
            {url, name, tagline, about, website, phone, industry, size, founded, headquarters, company_id}
        """
        await self.check_rate_limit("company_scrape")

        about_url = url.rstrip("/") + "/about/"
        await self.goto(about_url)
        await self.wait(4)

        data = {"url": url}

        # Extract company ID
        html = await self.get_html()
        match = re.search(r"urn:li:fs_normalized_company:(\d+)", html)
        if match:
            data["company_id"] = match.group(1)

        # Company name
        h1 = await self.query_selector("h1")
        if h1:
            data["name"] = (await h1.inner_text()).strip()

        # About text + tagline via JS
        about_data = await self.page.evaluate(JS_COMPANY_ABOUT)
        if about_data.get("about"):
            data["about"] = about_data["about"]
        if about_data.get("tagline"):
            data["tagline"] = about_data["tagline"]

        # Extract dt/dd pairs (industry, size, HQ, etc.)
        dt_elements = await self.query_selector_all("dt")
        for dt in dt_elements:
            label = (await dt.inner_text()).strip().lower()
            dd = await dt.evaluate_handle("el => el.nextElementSibling")
            if dd:
                value = (await dd.inner_text()).strip()

                if "site web" in label or "website" in label:
                    data["website"] = value
                elif "téléphone" in label or "phone" in label:
                    data["phone"] = value.split("\n")[0]
                elif "secteur" in label or "industry" in label:
                    data["industry"] = value
                elif "taille" in label or "company size" in label:
                    data["size"] = value.split("\n")[0]
                elif "fondée" in label or "founded" in label:
                    data["founded"] = value
                elif "siège" in label or "headquarters" in label:
                    data["headquarters"] = value

        return data
