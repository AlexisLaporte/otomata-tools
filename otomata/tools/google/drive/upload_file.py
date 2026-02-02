#!/usr/bin/env python3
"""Upload a file to Google Drive."""

import json
import sys
from pathlib import Path
import typer
from typing_extensions import Annotated
from typing import Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from lib.drive_client import DriveClient, DriveClientError

app = typer.Typer(help="Upload a file to Google Drive")

# Available folders
FOLDERS = {
    'business': '1lDh4H0cJKECdTv2y_zRbgifqjbDOvqbx',
    'teams': '1BHRuOqJizuFskRW7hg_dYc3J8kMI5Epf',
    'startups': '1xvwoHzk9Po7Ns9XUx-WyvMCTykRVbTuk'
}


def load_credentials_path() -> str:
    """Load Google service account credentials path from local .keys directory."""
    credentials_path = Path(__file__).parent / '.keys' / 'gdrive-key.json'

    if not credentials_path.exists():
        raise FileNotFoundError(f"Credentials file not found at {credentials_path}")

    return str(credentials_path)


@app.command()
def main(
    file: Annotated[str, typer.Option(help="Local file path to upload")],
    folder: Annotated[Optional[str], typer.Option(help="Target folder name: business, teams, or startups")] = None,
    folder_id: Annotated[Optional[str], typer.Option(help="Target folder ID (overrides --folder)")] = None,
    name: Annotated[Optional[str], typer.Option(help="Custom name for uploaded file")] = None,
    convert_to_sheets: Annotated[bool, typer.Option(help="Convert CSV to Google Sheets format")] = False,
):
    """Upload file to Google Drive."""
    try:
        # Verify file exists
        if not Path(file).exists():
            raise FileNotFoundError(f"Local file not found: {file}")

        # Validate folder choice
        if folder and folder not in FOLDERS:
            print(f"Error: Invalid folder '{folder}'. Choose from: {', '.join(FOLDERS.keys())}", file=sys.stderr)
            raise typer.Exit(1)

        # Resolve folder ID
        target_folder_id = folder_id
        if folder and not target_folder_id:
            target_folder_id = FOLDERS[folder]
            print(f"Using folder '{folder}': {target_folder_id}", file=sys.stderr)

        # Load credentials
        creds_path = load_credentials_path()

        # Initialize client
        client = DriveClient(creds_path)

        # Upload file
        print(f"Uploading {file}...", file=sys.stderr)
        result = client.upload_file(
            local_path=file,
            folder_id=target_folder_id,
            file_name=name,
            convert_to_sheets=convert_to_sheets
        )

        print(json.dumps(result, indent=2))

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(1)
    except DriveClientError as e:
        print(f"Drive API Error: {e}", file=sys.stderr)
        raise typer.Exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
