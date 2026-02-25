"""Google credentials loader - uses otomata config system.

Supports multiple OAuth accounts via named token files:
- google-oauth-token.json        → account "default"
- google-oauth-token-{name}.json → account "{name}"

If only one account exists, it's used automatically.
If multiple exist, --account is required.
"""

import json
import re
from typing import Optional, List
from pathlib import Path

from google.oauth2.service_account import Credentials
from google.oauth2.credentials import Credentials as UserCredentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

from otomata.config import get_json_secret, get_config_dir, get_secret, require_secret


DEFAULT_SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/presentations',
]

OAUTH_CLIENT_FILE = 'google-oauth-client.json'
OAUTH_TOKEN_FILE = 'google-oauth-token.json'
OAUTH_TOKEN_PREFIX = 'google-oauth-token'


def _token_path_for_account(config_dir: Path, account: str) -> Path:
    """Get token file path for a named account."""
    if account == 'default':
        return config_dir / OAUTH_TOKEN_FILE
    return config_dir / f'{OAUTH_TOKEN_PREFIX}-{account}.json'


def list_accounts() -> list[str]:
    """List configured OAuth account names."""
    config_dir = get_config_dir()
    accounts = []
    for f in sorted(config_dir.glob(f'{OAUTH_TOKEN_PREFIX}*.json')):
        m = re.match(rf'^{re.escape(OAUTH_TOKEN_PREFIX)}(?:-(.+))?\.json$', f.name)
        if m:
            accounts.append(m.group(1) or 'default')
    return accounts


def _resolve_account(account: Optional[str]) -> tuple[Path, str]:
    """Resolve account name to token path.

    Returns (token_path, account_name).
    Raises ValueError if ambiguous (multiple accounts, none specified).
    """
    config_dir = get_config_dir()

    if account:
        return _token_path_for_account(config_dir, account), account

    accounts = list_accounts()
    if len(accounts) == 1:
        return _token_path_for_account(config_dir, accounts[0]), accounts[0]
    if len(accounts) > 1:
        names = ', '.join(accounts)
        raise ValueError(
            f"Multiple Google accounts configured: {names}\n"
            f"Use --account <name> to select one."
        )
    # No accounts yet → will trigger OAuth flow with "default" name
    return config_dir / OAUTH_TOKEN_FILE, 'default'


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


def get_user_credentials(
    scopes: List[str],
    account: Optional[str] = None,
) -> UserCredentials:
    """
    Get OAuth2 user credentials (for APIs requiring user consent like Gmail).

    Args:
        scopes: OAuth scopes required
        account: Account name (None = auto-detect if single account)

    Returns:
        google.oauth2.credentials.Credentials with valid access token
    """
    token_path, _ = _resolve_account(account)
    creds = None

    if token_path.exists():
        creds = UserCredentials.from_authorized_user_file(str(token_path), scopes)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds or not creds.valid:
        config_dir = get_config_dir()
        client_config = _load_oauth_client_config(config_dir)
        flow = InstalledAppFlow.from_client_config(client_config, scopes)
        creds = flow.run_local_server(port=0)

    _save_token(token_path, creds, scopes)
    return creds


def setup_account(name: str, scopes: List[str]) -> UserCredentials:
    """Run OAuth flow for a named account (always opens browser)."""
    config_dir = get_config_dir()
    token_path = _token_path_for_account(config_dir, name)

    client_config = _load_oauth_client_config(config_dir)
    flow = InstalledAppFlow.from_client_config(client_config, scopes)
    creds = flow.run_local_server(port=0)

    _save_token(token_path, creds, scopes)
    return creds


def _save_token(token_path: Path, creds: UserCredentials, scopes: List[str]):
    """Save OAuth token to file."""
    token_path.write_text(json.dumps({
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': list(creds.scopes or scopes),
    }))


def _load_oauth_client_config(config_dir: Path) -> dict:
    """Load OAuth client config from file or secret."""
    client_file = config_dir / OAUTH_CLIENT_FILE
    if client_file.exists():
        return json.loads(client_file.read_text())

    client_json = get_secret('GOOGLE_OAUTH_CLIENT')
    if client_json:
        return json.loads(client_json)

    raise ValueError(
        f"OAuth client config not found. Either:\n"
        f"  - Place client JSON at {client_file}\n"
        f"  - Set GOOGLE_OAUTH_CLIENT in secrets.env"
    )
