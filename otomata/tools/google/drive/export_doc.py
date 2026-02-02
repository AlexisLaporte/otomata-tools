#!/usr/bin/env python3
"""Export a Google Doc to text or markdown."""

import json
import sys
from pathlib import Path
import typer
from typing_extensions import Annotated

sys.path.insert(0, str(Path(__file__).parent))

from lib.drive_client import DriveClient, DriveClientError

app = typer.Typer(help="Export a Google Doc to text or other format")


def load_credentials_path() -> str:
    """Load Google service account credentials path from local .keys directory."""
    credentials_path = Path(__file__).parent / '.keys' / 'gdrive-key.json'
    if not credentials_path.exists():
        raise FileNotFoundError(f"Credentials file not found at {credentials_path}")
    return str(credentials_path)


@app.command()
def main(
    file_id: Annotated[str, typer.Option(help="Google Drive file ID")],
    output: Annotated[str, typer.Option(help="Local path to save exported file")],
    format: Annotated[str, typer.Option(help="Export format")] = "txt",
):
    """Export Google Doc to text."""
    if format not in ['txt', 'pdf', 'docx', 'html']:
        print(f"Error: Invalid format '{format}'. Choose from: txt, pdf, docx, html", file=sys.stderr)
        raise typer.Exit(1)

    mime_types = {
        'txt': 'text/plain',
        'pdf': 'application/pdf',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'html': 'text/html'
    }

    try:
        creds_path = load_credentials_path()
        client = DriveClient(creds_path)

        print(f"Exporting file {file_id} as {format}...", file=sys.stderr)
        result = client.export_file(file_id, output, mime_types[format])

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
