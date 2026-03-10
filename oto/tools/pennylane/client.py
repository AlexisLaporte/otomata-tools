"""
Pennylane API Client - Fetch accounting data from Pennylane.

Requires: requests

Usage:
    client = PennylaneClient(api_key="your-api-key")

    # Get company info
    me = client.fetch("me")

    # Get trial balance for a year
    trial = client.fetch("trial_balance", {
        'period_start': '2025-01-01',
        'period_end': '2025-12-31'
    })

    # Fetch all pages of ledger accounts
    accounts = client.fetch_all_pages("ledger_accounts")
"""

import time
from typing import Optional

import requests

from ...config import require_secret


class PennylaneClient:
    """Client for Pennylane API v2"""

    BASE_URL = "https://app.pennylane.com/api/external/v2"

    def __init__(self, api_key: str = None, rate_limit_delay: float = 0.3):
        """
        Initialize the Pennylane client.

        Args:
            api_key: Pennylane API bearer token (or set PENNYLANE_API_KEY env var)
            rate_limit_delay: Delay between requests (default 0.3s for 4 req/sec limit)
        """
        self.api_key = api_key or require_secret("PENNYLANE_API_KEY")
        self.rate_limit_delay = rate_limit_delay
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        })

    def fetch(self, endpoint: str, params: Optional[dict] = None, retries: int = 3) -> dict:
        """
        Fetch data from Pennylane API with retry on rate limit.

        Args:
            endpoint: API endpoint (e.g., "me", "trial_balance", "ledger_accounts")
            params: Optional query parameters
            retries: Number of retries on rate limit

        Returns:
            JSON response as dict
        """
        url = f"{self.BASE_URL}/{endpoint}"

        for attempt in range(retries):
            try:
                response = self.session.get(url, params=params, timeout=30)

                if response.status_code == 429:  # Rate limited
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue

                if not response.ok:
                    return {
                        "error": str(response.status_code),
                        "details": response.text,
                        "status_code": response.status_code,
                    }

                return response.json()
            except Exception as e:
                return {"error": str(e)}

        return {"error": "Max retries exceeded"}

    def fetch_all_pages(
        self,
        endpoint: str,
        params: Optional[dict] = None,
        max_pages: Optional[int] = None,
        per_page: int = 100
    ) -> list:
        """
        Fetch all pages of a paginated endpoint.

        Args:
            endpoint: API endpoint
            params: Optional query parameters
            max_pages: Maximum number of pages to fetch (None for all)
            per_page: Items per page (default 100)

        Returns:
            List of all items across pages
        """
        all_data = []
        page = 1
        if params is None:
            params = {}
        params['per_page'] = per_page

        while True:
            params['page'] = page
            data = self.fetch(endpoint, params)
            time.sleep(self.rate_limit_delay)

            if 'error' in data:
                break

            # Handle different response formats
            if 'items' in data:
                items = data['items']
                total_pages = data.get('total_pages', 1)
            elif 'data' in data:
                items = data['data']
                total_pages = data.get('pagination', {}).get('total_pages', 1)
            else:
                # Single page response or unknown format
                return data if isinstance(data, list) else [data]

            if not items:
                break

            all_data.extend(items)

            if page >= total_pages:
                break
            if max_pages and page >= max_pages:
                break
            page += 1

        return all_data

    def get_company_info(self) -> dict:
        """Get company information."""
        return self.fetch("me")

    def get_fiscal_years(self) -> list:
        """Get fiscal years."""
        return self.fetch("fiscal_years")

    def get_trial_balance(self, start_date: str, end_date: str) -> list:
        """
        Get trial balance for a period.

        Args:
            start_date: Period start (YYYY-MM-DD)
            end_date: Period end (YYYY-MM-DD)
        """
        return self.fetch_all_pages("trial_balance", {
            'period_start': start_date,
            'period_end': end_date
        })

    def get_ledger_accounts(self) -> list:
        """Get all ledger accounts."""
        return self.fetch_all_pages("ledger_accounts")

    def get_ledger_entries(self, max_pages: Optional[int] = None) -> list:
        """Get ledger entries."""
        return self.fetch_all_pages("ledger_entries", max_pages=max_pages)

    def get_customer_invoices(self, max_pages: Optional[int] = None) -> list:
        """Get customer invoices."""
        return self.fetch_all_pages("customer_invoices", max_pages=max_pages)

    def get_supplier_invoices(self, max_pages: Optional[int] = None) -> list:
        """Get supplier invoices."""
        return self.fetch_all_pages("supplier_invoices", max_pages=max_pages)

    def get_categories(self) -> list:
        """Get expense categories."""
        return self.fetch("categories")

    def get_transactions(self, max_pages: Optional[int] = None) -> list:
        """Get bank transactions."""
        return self.fetch_all_pages("transactions", max_pages=max_pages)

    def fetch_complete_data(self, year: int = 2025) -> dict:
        """
        Fetch complete financial data for a year.

        Args:
            year: Fiscal year to fetch

        Returns:
            Dict with all financial data
        """
        data = {
            'company': self.get_company_info(),
            'fiscal_years': self.get_fiscal_years(),
            'ledger_accounts': self.get_ledger_accounts(),
            f'trial_balance_{year}': self.get_trial_balance(
                f'{year}-01-01', f'{year}-12-31'
            ),
            'customer_invoices': self.get_customer_invoices(max_pages=50),
            'supplier_invoices': self.get_supplier_invoices(max_pages=50),
            'categories': self.get_categories(),
        }
        return data
