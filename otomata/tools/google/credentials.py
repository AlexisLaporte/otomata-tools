"""Google credentials loader - uses otomata config system."""

from typing import Optional, List
from google.oauth2.service_account import Credentials

from otomata.config import get_json_secret, require_secret


DEFAULT_SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/presentations',
]


def get_credentials(scopes: Optional[List[str]] = None) -> Credentials:
    """
    Get Google service account credentials.

    Looks for GOOGLE_SERVICE_ACCOUNT in:
    1. Environment variable
    2. .env.local in CWD
    3. ~/.config/otomata/google_service_account

    Args:
        scopes: OAuth scopes (default: drive, docs, sheets, slides)

    Returns:
        google.oauth2.service_account.Credentials object

    Raises:
        ValueError: If credentials not found
    """
    if scopes is None:
        scopes = DEFAULT_SCOPES

    creds_json = get_json_secret('GOOGLE_SERVICE_ACCOUNT')
    if creds_json is None:
        require_secret('GOOGLE_SERVICE_ACCOUNT')  # Will raise with helpful error

    return Credentials.from_service_account_info(creds_json, scopes=scopes)
