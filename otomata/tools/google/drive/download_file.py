#!/usr/bin/env python3
"""Download a file from Google Drive."""

import json
import sys
from pathlib import Path
import typer
from typing_extensions import Annotated

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from lib.drive_client import DriveClient, DriveClientError

app = typer.Typer(help="Download a file from Google Drive")


def load_credentials_path() -> str:
    """Load Google service account credentials path from local .keys directory."""
    credentials_path = Path(__file__).parent / '.keys' / 'gdrive-key.json'

    if not credentials_path.exists():
        raise FileNotFoundError(f"Credentials file not found at {credentials_path}")

    return str(credentials_path)


@app.command()
def main(
    file_id: Annotated[str, typer.Option(help="Google Drive file ID")],
    output: Annotated[str, typer.Option(help="Local path to save file")],
):
    """Download file from Google Drive."""
    try:
        # Load credentials
        creds_path = load_credentials_path()

        # Initialize client
        client = DriveClient(creds_path)

        # Download file
        print(f"Downloading file {file_id}...", file=sys.stderr)
        result = client.download_file(file_id, output)

        print(json.dumps(result, indent=2))

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Please set up Google Drive credentials in tools/google-drive/.keys/gdrive-key.json", file=sys.stderr)
        raise typer.Exit(1)
    except DriveClientError as e:
        print(f"Drive API Error: {e}", file=sys.stderr)
        raise typer.Exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
