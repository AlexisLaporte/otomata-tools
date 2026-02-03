"""
Lemlist API Client for email campaign management.

Requires: requests
"""

import time
import base64
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

import requests

from ...config import require_secret


@dataclass
class Campaign:
    """Campaign data."""
    id: str
    name: str
    status: str
    senders: List[str]


@dataclass
class Lead:
    """Lead data for campaign."""
    email: str
    firstName: str = None
    lastName: str = None
    companyName: str = None
    phone: str = None
    picture: str = None
    linkedinUrl: str = None


class LemlistClient:
    """
    Lemlist API client for:
    - Campaign management
    - Lead management
    - Sequence/step management
    """

    BASE_URL = "https://api.lemlist.com/api"

    def __init__(self, api_key: str = None):
        """
        Initialize Lemlist client.

        Args:
            api_key: Lemlist API key (or set LEMLIST_API_KEY env var)
        """
        self.api_key = api_key or require_secret("LEMLIST_API_KEY")
        self._last_request = 0.0

    def _rate_limit(self):
        """Enforce minimum 100ms between requests."""
        elapsed = time.time() - self._last_request
        if elapsed < 0.1:
            time.sleep(0.1 - elapsed)
        self._last_request = time.time()

    def _get_auth_header(self) -> str:
        """Get Basic auth header."""
        credentials = f":{self.api_key}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Make API request."""
        self._rate_limit()

        url = f"{self.BASE_URL}/{endpoint}"
        headers = {"Authorization": self._get_auth_header()}

        response = requests.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()

        if response.content:
            return response.json()
        return {}

    def list_campaigns(self) -> List[Campaign]:
        """
        List all campaigns.

        Returns:
            List of Campaign objects
        """
        data = self._request("GET", "campaigns")
        return [
            Campaign(
                id=c["_id"],
                name=c.get("name", ""),
                status=c.get("status", ""),
                senders=c.get("senders", [])
            )
            for c in data
        ]

    def get_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """
        Get campaign details.

        Args:
            campaign_id: Campaign ID

        Returns:
            Campaign details
        """
        return self._request("GET", f"campaigns/{campaign_id}")

    def get_campaign_tree(self, campaign_id: str) -> Dict[str, Any]:
        """
        Get full campaign structure with sequences.

        Args:
            campaign_id: Campaign ID

        Returns:
            Campaign tree with sequences and steps
        """
        return self._request("GET", f"campaigns/{campaign_id}/tree")

    def add_lead(self, campaign_id: str, lead: Lead) -> Dict[str, Any]:
        """
        Add lead to campaign.

        Args:
            campaign_id: Campaign ID
            lead: Lead data

        Returns:
            Created lead
        """
        data = {"email": lead.email}
        if lead.firstName:
            data["firstName"] = lead.firstName
        if lead.lastName:
            data["lastName"] = lead.lastName
        if lead.companyName:
            data["companyName"] = lead.companyName
        if lead.phone:
            data["phone"] = lead.phone
        if lead.linkedinUrl:
            data["linkedinUrl"] = lead.linkedinUrl

        return self._request("POST", f"campaigns/{campaign_id}/leads", json=data)

    def delete_lead(self, campaign_id: str, email: str) -> Dict[str, Any]:
        """
        Remove lead from campaign.

        Args:
            campaign_id: Campaign ID
            email: Lead email

        Returns:
            Deletion result
        """
        return self._request("DELETE", f"campaigns/{campaign_id}/leads/{email}")

    def export_leads(self, campaign_id: str, state: str = None) -> str:
        """
        Export leads from campaign.

        Args:
            campaign_id: Campaign ID
            state: Filter by state (e.g., "interested", "notInterested")

        Returns:
            CSV export
        """
        params = {}
        if state:
            params["state"] = state

        response = requests.get(
            f"{self.BASE_URL}/campaigns/{campaign_id}/leads/export",
            headers={"Authorization": self._get_auth_header()},
            params=params
        )
        response.raise_for_status()
        return response.text
