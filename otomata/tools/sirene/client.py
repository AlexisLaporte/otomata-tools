"""
INSEE Sirene API Client for French company data.

Requires: requests

Authentication:
    SIRENE_API_KEY: API key from https://portail-api.insee.fr/
"""

import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

import requests

from ...config import get_secret


EMPLOYEE_RANGES = [
    {'code': 'NN', 'label': 'Unités non employeuses', 'min': 0, 'max': 0},
    {'code': '00', 'label': '0 salarié', 'min': 0, 'max': 0},
    {'code': '01', 'label': '1 ou 2 salariés', 'min': 1, 'max': 2},
    {'code': '02', 'label': '3 à 5 salariés', 'min': 3, 'max': 5},
    {'code': '03', 'label': '6 à 9 salariés', 'min': 6, 'max': 9},
    {'code': '11', 'label': '10 à 19 salariés', 'min': 10, 'max': 19},
    {'code': '12', 'label': '20 à 49 salariés', 'min': 20, 'max': 49},
    {'code': '21', 'label': '50 à 99 salariés', 'min': 50, 'max': 99},
    {'code': '22', 'label': '100 à 199 salariés', 'min': 100, 'max': 199},
    {'code': '31', 'label': '200 à 249 salariés', 'min': 200, 'max': 249},
    {'code': '32', 'label': '250 à 499 salariés', 'min': 250, 'max': 499},
    {'code': '41', 'label': '500 à 999 salariés', 'min': 500, 'max': 999},
    {'code': '42', 'label': '1 000 à 1 999 salariés', 'min': 1000, 'max': 1999},
    {'code': '51', 'label': '2 000 à 4 999 salariés', 'min': 2000, 'max': 4999},
    {'code': '52', 'label': '5 000 à 9 999 salariés', 'min': 5000, 'max': 9999},
    {'code': '53', 'label': '10 000 salariés et plus', 'min': 10000, 'max': None},
]


