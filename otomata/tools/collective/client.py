#!/usr/bin/env python3
"""
Collective.work client (browser-based).

No public API available, so we use browser automation.
"""

import asyncio
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..browser.lib.browser_client import BrowserClient


class CollectiveClient:
    """
    Collective.work client using browser automation.

    Args:
        profile_path: Browser profile path for session persistence.
        headless: Run browser in headless mode.
    """

    BASE_URL = "https://app.collective.work"

    def __init__(self, profile_path: Optional[str] = None, headless: bool = True):
        self.profile_path = profile_path
        self.headless = headless

    async def scrape_jobs(
        self,
        url: str,
        max_scroll: int = 3,
        scroll_until_end: bool = False,
        scroll_delay: float = 3.0,
        screenshot_path: Optional[str] = None,
    ) -> dict:
        """
        Scrape job listings from Collective.work.

        Args:
            url: Jobs page URL (with filters).
            max_scroll: Number of scrolls to load more jobs (ignored if scroll_until_end=True).
            scroll_until_end: Keep scrolling until no new jobs are loaded.
            scroll_delay: Delay in seconds between scrolls.
            screenshot_path: Optional path to save screenshot.

        Returns:
            Dict with timestamp, url, total_results, and jobs list.
        """
        async with BrowserClient(profile_path=self.profile_path, headless=self.headless) as browser:
            print(f"Navigating to {url}...", file=sys.stderr)
            await browser.goto(url)

            await asyncio.sleep(3)
            await browser.wait_for_content()

            # Collective uses a specific scrollable container with virtual scroll
            # We need to accumulate jobs as we scroll (they disappear from DOM)
            scroll_selector = "#jobs-scrollable"
            all_jobs = {}  # Use dict to dedupe by id

            all_job_ids = []  # Accumulate jobIds in order

            if scroll_until_end:
                # Scroll until no new content loads, accumulating jobs
                prev_total = 0
                scroll_num = 0
                no_change_count = 0
                while no_change_count < 3:  # Stop after 3 scrolls with no new jobs
                    raw_text = await browser.get_text()
                    current_jobs = self._parse_jobs(raw_text)
                    # Extract jobIds from visible links
                    job_ids = await browser.page.evaluate('''() => {
                        const links = document.querySelectorAll("a[href*='jobId=']");
                        return Array.from(links).map(a => {
                            const match = a.href.match(/jobId=([a-z0-9]+)/);
                            return match ? match[1] : null;
                        }).filter(Boolean);
                    }''')
                    for jid in job_ids:
                        if jid not in all_job_ids:
                            all_job_ids.append(jid)
                    for job in current_jobs:
                        all_jobs[job["id"]] = job
                    scroll_num += 1
                    print(f"Scroll {scroll_num}... ({len(all_jobs)} offres total)", file=sys.stderr)
                    if len(all_jobs) == prev_total:
                        no_change_count += 1
                    else:
                        no_change_count = 0
                    prev_total = len(all_jobs)
                    await browser.scroll_element(scroll_selector, times=1, delay=scroll_delay)
                print(f"Fin du scroll après {scroll_num} scrolls", file=sys.stderr)
                jobs = list(all_jobs.values())
            else:
                for i in range(max_scroll):
                    raw_text = await browser.get_text()
                    current_jobs = self._parse_jobs(raw_text)
                    # Extract jobIds from visible links
                    job_ids = await browser.page.evaluate('''() => {
                        const links = document.querySelectorAll("a[href*='jobId=']");
                        return Array.from(links).map(a => {
                            const match = a.href.match(/jobId=([a-z0-9]+)/);
                            return match ? match[1] : null;
                        }).filter(Boolean);
                    }''')
                    for jid in job_ids:
                        if jid not in all_job_ids:
                            all_job_ids.append(jid)
                    for job in current_jobs:
                        all_jobs[job["id"]] = job
                    print(f"Scroll {i + 1}/{max_scroll}... ({len(all_jobs)} offres total)", file=sys.stderr)
                    await browser.scroll_element(scroll_selector, times=1, delay=scroll_delay)
                # Final parse after last scroll
                raw_text = await browser.get_text()
                for job in self._parse_jobs(raw_text):
                    all_jobs[job["id"]] = job
                jobs = list(all_jobs.values())

            # Assign jobIds to jobs (by position order)
            for i, job in enumerate(jobs):
                if i < len(all_job_ids):
                    job["jobId"] = all_job_ids[i]
                    job["url"] = f"https://app.collective.work/collective/alexis-laporte/jobs?jobId={all_job_ids[i]}"

            if screenshot_path:
                await browser.screenshot(screenshot_path)
                print(f"Screenshot: {screenshot_path}", file=sys.stderr)

            return {
                "timestamp": datetime.now().isoformat(),
                "url": url,
                "total_results": len(jobs),
                "jobs": jobs,
            }

    async def get_job_details(self, job_url: str) -> dict:
        """
        Get full details of a single job listing.

        Args:
            job_url: URL of the job page.

        Returns:
            Dict with full job details including description.
        """
        async with BrowserClient(profile_path=self.profile_path, headless=self.headless) as browser:
            print(f"Fetching {job_url}...", file=sys.stderr)
            await browser.goto(job_url)
            await asyncio.sleep(2)
            await browser.wait_for_content()

            raw_text = await browser.get_text()
            return {
                "url": job_url,
                "content": raw_text,
            }

    def _parse_jobs(self, raw_text: str) -> list[dict]:
        """Parse job listings from raw page text."""
        jobs = []
        parts = raw_text.split("Voir l'offre")

        for i, part in enumerate(parts[:-1]):
            lines = [l.strip() for l in part.split("\n") if l.strip()]
            if len(lines) < 3:
                continue

            company = None
            title = None

            for line in reversed(lines):
                if not title and len(line) > 5 and "€" not in line and "il y a" not in line and "résultats" not in line:
                    title = line
                elif title and not company and 2 < len(line) < 60:
                    company = line
                    break

            if not title:
                continue

            details = parts[i + 1] if i + 1 < len(parts) else ""

            # Parse TJM
            tjm_match = re.search(r"(\d{3,4})(?:€| à |\n)", details)
            tjm = int(tjm_match.group(1)) if tjm_match else None

            # Parse date
            date_match = re.search(r"il y a ([^\n•]+)", details)
            date = date_match.group(1).strip() if date_match else None

            # Parse location
            loc_match = re.search(
                r"(Paris|Lyon|Toulouse|Bordeaux|Nantes|Marseille|Bruxelles|France|Belgique|Remote)[^\n]*",
                details,
                re.I,
            )
            location = loc_match.group(0).strip() if loc_match else None

            # Remote?
            remote = "remote" in details.lower() or "télétravail" in details.lower()

            # Job type
            job_type = "Freelance" if "Freelance" in details else "CDI" if "CDI" in details else None

            # Expertises
            exp_match = re.search(r"Expertises?\s*\n([^\n]+(?:\n[^\n]+)*?)(?:\nil y a|$)", details)
            expertises = []
            if exp_match:
                exp_text = exp_match.group(1)
                expertises = [
                    e.strip()
                    for e in exp_text.split("\n")
                    if e.strip() and len(e.strip()) > 1 and "il y a" not in e.lower()
                ][:5]

            # Generate ID from title+company hash
            job_id = f"{hash((title, company)) & 0xFFFFFFFF:08x}"

            jobs.append({
                "id": job_id,
                "title": title,
                "company": company,
                "tjm": tjm,
                "date": date,
                "location": location,
                "remote": remote,
                "type": job_type,
                "expertises": expertises,
            })

        return jobs


