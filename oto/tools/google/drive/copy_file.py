#!/usr/bin/env python3
"""Copy a file in Google Drive."""

import json
import sys
from pathlib import Path
import typer
from typing_extensions import Annotated
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))
from lib.drive_client import DriveClient, DriveClientError

app = typer.Typer(help="Copy a file in Google Drive")


def load_credentials_path() -> str:
    credentials_path = Path(__file__).parent / '.keys' / 'gdrive-key.json'
    if not credentials_path.exists():
        raise FileNotFoundError(f"Credentials file not found at {credentials_path}")
    return str(credentials_path)


@app.command()
def main(
    file_id: Annotated[str, typer.Option(help="Source file ID to copy")],
    name: Annotated[Optional[str], typer.Option(help="Name for the copy")] = None,
    folder_id: Annotated[Optional[str], typer.Option(help="Destination folder ID")] = None,
):
    """Copy a file in Google Drive."""
    try:
        creds_path = load_credentials_path()
        client = DriveClient(creds_path)

        # Get original file metadata
        original = client.service.files().get(
            fileId=file_id,
            fields='name,mimeType',
            supportsAllDrives=True
        ).execute()

        # Prepare copy metadata
        copy_metadata = {}
        if name:
            copy_metadata['name'] = name
        else:
            copy_metadata['name'] = f"Copy of {original['name']}"

        if folder_id:
            copy_metadata['parents'] = [folder_id]

        # Copy the file
        copied_file = client.service.files().copy(
            fileId=file_id,
            body=copy_metadata,
            fields='id,name,webViewLink,mimeType',
            supportsAllDrives=True
        ).execute()

        print(json.dumps({
            'status': 'success',
            'original_id': file_id,
            'original_name': original['name'],
            'copy_id': copied_file['id'],
            'copy_name': copied_file['name'],
            'web_link': copied_file.get('webViewLink'),
            'mime_type': copied_file['mimeType']
        }, indent=2))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
