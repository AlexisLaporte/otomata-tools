"""
ZeroBounce API Client for email verification.

Requires: requests
"""

from typing import Dict, Any, List

import requests

from ...config import require_secret


class ZeroBounceClient:
    """
    ZeroBounce API client for:
    - Single email verification
    - Batch email verification
    - Credits management
    """

    BASE_URL = "https://api.zerobounce.net/v2"

    def __init__(self, api_key: str = None):
        """
        Initialize ZeroBounce client.

        Args:
            api_key: ZeroBounce API key (or set ZEROBOUNCE_API_KEY env var)
        """
        self.api_key = api_key or require_secret("ZEROBOUNCE_API_KEY")

    def _request(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        """Make API request."""
        url = f"{self.BASE_URL}/{endpoint}"
        params = params or {}
        params["api_key"] = self.api_key

        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_credits(self) -> int:
        """
        Get remaining verification credits.

        Returns:
            Number of credits
        """
        data = self._request("getcredits")
        return int(data.get("Credits", 0))

    def verify_email(self, email: str) -> Dict[str, Any]:
        """
        Verify a single email address.

        Args:
            email: Email to verify

        Returns:
            Verification result with status:
            - valid: Deliverable
            - invalid: Undeliverable
            - catch-all: Domain accepts all
            - unknown: Unable to verify
            - spamtrap: Known spam trap
            - abuse: Abuse/complaint email
            - do_not_mail: Disposable/role-based
        """
        return self._request("validate", {"email": email})

    def verify_batch(self, emails: List[str]) -> List[Dict[str, Any]]:
        """
        Verify multiple emails (up to 200).

        Args:
            emails: List of emails to verify

        Returns:
            List of verification results
        """
        if len(emails) > 200:
            raise ValueError("Maximum 200 emails per batch")

        url = f"{self.BASE_URL}/validatebatch"
        data = {
            "api_key": self.api_key,
            "email_batch": [{"email_address": e} for e in emails]
        }

        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json().get("email_batch", [])
