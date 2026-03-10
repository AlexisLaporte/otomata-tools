#!/usr/bin/env python3
"""Move a file to a different folder in Google Drive."""

import json
import sys
from pathlib import Path
import typer
from typing_extensions import Annotated

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from lib.drive_client import DriveClient, DriveClientError

app = typer.Typer(help="Move a file to a different folder in Google Drive")


def load_credentials_path() -> str:
    """Load Google service account credentials path from local .keys directory."""
    credentials_path = Path(__file__).parent / '.keys' / 'gdrive-key.json'

    if not credentials_path.exists():
        raise FileNotFoundError(f"Credentials file not found at {credentials_path}")

    return str(credentials_path)


@app.command()
def main(
    file_id: Annotated[str, typer.Option(help="Google Drive file ID to move")],
    destination_folder_id: Annotated[str, typer.Option(help="Destination folder ID")],
):
    """Move a file to a different folder in Google Drive."""
    try:
        # Load credentials path
        creds_path = load_credentials_path()
        # Initialize client
        client = DriveClient(creds_path)

        # Move file
        result = client.move_file(
            file_id=file_id,
            destination_folder_id=destination_folder_id
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
