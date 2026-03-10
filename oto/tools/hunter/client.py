"""
Hunter.io API Client for email finding and verification.

Requires: requests
"""

from typing import Optional, Dict, Any

import requests

from ...config import require_secret


class HunterClient:
    """
    Hunter.io API client for:
    - Domain email search
    - Email finding by name
    - Email verification
    """

    BASE_URL = "https://api.hunter.io/v2"

    def __init__(self, api_key: str = None):
        """
        Initialize Hunter client.

        Args:
            api_key: Hunter API key (or set HUNTER_API_KEY env var)
        """
        self.api_key = api_key or require_secret("HUNTER_API_KEY")

    def _request(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        """Make API request."""
        url = f"{self.BASE_URL}/{endpoint}"
        params = params or {}
        params["api_key"] = self.api_key

        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def domain_search(self, domain: str, limit: int = 10) -> Dict[str, Any]:
        """
        Search for emails on a domain.

        Args:
            domain: Domain to search
            limit: Max results (1 credit per 10 emails)

        Returns:
            Emails found for domain
        """
        return self._request("domain-search", {"domain": domain, "limit": limit})

    def email_finder(
        self,
        domain: str,
        first_name: str = None,
        last_name: str = None,
        full_name: str = None,
    ) -> Dict[str, Any]:
        """
        Find email for a specific person.

        Args:
            domain: Company domain
            first_name: Person's first name
            last_name: Person's last name
            full_name: Full name (alternative to first/last)

        Returns:
            Email and confidence score (1 credit)
        """
        params = {"domain": domain}
        if first_name:
            params["first_name"] = first_name
        if last_name:
            params["last_name"] = last_name
        if full_name:
            params["full_name"] = full_name

        return self._request("email-finder", params)

    def email_verifier(self, email: str) -> Dict[str, Any]:
        """
        Verify an email address.

        Args:
            email: Email to verify

        Returns:
            Verification status (1 credit)
        """
        return self._request("email-verifier", {"email": email})

    def account_info(self) -> Dict[str, Any]:
        """
        Get account info with remaining credits.

        Returns:
            Account details and credits
        """
        return self._request("account")
