#!/usr/bin/env python3
"""
Welcome to the Jungle client (browser-based).

Scrapes job listings from WTTJ search pages.
"""

import asyncio
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..browser.lib.browser_client import BrowserClient


class WTTJClient:
    """
    Welcome to the Jungle client using browser automation.

    Args:
        profile_path: Browser profile path for session persistence.
        headless: Run browser in headless mode.
    """

    BASE_URL = "https://www.welcometothejungle.com"

    def __init__(self, profile_path: Optional[str] = None, headless: bool = True):
        self.profile_path = profile_path
        self.headless = headless

    async def scrape_jobs(
        self,
        url: str,
        max_pages: int = 3,
        scroll_delay: float = 2.0,
        seen_ids: Optional[set[str]] = None,
    ) -> dict:
        """
        Scrape job listings from WTTJ search page.

        Args:
            url: WTTJ jobs search URL (with filters).
            max_pages: Maximum number of pages to scrape.
            scroll_delay: Delay between actions.
            seen_ids: Set of job slugs already seen. Stops when a seen ID is found.

        Returns:
            Dict with timestamp, url, total_results, and jobs list.
        """
        async with BrowserClient(profile_path=self.profile_path, headless=self.headless) as browser:
            print(f"Navigating to {url}...", file=sys.stderr)
            await browser.goto(url)
            await asyncio.sleep(3)

            all_jobs = []
            found_seen = False
            page = 1

            while page <= max_pages and not found_seen:
                print(f"Page {page}...", file=sys.stderr)

                # Wait for job cards to load
                await asyncio.sleep(scroll_delay)

                # Extract jobs from current page
                jobs = await browser.page.evaluate('''() => {
                    const jobs = [];
                    // WTTJ uses article or li elements for job cards
                    const cards = document.querySelectorAll('[data-testid="search-results-list-item-wrapper"], article[data-role="job-card"], li[data-testid*="job"]');

                    // Fallback: look for job links
                    if (cards.length === 0) {
                        const links = document.querySelectorAll('a[href*="/companies/"][href*="/jobs/"]');
                        links.forEach(link => {
                            const href = link.getAttribute('href');
                            const match = href.match(/\\/companies\\/([^\\/]+)\\/jobs\\/([^\\/\\?]+)/);
                            if (match) {
                                const card = link.closest('div[class*="sc-"]') || link.parentElement?.parentElement;
                                const text = card ? card.innerText : link.innerText;
                                jobs.push({
                                    company_slug: match[1],
                                    job_slug: match[2],
                                    url: href,
                                    raw_text: text
                                });
                            }
                        });
                    } else {
                        cards.forEach(card => {
                            const link = card.querySelector('a[href*="/jobs/"]');
                            if (link) {
                                const href = link.getAttribute('href');
                                const match = href.match(/\\/companies\\/([^\\/]+)\\/jobs\\/([^\\/\\?]+)/);
                                if (match) {
                                    jobs.push({
                                        company_slug: match[1],
                                        job_slug: match[2],
                                        url: href,
                                        raw_text: card.innerText
                                    });
                                }
                            }
                        });
                    }
                    return jobs;
                }''')

                if not jobs:
                    print("No jobs found on page, stopping.", file=sys.stderr)
                    break

                # Parse and dedupe jobs
                for job_data in jobs:
                    job_id = f"{job_data['company_slug']}/{job_data['job_slug']}"

                    # Check if we've seen this job before
                    if seen_ids and job_id in seen_ids:
                        found_seen = True
                        print(f"Found seen job {job_id}, stopping", file=sys.stderr)
                        break

                    # Check if already in current scrape
                    if any(j['id'] == job_id for j in all_jobs):
                        continue

                    # Parse job details from raw text
                    parsed = self._parse_job(job_data)
                    all_jobs.append(parsed)

                print(f"  {len(jobs)} offres sur la page, {len(all_jobs)} total", file=sys.stderr)

                if found_seen:
                    break

                # Try to go to next page
                page += 1
                if page <= max_pages:
                    # Update URL with new page number
                    next_url = re.sub(r'page=\d+', f'page={page}', url)
                    if 'page=' not in url:
                        next_url = url + f'&page={page}'
                    await browser.goto(next_url)
                    await asyncio.sleep(scroll_delay)

            print(f"Terminé: {len(all_jobs)} offres scrapées", file=sys.stderr)

            return {
                "timestamp": datetime.now().isoformat(),
                "url": url,
                "total_results": len(all_jobs),
                "jobs": all_jobs,
            }

    def _parse_job(self, job_data: dict) -> dict:
        """Parse job details from raw data."""
        raw_text = job_data.get('raw_text', '')
        lines = [l.strip() for l in raw_text.split('\n') if l.strip()]

        # Extract company name (usually first or second line, or from slug)
        company = job_data['company_slug'].replace('-', ' ').title()

        # Extract title (usually the main text)
        title = lines[0] if lines else job_data['job_slug'].replace('-', ' ').title()

        # Look for location
        location = None
        for line in lines:
            if any(city in line for city in ['Paris', 'Lyon', 'Toulouse', 'Bordeaux', 'Nantes', 'Marseille', 'Remote', 'France']):
                location = line
                break

        # Look for contract type
        contract = 'Freelance'  # Default based on filter
        for line in lines:
            if 'CDI' in line:
                contract = 'CDI'
            elif 'CDD' in line:
                contract = 'CDD'
            elif 'Freelance' in line:
                contract = 'Freelance'

        # Look for remote info
        remote = False
        for line in lines:
            if 'remote' in line.lower() or 'télétravail' in line.lower():
                remote = True
                break

        # Look for date
        date = None
        for line in lines:
            if any(x in line.lower() for x in ['il y a', 'aujourd', 'hier', 'jour', 'semaine', 'mois']):
                date = line
                break

        return {
            "id": f"{job_data['company_slug']}/{job_data['job_slug']}",
            "title": title,
            "company": company,
            "company_slug": job_data['company_slug'],
            "job_slug": job_data['job_slug'],
            "location": location,
            "remote": remote,
            "contract": contract,
            "date": date,
            "url": f"https://www.welcometothejungle.com{job_data['url']}" if job_data['url'].startswith('/') else job_data['url'],
        }


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Scrape Welcome to the Jungle jobs")
    parser.add_argument("--url", required=True, help="WTTJ jobs search URL")
    parser.add_argument("--profile", help="Browser profile path for session")
    parser.add_argument("--visible", action="store_true", help="Show browser")
    parser.add_argument("--pages", type=int, default=3, help="Max pages to scrape")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between pages")
    parser.add_argument("--output", "-o", help="Output JSON file path")
    parser.add_argument("--seen-file", help="JSON file with seen IDs (stops when a seen ID is found)")
    args = parser.parse_args()

    # Load seen IDs if provided
    seen_ids = None
    if args.seen_file:
        seen_data = json.loads(Path(args.seen_file).read_text())
        seen_ids = set(seen_data.get("ids", []))
        print(f"Loaded {len(seen_ids)} seen IDs", file=sys.stderr)

    client = WTTJClient(profile_path=args.profile, headless=not args.visible)
    result = await client.scrape_jobs(
        url=args.url,
        max_pages=args.pages,
        scroll_delay=args.delay,
        seen_ids=seen_ids,
    )

    output = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        Path(args.output).write_text(output)
        print(f"Saved to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    asyncio.run(main())
