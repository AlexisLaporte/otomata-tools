"""Configuration loader for otomata tools.

Secret resolution order:
1. Environment variable
2. Project secrets: .otomata/secrets.env in CWD or parent directories
3. User secrets: ~/.otomata/secrets.env
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any

# Cache for parsed secrets files
_secrets_cache: Dict[Path, Dict[str, str]] = {}


def _parse_env_file(path: Path) -> Dict[str, str]:
    """Parse a .env file into a dictionary."""
    if path in _secrets_cache:
        return _secrets_cache[path]

    result = {}
    if path.exists():
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    value = value.strip()
                    # Remove quotes if present
                    if (value.startswith("'") and value.endswith("'")) or (
                        value.startswith('"') and value.endswith('"')
                    ):
                        value = value[1:-1]
                    result[key.strip()] = value

    _secrets_cache[path] = result
    return result


def _find_project_secrets() -> Optional[Path]:
    """Find .otomata/secrets.env in CWD or parent directories."""
    cwd = Path.cwd()

    # Check CWD and up to 4 parent levels
    for _ in range(5):
        secrets_file = cwd / ".otomata" / "secrets.env"
        if secrets_file.exists():
            return secrets_file
        if cwd.parent == cwd:
            break
        cwd = cwd.parent

    return None


def _get_user_secrets() -> Path:
    """Get user secrets file path (~/.otomata/secrets.env)."""
    return Path.home() / ".otomata" / "secrets.env"


def get_secret(name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get a secret value from config files (CLI mode).

    Search order:
    1. Project secrets: .otomata/secrets.env in CWD or parents
    2. User secrets: ~/.otomata/secrets.env
    3. Default value

    Note: For library usage, pass secrets explicitly via constructor
    (e.g., SireneClient(api_key='...')). This function is for CLI mode only.

    Args:
        name: Secret name (e.g., 'GROQ_API_KEY', 'SIRENE_API_KEY')
        default: Default value if not found

    Returns:
        Secret value or default
    """
    # 1. Project secrets
    project_secrets = _find_project_secrets()
    if project_secrets:
        secrets = _parse_env_file(project_secrets)
        if name in secrets:
            return secrets[name]

    # 2. User secrets
    user_secrets = _get_user_secrets()
    secrets = _parse_env_file(user_secrets)
    if name in secrets:
        return secrets[name]

    return default


def get_json_secret(name: str) -> Optional[Dict[str, Any]]:
    """
    Get a secret that contains JSON data.

    Args:
        name: Secret name

    Returns:
        Parsed JSON as dictionary, or None if not found
    """
    value = get_secret(name)
    if value:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None
    return None


def require_secret(name: str) -> str:
    """
    Get a required secret, raise error if not found.

    Args:
        name: Secret name

    Returns:
        Secret value

    Raises:
        ValueError: If secret not found
    """
    value = get_secret(name)
    if value is None:
        raise ValueError(
            f"Required secret '{name}' not found. Set it via:\n"
            f"  - Environment variable: export {name}='...'\n"
            f"  - Project file: .otomata/secrets.env\n"
            f"  - User file: ~/.otomata/secrets.env"
        )
    return value


def get_config_dir() -> Path:
    """Get otomata config directory (~/.otomata/)."""
    config_dir = Path.home() / ".otomata"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_cache_dir() -> Path:
    """Get otomata cache directory (~/.cache/otomata/)."""
    cache_dir = Path.home() / ".cache" / "otomata"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_sessions_dir() -> Path:
    """Get browser sessions directory (~/.otomata/sessions/)."""
    sessions_dir = get_config_dir() / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    return sessions_dir


# Legacy compatibility
def find_env_file() -> Optional[Path]:
    """Legacy: find secrets file."""
    return _find_project_secrets() or _get_user_secrets()
