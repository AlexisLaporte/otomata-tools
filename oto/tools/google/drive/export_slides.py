#!/usr/bin/env python3
"""
Export Google Slides to PDF format
"""
import sys
import os
import json
import typer
from typing_extensions import Annotated
from pathlib import Path

# Add lib to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

from drive_client import DriveClient, DriveClientError
from googleapiclient.http import MediaIoBaseDownload

app = typer.Typer(help="Export Google Slides")


def export_slides(file_id: str, output_path: str, format: str = 'pdf'):
    """Export Google Slides to specified format"""

    # Get credentials path from environment
    creds_path = os.environ.get('GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON')
    if not creds_path:
        creds_path = os.path.join(os.path.dirname(__file__), '.keys', 'gdrive-key.json')

    if not os.path.exists(creds_path):
        return {
            "status": "error",
            "error": f"Credentials file not found at {creds_path}"
        }

    try:
        client = DriveClient(creds_path)

        # MIME types for export
        mime_types = {
            'pdf': 'application/pdf',
            'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'txt': 'text/plain'
        }

        mime_type = mime_types.get(format, mime_types['pdf'])

        # Export the file
        print(f"Exporting Google Slides {file_id} as {format}...", file=sys.stderr)
        request = client.service.files().export_media(fileId=file_id, mimeType=mime_type)

        with open(output_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    print(f"Download {int(status.progress() * 100)}%", file=sys.stderr)

        file_size = os.path.getsize(output_path)

        return {
            "status": "success",
            "file_id": file_id,
            "output_path": output_path,
            "format": format,
            "size": str(file_size)
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.command()
def main(
    file_id: Annotated[str, typer.Option(help="Google Drive file ID")],
    output: Annotated[str, typer.Option(help="Output file path")],
    format: Annotated[str, typer.Option(help="Export format")] = 'pdf',
):
    """Export Google Slides."""
    if format not in ['pdf', 'pptx', 'txt']:
        print(f"Error: Invalid format '{format}'. Choose from: pdf, pptx, txt", file=sys.stderr)
        raise typer.Exit(1)

    result = export_slides(file_id, output, format)
    print(json.dumps(result, indent=2))

    if result['status'] != 'success':
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
