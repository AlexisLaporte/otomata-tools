"""
Folk CRM API Client.

Requires: requests
"""

import time
from typing import Optional, Dict, Any, List

import requests

from ...config import require_secret


class FolkClient:
    """
    Folk CRM API client for:
    - People/contacts management
    - Companies management
    - Deals management
    - Notes and groups
    """

    BASE_URL = "https://api.folk.app/v1"

    def __init__(self, api_key: str = None):
        """
        Initialize Folk client.

        Args:
            api_key: Folk API key (or set FOLK_API_KEY env var)
        """
        self.api_key = api_key or require_secret("FOLK_API_KEY")
        self._workspace_id = None
        self._api_calls = 0

    def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Make API request with retry on rate limit."""
        url = f"{self.BASE_URL}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        for attempt in range(3):
            response = requests.request(method, url, headers=headers, **kwargs)
            self._api_calls += 1

            if response.status_code == 429:
                time.sleep(2)
                continue

            response.raise_for_status()

            if response.content:
                return response.json()
            return {}

        raise Exception("Rate limit exceeded after retries")

    def validate_authentication(self) -> bool:
        """
        Validate API key and load workspace info.

        Returns:
            True if valid
        """
        try:
            data = self._request("GET", "me")
            if data.get("data", {}).get("workspaces"):
                self._workspace_id = data["data"]["workspaces"][0]["id"]
            return True
        except:
            return False

    def get_paginated_data(self, endpoint: str, params: Dict = None) -> List[Dict]:
        """
        Fetch all pages of data.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            All items
        """
        params = params or {}
        all_items = []
        cursor = None

        while True:
            if cursor:
                params["cursor"] = cursor

            data = self._request("GET", endpoint, params=params)
            items = data.get("data", {}).get("items", [])
            all_items.extend(items)

            pagination = data.get("data", {}).get("pagination", {})
            if not pagination.get("hasMore"):
                break

            cursor = pagination.get("cursor")
            if not cursor:
                break

        return all_items

    def fetch_people(self, group_filter: str = None) -> List[Dict[str, Any]]:
        """
        Fetch all contacts.

        Args:
            group_filter: Filter by group ID

        Returns:
            List of people
        """
        params = {}
        if group_filter:
            params["groupId"] = group_filter

        return self.get_paginated_data("people", params)

    def fetch_companies(self) -> List[Dict[str, Any]]:
        """Fetch all companies."""
        return self.get_paginated_data("companies")

    def fetch_deals(self) -> List[Dict[str, Any]]:
        """Fetch all deals."""
        return self.get_paginated_data("deals")

    def fetch_notes(self) -> List[Dict[str, Any]]:
        """Fetch all notes."""
        return self.get_paginated_data("notes")

    def fetch_groups(self) -> List[Dict[str, Any]]:
        """Fetch all groups."""
        return self.get_paginated_data("groups")

    def create_person(
        self,
        first_name: str,
        last_name: str = None,
        email: str = None,
        phone: str = None,
        company_id: str = None,
        **custom_fields,
    ) -> Dict[str, Any]:
        """
        Create a new person.

        Args:
            first_name: First name
            last_name: Last name
            email: Email address
            phone: Phone number
            company_id: Link to company
            **custom_fields: Additional fields

        Returns:
            Created person
        """
        data = {"firstName": first_name}
        if last_name:
            data["lastName"] = last_name
        if email:
            data["email"] = email
        if phone:
            data["phone"] = phone
        if company_id:
            data["companyId"] = company_id
        data.update(custom_fields)

        return self._request("POST", "people", json=data)

    def create_company(
        self,
        name: str,
        domain: str = None,
        **custom_fields,
    ) -> Dict[str, Any]:
        """
        Create a new company.

        Args:
            name: Company name
            domain: Company domain
            **custom_fields: Additional fields

        Returns:
            Created company
        """
        data = {"name": name}
        if domain:
            data["domain"] = domain
        data.update(custom_fields)

        return self._request("POST", "companies", json=data)

    def get_api_calls_count(self) -> int:
        """Get total API calls made."""
        return self._api_calls
