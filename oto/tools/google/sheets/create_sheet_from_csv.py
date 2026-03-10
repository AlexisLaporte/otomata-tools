#!/usr/bin/env python3
"""
Create Google Sheet from CSV file

Usage:
    python create_sheet_from_csv.py --csv-file data.csv --sheet-name "My Sheet" [--folder-id ID] [--share]
"""

import sys
import csv
import json
import typer
from typing_extensions import Annotated
from typing import Optional
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

app = typer.Typer(help="Create Google Sheet from CSV file")

# Default credentials path
DEFAULT_CREDS = Path(__file__).parent / ".keys" / "gdrive-key.json"

# Default folder for sheets (same as slides)
DEFAULT_FOLDER_ID = "1lDh4H0cJKECdTv2y_zRbgifqjbDOvqbx"

# API scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]


def create_sheet_from_csv(csv_file: str, sheet_name: str, folder_id: str = None, share: bool = False, creds_path: str = None) -> dict:
    """
    Create a Google Sheet from CSV file

    Args:
        csv_file: Path to CSV file
        sheet_name: Name for the new sheet
        folder_id: Optional folder ID to place sheet in
        share: Make sheet publicly viewable (anyone with link)
        creds_path: Path to service account credentials

    Returns:
        dict with sheet info (id, name, url)
    """
    if creds_path is None:
        creds_path = DEFAULT_CREDS

    if not Path(creds_path).exists():
        raise FileNotFoundError(f"Credentials not found: {creds_path}")

    if not Path(csv_file).exists():
        raise FileNotFoundError(f"CSV file not found: {csv_file}")

    # Load credentials
    creds = service_account.Credentials.from_service_account_file(
        str(creds_path),
        scopes=SCOPES
    )

    # Build services
    sheets_service = build('sheets', 'v4', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    # Use default folder if not specified
    if folder_id is None:
        folder_id = DEFAULT_FOLDER_ID

    # Read CSV data
    data = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            data.append(row)

    print(f"Creating Google Sheet: {sheet_name}")
    print(f"Importing {len(data)} rows from CSV...")

    # Create spreadsheet in Drive folder
    file_metadata = {
        'name': sheet_name,
        'mimeType': 'application/vnd.google-apps.spreadsheet',
        'parents': [folder_id]
    }

    # Upload CSV and convert to Sheet
    media = MediaFileUpload(
        csv_file,
        mimetype='text/csv',
        resumable=True
    )

    file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id,name,webViewLink',
        supportsAllDrives=True
    ).execute()

    sheet_id = file['id']
    sheet_url = file['webViewLink']

    # Share if requested
    if share:
        print("Setting sharing permissions...")
        permission = {
            'type': 'anyone',
            'role': 'reader'
        }
        drive_service.permissions().create(
            fileId=sheet_id,
            body=permission,
            supportsAllDrives=True
        ).execute()

    return {
        'status': 'success',
        'file_id': sheet_id,
        'filename': sheet_name,
        'web_link': sheet_url,
        'rows_imported': len(data),
        'folder_id': folder_id
    }


@app.command()
def main(
    csv_file: Annotated[str, typer.Option(help="Path to CSV file")],
    sheet_name: Annotated[str, typer.Option(help="Name for Google Sheet")],
    folder_id: Annotated[Optional[str], typer.Option(help=f"Folder ID (default: {DEFAULT_FOLDER_ID})")] = None,
    share: Annotated[bool, typer.Option(help="Make sheet publicly viewable")] = False,
    creds: Annotated[Optional[str], typer.Option(help="Path to service account JSON")] = None,
):
    """Create Google Sheet from CSV file."""
    try:
        result = create_sheet_from_csv(
            csv_file,
            sheet_name,
            folder_id,
            share,
            creds
        )

        print(f"\nSheet created successfully!")
        print(f"ID: {result['file_id']}")
        print(f"Name: {result['filename']}")
        print(f"Rows: {result['rows_imported']}")
        print(f"\nView: {result['web_link']}")

        # Output JSON for programmatic use
        print(f"\n{json.dumps(result, indent=2)}")

    except Exception as e:
        error_result = {
            'status': 'error',
            'error': str(e)
        }
        print(f"\nError: {e}", file=sys.stderr)
        print(json.dumps(error_result))
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
