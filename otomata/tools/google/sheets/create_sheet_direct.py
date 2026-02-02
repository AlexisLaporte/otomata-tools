#!/usr/bin/env python3
"""
Create Google Sheet directly via Sheets API (no file upload)

Usage:
    python create_sheet_direct.py --csv profiles.csv --title "My Sheet"
"""

import sys
import json
import csv
import typer
from typing_extensions import Annotated
from typing import Optional
from pathlib import Path

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

app = typer.Typer(help="Create Google Sheet directly from CSV")

# Default credentials path
DEFAULT_CREDS = Path(__file__).parent / ".keys" / "gdrive-key.json"

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]


def create_sheet_from_csv(csv_path: str, title: str, creds_path: str = None) -> dict:
    """
    Create Google Sheet directly and populate with CSV data

    Args:
        csv_path: Path to CSV file
        title: Title for the Google Sheet
        creds_path: Path to Google service account JSON

    Returns:
        dict with file info including web link
    """
    if creds_path is None:
        creds_path = DEFAULT_CREDS

    if not Path(creds_path).exists():
        raise FileNotFoundError(f"Credentials not found: {creds_path}")

    if not Path(csv_path).exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    # Load credentials
    print(f"Initializing Google Sheets API...")
    credentials = Credentials.from_service_account_file(
        str(creds_path),
        scopes=SCOPES
    )

    # Initialize services
    sheets_service = build('sheets', 'v4', credentials=credentials)
    drive_service = build('drive', 'v3', credentials=credentials)

    # Read CSV data
    print(f"Reading CSV: {csv_path}")
    data = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            data.append(row)

    print(f"Loaded {len(data)} rows (including header)")

    # Create empty spreadsheet
    print(f"Creating Google Sheet: {title}")
    spreadsheet = {
        'properties': {
            'title': title
        }
    }

    spreadsheet = sheets_service.spreadsheets().create(
        body=spreadsheet,
        fields='spreadsheetId,spreadsheetUrl'
    ).execute()

    spreadsheet_id = spreadsheet.get('spreadsheetId')
    spreadsheet_url = spreadsheet.get('spreadsheetUrl')

    print(f"✓ Sheet created: {spreadsheet_id}")

    # Write data to sheet
    print(f"Writing data to sheet...")
    body = {
        'values': data
    }

    sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range='A1',
        valueInputOption='RAW',
        body=body
    ).execute()

    print(f"✓ Data written: {len(data)} rows")

    # Set sharing to "Anyone with link can view"
    print(f"Setting sharing permissions...")
    permission = {
        'type': 'anyone',
        'role': 'reader'
    }

    drive_service.permissions().create(
        fileId=spreadsheet_id,
        body=permission
    ).execute()

    print(f"✓ Sharing enabled")

    return {
        'id': spreadsheet_id,
        'name': title,
        'webViewLink': spreadsheet_url
    }


@app.command()
def main(
    csv: Annotated[str, typer.Option(help="Path to CSV file")],
    title: Annotated[str, typer.Option(help="Title for Google Sheet")],
    creds: Annotated[Optional[str], typer.Option(help="Path to service account JSON")] = None,
    output: Annotated[Optional[str], typer.Option(help="Save result to JSON file")] = None,
):
    """Create Google Sheet directly from CSV."""
    try:
        result = create_sheet_from_csv(csv, title, creds)

        print(f"\nGoogle Sheet created successfully!")
        print(f"\nSheet ID: {result['id']}")
        print(f"Sheet Name: {result['name']}")
        print(f"\nShare URL:")
        print(f"{result['webViewLink']}")

        if output:
            with open(output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\nSaved details to: {output}")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
