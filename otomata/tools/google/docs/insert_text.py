#!/usr/bin/env python3
"""Insert text into a Google Doc."""

import json
import sys
from pathlib import Path
import typer
from typing_extensions import Annotated
from typing import Optional

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

app = typer.Typer(help="Insert text into a Google Doc")

SCOPES = ['https://www.googleapis.com/auth/documents']


def load_credentials():
    credentials_path = Path(__file__).parent.parent / 'drive' / '.keys' / 'gdrive-key.json'
    if not credentials_path.exists():
        raise FileNotFoundError(f"Credentials file not found at {credentials_path}")

    with open(credentials_path, 'r') as f:
        creds_dict = json.load(f)

    return Credentials.from_service_account_info(creds_dict, scopes=SCOPES)


@app.command()
def main(
    doc_id: Annotated[str, typer.Option(help="Google Doc ID")],
    text: Annotated[Optional[str], typer.Option(help="Text to insert")] = None,
    file: Annotated[Optional[str], typer.Option(help="File containing text to insert")] = None,
    index: Annotated[int, typer.Option(help="Position to insert (1 = start of doc)")] = 1,
    heading: Annotated[Optional[str], typer.Option(help="Add as heading (1, 2, or 3)")] = None,
):
    """Insert text into a Google Doc at specified position."""
    try:
        if not text and not file:
            print("Error: Either --text or --file is required", file=sys.stderr)
            raise typer.Exit(1)

        if file:
            with open(file, 'r') as f:
                text = f.read()

        credentials = load_credentials()
        service = build('docs', 'v1', credentials=credentials)

        # Build requests
        requests = []

        # Insert text
        requests.append({
            'insertText': {
                'location': {'index': index},
                'text': text + '\n'
            }
        })

        # Apply heading style if requested
        if heading:
            heading_map = {'1': 'HEADING_1', '2': 'HEADING_2', '3': 'HEADING_3'}
            if heading in heading_map:
                requests.append({
                    'updateParagraphStyle': {
                        'range': {
                            'startIndex': index,
                            'endIndex': index + len(text) + 1
                        },
                        'paragraphStyle': {
                            'namedStyleType': heading_map[heading]
                        },
                        'fields': 'namedStyleType'
                    }
                })

        # Execute batch update
        result = service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests}
        ).execute()

        print(json.dumps({
            'status': 'success',
            'doc_id': doc_id,
            'inserted_length': len(text),
            'at_index': index,
            'replies': len(result.get('replies', []))
        }, indent=2))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
