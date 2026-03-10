#!/usr/bin/env python3
"""Create a folder in Google Drive."""

import json
import sys
from pathlib import Path
import typer
from typing_extensions import Annotated
from typing import Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from lib.drive_client import DriveClient, DriveClientError

app = typer.Typer(help="Create a folder in Google Drive")


def load_credentials_path() -> str:
    """Load Google service account credentials path from local .keys directory."""
    credentials_path = Path(__file__).parent / '.keys' / 'gdrive-key.json'

    if not credentials_path.exists():
        raise FileNotFoundError(f"Credentials file not found at {credentials_path}")

    return str(credentials_path)


@app.command()
def main(
    name: Annotated[str, typer.Option(help="Folder name")],
    parent_folder_id: Annotated[Optional[str], typer.Option(help="Parent folder ID (optional, uses root if not specified)")] = None,
):
    """Create a folder in Google Drive."""
    try:
        # Load credentials path
        creds_path = load_credentials_path()
        # Initialize client
        client = DriveClient(creds_path)

        # Create folder
        result = client.create_folder(
            folder_name=name,
            parent_folder_id=parent_folder_id
        )

        print(json.dumps(result, indent=2))

    except (DriveClientError, FileNotFoundError, ValueError) as e:
        print(json.dumps({
            'status': 'error',
            'error': str(e)
        }))
        raise typer.Exit(1)


if __name__ == '__main__':
    app()
