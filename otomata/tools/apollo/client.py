"""
Apollo.io API Client for lead enrichment and search.

Requires: requests
"""

import time
from typing import Optional, Dict, Any, List

import requests

from ...config import require_secret


class ApolloClient:
    """
    Apollo.io API client for:
    - Organization search and enrichment
    - People search and matching
    - Job postings lookup
    """

    BASE_URL = "https://api.apollo.io/v1"

    def __init__(self, api_key: str = None):
        """
        Initialize Apollo client.

        Args:
            api_key: Apollo API key (or set APOLLO_API_KEY env var)
        """
        self.api_key = api_key or require_secret("APOLLO_API_KEY")
        self._last_request = 0.0

    def _rate_limit(self):
        """Enforce minimum 1 second between requests."""
        elapsed = time.time() - self._last_request
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)
        self._last_request = time.time()

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make API request."""
        self._rate_limit()

        url = f"{self.BASE_URL}/{endpoint}"
        headers = {"X-Api-Key": self.api_key, "Content-Type": "application/json"}

        response = requests.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        return response.json()

    def search_organizations(
        self,
        name: str = None,
        domain: str = None,
        country: str = None,
        per_page: int = 10,
    ) -> Dict[str, Any]:
        """
        Search for organizations.

        Args:
            name: Company name to search
            domain: Domain to search
            country: Country filter
            per_page: Results per page

        Returns:
            Dict with organizations list
        """
        data = {"per_page": per_page}
        if name:
            data["organization_name"] = name
        if domain:
            data["organization_domain"] = domain
        if country:
            data["organization_locations"] = [country]

        return self._request("POST", "organizations/search", json=data)

    def enrich_organization(self, domain: str) -> Dict[str, Any]:
        """
        Enrich organization by domain.

        Args:
            domain: Company domain

        Returns:
            Detailed company data
        """
        return self._request("GET", "organizations/enrich", params={"domain": domain})

    def search_people(
        self,
        domains: List[str] = None,
        org_ids: List[str] = None,
        departments: List[str] = None,
        titles: List[str] = None,
        seniorities: List[str] = None,
        per_page: int = 25,
        page: int = 1,
    ) -> Dict[str, Any]:
        """
        Search for people.

        Args:
            domains: Company domains to search
            org_ids: Apollo organization IDs
            departments: Department filters (e.g., ["engineering", "sales"])
            titles: Title keywords
            seniorities: Seniority levels (e.g., ["c_suite", "director"])
            per_page: Results per page
            page: Page number

        Returns:
            People search results
        """
        data = {"per_page": per_page, "page": page}
        if domains:
            data["organization_domains"] = domains
        if org_ids:
            data["organization_ids"] = org_ids
        if departments:
            data["person_departments"] = departments
        if titles:
            data["person_titles"] = titles
        if seniorities:
            data["person_seniorities"] = seniorities

        return self._request("POST", "people/search", json=data)

    def match_person(
        self,
        linkedin_url: str = None,
        email: str = None,
        first_name: str = None,
        last_name: str = None,
        name: str = None,
        domain: str = None,
        org_name: str = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Match a specific person.

        Args:
            linkedin_url: LinkedIn profile URL
            email: Email address
            first_name: First name
            last_name: Last name
            name: Full name
            domain: Company domain
            org_name: Organization name

        Returns:
            Matched person data or None
        """
        data = {}
        if linkedin_url:
            data["linkedin_url"] = linkedin_url
        if email:
            data["email"] = email
        if first_name:
            data["first_name"] = first_name
        if last_name:
            data["last_name"] = last_name
        if name:
            data["name"] = name
        if domain:
            data["organization_domain"] = domain
        if org_name:
            data["organization_name"] = org_name

        try:
            return self._request("POST", "people/match", json=data)
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise

    def get_job_postings(self, org_id: str) -> Dict[str, Any]:
        """
        Get job postings for an organization.

        Args:
            org_id: Apollo organization ID

        Returns:
            Job postings list
        """
        return self._request("GET", f"organizations/{org_id}/job_postings")