class SireneClient:
    """
    INSEE Sirene API client for French company data.

    Features:
    - Company search with filters
    - Company lookup by SIREN
    - Establishment (SIRET) listing
    """

    BASE_URL = "https://api.insee.fr/api-sirene/3.11"
    TOKEN_URL = "https://auth.insee.net/auth/realms/apim-gravitee/protocol/openid-connect/token"

    def __init__(self, api_key: str = None, secret: str = None):
        """
        Initialize Sirene client.

        Args:
            api_key: API key from new portal (preferred)
            secret: Legacy OAuth credentials (base64 of client_id:client_secret)
        """
        self.api_key = api_key or get_secret("SIRENE_API_KEY")
        self.secret = secret or get_secret("SIRENE_SECRET")
        self._token = None
        self._token_expiry = None

    def _get_headers(self) -> dict:
        """Get authorization headers."""
        headers = {"Accept": "application/json"}

        if self.api_key:
            headers["X-INSEE-Api-Key-Integration"] = self.api_key
            return headers

        headers["Authorization"] = f"Bearer {self._get_token()}"
        return headers

    def _get_token(self) -> str:
        """Get valid OAuth2 token (legacy)."""
        if self._token and self._token_expiry and datetime.now() < self._token_expiry:
            return self._token

        if not self.secret:
            raise ValueError(
                "SIRENE_API_KEY or SIRENE_SECRET not set. "
                "Get API key from https://portail-api.insee.fr/"
            )

        try:
            decoded = base64.b64decode(self.secret).decode("ascii")
            client_id, client_secret = decoded.split(":", 1)
        except Exception as e:
            raise ValueError(f"Invalid SIRENE_SECRET format: {e}")

        resp = requests.post(
            self.TOKEN_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            }
        )

        if not resp.ok:
            raise Exception(f"Token error: {resp.status_code} {resp.text}")

        data = resp.json()
        self._token = data["access_token"]
        self._token_expiry = datetime.now() + timedelta(seconds=data["expires_in"] - 60)
        return self._token

    def _build_query(self, params: Dict[str, Any]) -> str:
        """Build Sirene search query string."""
        conditions = []

        if params.get("active_only", True):
            conditions.append("periode(etatAdministratifUniteLegale:A)")

        naf_codes = params.get("naf_codes", [])
        if naf_codes:
            naf_q = []
            for code in naf_codes:
                if len(code) == 2 and code.isdigit():
                    naf_q.append(f"periode(activitePrincipaleUniteLegale:{code}.*)")
                else:
                    naf_q.append(f"periode(activitePrincipaleUniteLegale:{code})")
            conditions.append(f"({' OR '.join(naf_q)})")

        emp_ranges = params.get("employee_ranges")
        if emp_ranges:
            emp_q = " OR ".join([f"trancheEffectifsUniteLegale:{r}" for r in emp_ranges])
            conditions.append(f"({emp_q})")

        legal_cats = params.get("legal_categories", [])
        if legal_cats:
            cat_q = " OR ".join([f"periode(categorieJuridiqueUniteLegale:{c})" for c in legal_cats])
            conditions.append(f"({cat_q})")

        date_min = params.get("created_after")
        date_max = params.get("created_before")
        if date_min or date_max:
            if date_min and date_max:
                conditions.append(f"dateCreationUniteLegale:[{date_min} TO {date_max}]")
            elif date_min:
                conditions.append(f"dateCreationUniteLegale:[{date_min} TO *]")
            elif date_max:
                conditions.append(f"dateCreationUniteLegale:[* TO {date_max}]")

        return " AND ".join(conditions)

    def search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search companies.

        Args:
            params: Search parameters
                - naf_codes: list of NAF codes (e.g. ['62.01Z', '62'])
                - employee_ranges: list of range codes (e.g. ['11', '12'])
                - legal_categories: list of legal category codes
                - created_after: YYYY-MM-DD
                - created_before: YYYY-MM-DD
                - active_only: bool (default True)
                - limit: max results (default 20)
                - offset: pagination offset

        Returns:
            API response with unitesLegales array
        """
        query_params = {}
        query = self._build_query(params)
        if query:
            query_params["q"] = query

        query_params["nombre"] = params.get("limit", 20)
        if params.get("offset"):
            query_params["debut"] = params["offset"]

        query_params["champs"] = ",".join([
            "siren", "denominationUniteLegale", "sigleUniteLegale",
            "dateCreationUniteLegale", "trancheEffectifsUniteLegale",
            "categorieJuridiqueUniteLegale", "activitePrincipaleUniteLegale",
            "etatAdministratifUniteLegale", "nicSiegeUniteLegale",
            "nomUniteLegale", "prenom1UniteLegale", "categorieEntreprise"
        ])

        resp = requests.get(
            f"{self.BASE_URL}/siren",
            params=query_params,
            headers=self._get_headers()
        )

        if not resp.ok:
            raise Exception(f"API error: {resp.status_code} {resp.text}")

        return resp.json()

    def get_by_siren(self, siren: str) -> Dict[str, Any]:
        """
        Get company details by SIREN number.

        Args:
            siren: 9-digit SIREN number

        Returns:
            Company data
        """
        resp = requests.get(
            f"{self.BASE_URL}/siren/{siren}",
            headers=self._get_headers()
        )

        if not resp.ok:
            raise Exception(f"API error: {resp.status_code} {resp.text}")

        return resp.json().get("uniteLegale", {})

    def get_establishments(self, siren: str) -> List[Dict[str, Any]]:
        """
        Get all establishments (SIRET) for a company.

        Args:
            siren: Company SIREN number

        Returns:
            List of establishments
        """
        resp = requests.get(
            f"{self.BASE_URL}/siret",
            params={"q": f"siren:{siren}", "nombre": 1000},
            headers=self._get_headers()
        )

        if not resp.ok:
            raise Exception(f"API error: {resp.status_code} {resp.text}")

        return resp.json().get("etablissements", [])
