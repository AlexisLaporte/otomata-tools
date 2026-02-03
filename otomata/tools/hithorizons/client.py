"""
HitHorizons API Client for company data.

Requires: requests
"""

import time
from typing import Optional, Dict, Any, List

import requests

from ...config import require_secret


class HitHorizonsClient:
    """
    HitHorizons Invoicing Data API client for:
    - Company search by name
    - Company details
    - Autocomplete suggestions
    """

    BASE_URL = "https://api.hithorizons.com/invoicing-partner"
    DEFAULT_COUNTRY = "FR"

    def __init__(self, api_key: str = None, country: str = DEFAULT_COUNTRY):
        """
        Initialize HitHorizons client.

        Args:
            api_key: HitHorizons API key (or set HITHORIZONS_API_KEY env var)
            country: Country code (default FR)
        """
        self.api_key = api_key or require_secret("HITHORIZONS_API_KEY")
        self.country = country
        self.session = requests.Session()
        self.session.headers.update({
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Accept": "application/json"
        })
        self._last_request = 0.0
        self._min_interval = 0.2  # 200ms

    def _rate_limit(self):
        """Ensure minimum time between requests."""
        elapsed = time.time() - self._last_request
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request = time.time()

    def _request(self, endpoint: str, params: Dict = None, retry: int = 0) -> Dict:
        """Make API request with rate limiting and retry."""
        self._rate_limit()

        url = f"{self.BASE_URL}/{self.country}/{endpoint}"

        response = self.session.get(url, params=params)

        if response.status_code == 429:
            if retry < 3:
                wait_time = 15 * (retry + 1)
                time.sleep(wait_time)
                return self._request(endpoint, params, retry + 1)
            else:
                raise Exception("Rate limit exceeded after 3 retries")

        response.raise_for_status()
        return response.json()

    def search_company(
        self,
        name: str,
        city: str = None,
        postal_code: str = None,
        max_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search for companies by name and location.

        Args:
            name: Company name
            city: City name (optional)
            postal_code: Postal code (optional)
            max_results: Maximum results

        Returns:
            List of matching companies
        """
        params = {"CompanyName": name, "MaxResults": max_results}
        if city:
            params["City"] = city
        if postal_code:
            params["PostalCode"] = postal_code

        result = self._request("Company/Search", params)

        if result.get("Success") and result.get("Result"):
            inner = result["Result"]
            if isinstance(inner, dict) and "Results" in inner:
                return inner["Results"]
            return inner if isinstance(inner, list) else []
        return []

    def search_unstructured(
        self,
        name: str,
        address: str = None,
        max_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search for companies with unstructured query.

        Args:
            name: Company name
            address: Full address string (optional)
            max_results: Maximum results

        Returns:
            List of matching companies
        """
        params = {"Name": name, "MaxResults": max_results}
        if address:
            params["Address"] = address

        result = self._request("Company/SearchUnstructured", params)

        if result.get("Success") and result.get("Result"):
            inner = result["Result"]
            if isinstance(inner, dict) and "Results" in inner:
                return inner["Results"]
            return inner if isinstance(inner, list) else []
        return []

    def get_detail(self, company_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed company information.

        Args:
            company_id: HitHorizons company ID

        Returns:
            Company details or None
        """
        result = self._request("Company/Detail", {"Id": company_id})

        if result.get("Success") and result.get("Result"):
            return result["Result"]
        return None

    def suggestions(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Get company name suggestions (autocomplete).

        Args:
            query: Search query
            max_results: Maximum results

        Returns:
            List of suggestions
        """
        result = self._request("Company/Suggestions", {
            "Query": query,
            "MaxResults": max_results
        })

        if result.get("Success") and result.get("Result"):
            return result["Result"]
        return []
