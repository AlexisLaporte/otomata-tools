#!/usr/bin/env python3
"""
Extract content from Google Slides using Slides API
"""
import sys
import os
import json
import typer
from typing_extensions import Annotated
from typing import Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = typer.Typer(help="Extract Google Slides content")


def extract_slides(file_id: str):
    """Extract slides content from Google Slides"""

    # Get credentials
    creds_path = os.environ.get('GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON')
    if not creds_path:
        creds_path = os.path.join(os.path.dirname(__file__), '.keys', 'gdrive-key.json')

    if not os.path.exists(creds_path):
        return {"status": "error", "error": f"Credentials not found at {creds_path}"}

    try:
        # Load credentials
        credentials = service_account.Credentials.from_service_account_file(
            creds_path,
            scopes=[
                'https://www.googleapis.com/auth/presentations.readonly',
                'https://www.googleapis.com/auth/drive.readonly'
            ]
        )

        # Build Slides API service
        slides_service = build('slides', 'v1', credentials=credentials)

        # Get presentation
        presentation = slides_service.presentations().get(
            presentationId=file_id
        ).execute()

        # Extract basic info
        result = {
            "status": "success",
            "presentation": {
                "id": presentation.get('presentationId'),
                "title": presentation.get('title'),
                "slides_count": len(presentation.get('slides', []))
            },
            "slides": []
        }

        # Extract each slide
        for slide in presentation.get('slides', []):
            slide_data = {
                "id": slide.get('objectId'),
                "title": "",
                "content": []
            }

            # Extract page elements (text boxes, shapes, etc.)
            for element in slide.get('pageElements', []):
                if 'shape' in element:
                    shape = element['shape']
                    if 'text' in shape:
                        text_content = ""
                        for text_element in shape['text'].get('textElements', []):
                            if 'textRun' in text_element:
                                text_content += text_element['textRun'].get('content', '')

                        if text_content.strip():
                            # First non-empty text is likely the title
                            if not slide_data['title']:
                                slide_data['title'] = text_content.strip()
                            else:
                                slide_data['content'].append(text_content.strip())

            result['slides'].append(slide_data)

        return result

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.command()
def main(
    file_id: Annotated[str, typer.Option(help="Google Slides file ID")],
    output: Annotated[Optional[str], typer.Option(help="Output JSON file path (optional)")] = None,
):
    """Extract Google Slides content."""
    result = extract_slides(file_id)

    if output:
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Content extracted to {output}")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))

    if result['status'] != 'success':
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
