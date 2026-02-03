"""
SerpAPI Client for Google Jobs and search.

Requires: requests
"""

import time
from typing import Optional, Dict, Any

import requests

from ...config import require_secret


class SerpAPIClient:
    """
    SerpAPI client for:
    - Google Jobs search
    - Job details retrieval
    """

    BASE_URL = "https://serpapi.com/search"

    def __init__(self, api_key: str = None):
        """
        Initialize SerpAPI client.

        Args:
            api_key: SerpAPI key (or set SERPAPI_API_KEY env var)
        """
        self.api_key = api_key or require_secret("SERPAPI_API_KEY")
        self.session = requests.Session()
        self._last_request = 0.0
        self._min_interval = 1.0

    def _rate_limit(self):
        """Ensure minimum time between requests."""
        elapsed = time.time() - self._last_request
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request = time.time()

    def _request(self, params: Dict) -> Dict:
        """Make API request."""
        self._rate_limit()
        params["api_key"] = self.api_key

        response = self.session.get(self.BASE_URL, params=params)
        response.raise_for_status()
        return response.json()

    def search_jobs(
        self,
        company: str,
        location: str = None,
        country: str = None,
        language: str = "en",
        max_results: int = 100,
        no_cache: bool = False,
    ) -> Dict[str, Any]:
        """
        Search Google Jobs for company job postings.

        Args:
            company: Company name
            location: Geographic location (e.g., 'Paris, France')
            country: Country code (e.g., 'fr', 'us')
            language: Language code
            max_results: Maximum results (handles pagination)
            no_cache: Force fresh results

        Returns:
            Dict with jobs_results array
        """
        query = f"{company} jobs"

        params = {
            "engine": "google_jobs",
            "q": query,
            "hl": language,
            "no_cache": str(no_cache).lower()
        }

        if location:
            params["location"] = location
        if country:
            params["gl"] = country

        result = self._request(params)
        all_jobs = result.get("jobs_results", [])

        # Handle pagination
        page = 2
        while len(all_jobs) < max_results:
            pagination = result.get("serpapi_pagination", {})
            next_token = pagination.get("next_page_token")

            if not next_token:
                break

            params["next_page_token"] = next_token
            result = self._request(params)

            new_jobs = result.get("jobs_results", [])
            if not new_jobs:
                break

            all_jobs.extend(new_jobs)
            page += 1

        result["jobs_results"] = all_jobs[:max_results]
        return result

    def get_job_details(self, job_id: str) -> Dict[str, Any]:
        """
        Get detailed job information.

        Args:
            job_id: Google Jobs job ID

        Returns:
            Detailed job information
        """
        params = {
            "engine": "google_jobs_listing",
            "q": job_id
        }
        return self._request(params)
