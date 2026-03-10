#!/usr/bin/env python3
"""List files from Google Drive."""

import json
import sys
from pathlib import Path
import typer
from typing_extensions import Annotated
from typing import Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from lib.drive_client import DriveClient, DriveClientError

app = typer.Typer(help="List files from Google Drive")


def load_credentials_path() -> str:
    """Load Google service account credentials path from local .keys directory."""
    credentials_path = Path(__file__).parent / '.keys' / 'gdrive-key.json'

    if not credentials_path.exists():
        raise FileNotFoundError(f"Credentials file not found at {credentials_path}")

    return str(credentials_path)


@app.command()
def main(
    folder_id: Annotated[Optional[str], typer.Option(help="Filter by parent folder ID")] = None,
    query: Annotated[Optional[str], typer.Option(help="Custom query filter (e.g., \"name contains 'report'\")")] = None,
    page_size: Annotated[int, typer.Option(help="Max results per page")] = 100,
    fields: Annotated[str, typer.Option(help="Fields to retrieve")] = 'files(id,name,mimeType,modifiedTime,size,webViewLink)',
    format: Annotated[str, typer.Option(help="Output format")] = 'json',
):
    """List files from Google Drive."""
    if format not in ['json', 'table']:
        print(f"Error: Invalid format '{format}'. Choose from: json, table", file=sys.stderr)
        raise typer.Exit(1)

    try:
        # Load credentials
        creds_path = load_credentials_path()

        # Initialize client
        client = DriveClient(creds_path)

        # List files
        files = client.list_files(
            folder_id=folder_id,
            query=query,
            page_size=page_size,
            fields=fields
        )

        # Output results
        if format == 'json':
            result = {
                'status': 'success',
                'count': len(files),
                'files': files
            }
            print(json.dumps(result, indent=2))
        else:
            # Simple table format
            if not files:
                print("No files found")
                return

            print(f"Found {len(files)} files:\n")
            print(f"{'ID':<40} {'Name':<50} {'Size':<15} {'Modified':<20}")
            print("-" * 125)

            for f in files:
                size_str = f.get('size', 'N/A')
                if size_str and size_str.isdigit():
                    size_mb = int(size_str) / (1024 * 1024)
                    size_str = f"{size_mb:.2f} MB"

                modified = f.get('modifiedTime', 'N/A')[:10]
                print(f"{f['id']:<40} {f['name']:<50} {size_str:<15} {modified:<20}")

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