def filter_jobs(
    jobs: list[dict],
    keywords: Optional[list[str]] = None,
    exclude: Optional[list[str]] = None,
    min_tjm: Optional[int] = None,
) -> list[dict]:
    """
    Filter jobs by criteria.

    Args:
        jobs: List of job dicts.
        keywords: Include jobs matching these keywords in title/expertises.
        exclude: Exclude jobs matching these keywords.
        min_tjm: Minimum TJM.

    Returns:
        Filtered list of jobs.
    """
    def matches(text: str, kws: list[str]) -> bool:
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in kws)

    result = jobs

    if min_tjm:
        result = [j for j in result if j.get("tjm") and j["tjm"] >= min_tjm]

    if exclude:
        result = [
            j for j in result
            if not matches(f"{j['title']} {' '.join(j.get('expertises', []))}", exclude)
        ]

    if keywords:
        result = [
            j for j in result
            if matches(f"{j['title']} {' '.join(j.get('expertises', []))}", keywords)
        ]

    return result


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Scrape Collective.work jobs")
    parser.add_argument("--url", required=True, help="Collective.work jobs URL")
    parser.add_argument("--profile", help="Browser profile path for session")
    parser.add_argument("--visible", action="store_true", help="Show browser")
    parser.add_argument("--scroll", type=int, default=3, help="Number of scrolls")
    parser.add_argument("--scroll-until-end", action="store_true", help="Scroll until no new jobs load")
    parser.add_argument("--scroll-delay", type=float, default=3.0, help="Delay between scrolls (seconds)")
    parser.add_argument("--screenshot", help="Screenshot output path")
    parser.add_argument("--output", "-o", help="Output JSON file path")
    args = parser.parse_args()

    client = CollectiveClient(profile_path=args.profile, headless=not args.visible)
    result = await client.scrape_jobs(
        url=args.url,
        max_scroll=args.scroll,
        scroll_until_end=args.scroll_until_end,
        scroll_delay=args.scroll_delay,
        screenshot_path=args.screenshot,
    )

    output = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        Path(args.output).write_text(output)
        print(f"Saved to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    asyncio.run(main())
