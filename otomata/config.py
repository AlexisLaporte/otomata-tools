"""Configuration loader - finds secrets in calling project's CWD."""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any


def find_env_file() -> Optional[Path]:
    """Find .env.local in CWD or parent directories."""
    cwd = Path.cwd()

    # Check CWD and up to 3 parent levels
    for _ in range(4):
        env_file = cwd / '.env.local'
        if env_file.exists():
            return env_file
        cwd = cwd.parent

    return None


def parse_env_file(path: Path) -> Dict[str, str]:
    """Parse a .env file into a dictionary."""
    result = {}
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                # Remove quotes if present
                value = value.strip()
                if (value.startswith("'") and value.endswith("'")) or \
                   (value.startswith('"') and value.endswith('"')):
                    value = value[1:-1]
                result[key.strip()] = value
    return result


def get_secret(name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get a secret value. Search order:
    1. Environment variable
    2. .env.local in CWD (or parent dirs)
    3. User config (~/.config/otomata/)
    4. Default value

    Args:
        name: Secret name (e.g., 'GOOGLE_SERVICE_ACCOUNT', 'NOTION_API_KEY')
        default: Default value if not found

    Returns:
        Secret value or default
    """
    # 1. Environment variable
    if value := os.environ.get(name):
        return value

    # 2. .env.local in CWD
    env_file = find_env_file()
    if env_file:
        env_vars = parse_env_file(env_file)
        if name in env_vars:
            return env_vars[name]

    # 3. User config
    user_config = Path.home() / '.config' / 'otomata' / name.lower()
    if user_config.exists():
        return user_config.read_text().strip()

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
            f"Required secret '{name}' not found. "
            f"Set it via:\n"
            f"  - Environment variable: export {name}='...'\n"
            f"  - Project file: .env.local with {name}=...\n"
            f"  - User config: ~/.config/otomata/{name.lower()}"
        )
    return value
