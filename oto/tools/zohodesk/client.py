"""Zoho Desk API Client — https://desk.zoho.com/DeskAPIDocument

OAuth scopes required (combine with comma at token-generation time):
  Desk.tickets.ALL
  Desk.contacts.READ
  Desk.basic.READ
  Desk.settings.READ

Secrets expected in environment / ~/.otomata/secrets.env:
  ZOHO_DESK_CLIENT_ID
  ZOHO_DESK_CLIENT_SECRET
  ZOHO_DESK_REFRESH_TOKEN
  ZOHO_DESK_ORG_ID            (header `orgId` required on every call)
  ZOHO_DESK_API_DOMAIN        (default https://desk.zoho.com — use .eu / .in if applicable)
  ZOHO_DESK_ACCOUNTS_URL      (default https://accounts.zoho.com — must match the data center)
"""

import json
import time
from typing import Any, Optional

import requests

from ...config import require_secret, get_secret, get_cache_dir


class ZohoDeskClient:
    API_VERSION = "v1"

    def __init__(self):
        self.client_id = require_secret("ZOHO_DESK_CLIENT_ID")
        self.client_secret = require_secret("ZOHO_DESK_CLIENT_SECRET")
        self.refresh_token = require_secret("ZOHO_DESK_REFRESH_TOKEN")
        self.org_id = require_secret("ZOHO_DESK_ORG_ID")
        self.api_domain = get_secret("ZOHO_DESK_API_DOMAIN", "https://desk.zoho.com")
        self.accounts_url = get_secret("ZOHO_DESK_ACCOUNTS_URL", "https://accounts.zoho.com")
        self._token_path = get_cache_dir() / "zoho-desk-access-token.json"

    # --- Auth ---

    def _get_access_token(self) -> str:
        if self._token_path.exists():
            data = json.loads(self._token_path.read_text())
            if data.get("expires_at", 0) > time.time() + 60:
                return data["access_token"]

        resp = requests.post(
            f"{self.accounts_url}/oauth/v2/token",
            params={
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
            },
        )
        resp.raise_for_status()
        token_data = resp.json()
        if "error" in token_data:
            raise ValueError(f"Zoho Desk OAuth error: {token_data['error']}")

        cache = {
            "access_token": token_data["access_token"],
            "expires_at": time.time() + token_data.get("expires_in", 3600),
        }
        self._token_path.parent.mkdir(parents=True, exist_ok=True)
        self._token_path.write_text(json.dumps(cache))
        return cache["access_token"]

    def _invalidate_token(self):
        self._token_path.unlink(missing_ok=True)

    # --- HTTP ---

    def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        url = f"{self.api_domain}/api/{self.API_VERSION}/{endpoint}"
        token = self._get_access_token()
        headers = {
            "Authorization": f"Zoho-oauthtoken {token}",
            "orgId": self.org_id,
        }
        if "json" in kwargs:
            headers["Content-Type"] = "application/json"

        for attempt in range(3):
            resp = requests.request(method, url, headers=headers, **kwargs)

            if resp.status_code == 401 and attempt == 0:
                self._invalidate_token()
                token = self._get_access_token()
                headers["Authorization"] = f"Zoho-oauthtoken {token}"
                continue

            if resp.status_code == 429:
                wait = int(resp.headers.get("Retry-After", 2))
                time.sleep(wait)
                continue

            if resp.status_code >= 400:
                try:
                    error_body = resp.json()
                except Exception:
                    error_body = resp.text
                raise Exception(f"HTTP {resp.status_code}: {error_body}")

            return resp.json() if resp.content else {}

        raise Exception("Request failed after retries")

    # --- Tickets ---

    def list_tickets(
        self,
        from_index: int = 1,
        limit: int = 50,
        department_id: Optional[str] = None,
        status: Optional[str] = None,
        sort_by: Optional[str] = None,
        fields: Optional[str] = None,
    ) -> dict:
        """List tickets. status: Open / On Hold / Escalated / Closed."""
        params: dict[str, Any] = {"from": from_index, "limit": min(limit, 100)}
        if department_id:
            params["departmentId"] = department_id
        if status:
            params["status"] = status
        if sort_by:
            params["sortBy"] = sort_by
        if fields:
            params["fields"] = fields
        return self._request("GET", "tickets", params=params)

    def get_ticket(self, ticket_id: str, include: Optional[str] = None) -> dict:
        """Get a single ticket. include: contacts,products,assignee,team,..."""
        params = {"include": include} if include else None
        return self._request("GET", f"tickets/{ticket_id}", params=params)

    def create_ticket(self, data: dict) -> dict:
        """Create a ticket. Required: subject, departmentId, contactId (or contact dict)."""
        return self._request("POST", "tickets", json=data)

    def update_ticket(self, ticket_id: str, data: dict) -> dict:
        """Patch ticket fields (status, priority, assignee, customFields, ...)."""
        return self._request("PATCH", f"tickets/{ticket_id}", json=data)

    def delete_ticket(self, ticket_id: str) -> dict:
        """Move a single ticket to trash (uses the bulk endpoint with one id)."""
        return self._request("POST", "tickets/moveToTrash", json={"ticketIds": [ticket_id]})

    def move_tickets_to_trash(self, ticket_ids: list[str]) -> dict:
        """Move multiple tickets to trash in one call (max 50 per Zoho)."""
        return self._request("POST", "tickets/moveToTrash", json={"ticketIds": ticket_ids})

    def search_tickets(self, query: dict, from_index: int = 1, limit: int = 50) -> dict:
        """Search tickets via /tickets/search. query: dict of field=value pairs."""
        params: dict[str, Any] = {"from": from_index, "limit": min(limit, 100), **query}
        return self._request("GET", "tickets/search", params=params)

    # --- Threads (replies / comments on a ticket) ---

    def list_threads(self, ticket_id: str) -> dict:
        return self._request("GET", f"tickets/{ticket_id}/threads")

    def get_thread(self, ticket_id: str, thread_id: str) -> dict:
        return self._request("GET", f"tickets/{ticket_id}/threads/{thread_id}")

    # --- Contacts ---

    def list_contacts(self, from_index: int = 1, limit: int = 50) -> dict:
        params = {"from": from_index, "limit": min(limit, 100)}
        return self._request("GET", "contacts", params=params)

    def get_contact(self, contact_id: str) -> dict:
        return self._request("GET", f"contacts/{contact_id}")

    def create_contact(self, data: dict) -> dict:
        """Create a contact. Required: lastName. Optional: firstName, email, phone, accountId."""
        return self._request("POST", "contacts", json=data)

    def search_contacts(self, query: dict) -> dict:
        return self._request("GET", "contacts/search", params=query)

    # --- Departments ---

    def list_departments(self) -> dict:
        return self._request("GET", "departments")

    # --- Agents ---

    def list_agents(self) -> dict:
        return self._request("GET", "agents")
