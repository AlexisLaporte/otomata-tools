#!/usr/bin/env python3
"""
Google Docs Sync Tool

Synchronize markdown sections with a Google Doc.

Usage:
    python gdoc_sync.py init --doc-id XXX --source-dir /path/to/sections
    python gdoc_sync.py push --doc-id XXX --section 03-collaboration --source-dir /path
    python gdoc_sync.py pull --doc-id XXX --section 03-collaboration --output-dir /path
    python gdoc_sync.py status --doc-id XXX --source-dir /path
"""

import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

import typer
from typing_extensions import Annotated

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.docs_client import DocsClient

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

app = typer.Typer(help="Sync markdown sections with Google Docs")

SCOPES = ['https://www.googleapis.com/auth/documents']


@dataclass
class ParsedSection:
    """A parsed markdown section."""
    title: str
    level: int  # 1 = H1, 2 = H2, etc.
    content: List[Tuple[str, str]]  # (text, style) pairs


def load_credentials():
    """Load Google service account credentials."""
    creds_path = Path(__file__).parent.parent.parent / 'drive' / '.keys' / 'gdrive-key.json'
    if not creds_path.exists():
        raise FileNotFoundError(f"Credentials not found: {creds_path}")

    with open(creds_path, 'r') as f:
        creds_dict = json.load(f)

    return Credentials.from_service_account_info(creds_dict, scopes=SCOPES)


def parse_markdown(content: str) -> List[Tuple[str, str]]:
    """
    Parse markdown content into (text, style) pairs.

    Returns list of tuples: (text, style)
    where style is: HEADING_1, HEADING_2, HEADING_3, NORMAL_TEXT, BULLET_1, BULLET_2
    """
    lines = content.split('\n')
    result = []
    in_table = False

    for line in lines:
        # Skip empty lines but preserve them
        if not line.strip():
            result.append(('\n', 'NORMAL_TEXT'))
            continue

        # Headers
        if line.startswith('# '):
            result.append((line[2:].strip() + '\n', 'HEADING_1'))
        elif line.startswith('## '):
            result.append((line[3:].strip() + '\n', 'HEADING_2'))
        elif line.startswith('### '):
            result.append((line[4:].strip() + '\n', 'HEADING_3'))

        # Bullet points
        elif line.startswith('- ') or line.startswith('* '):
            result.append((line[2:].strip() + '\n', 'BULLET_1'))
        elif line.startswith('  - ') or line.startswith('  * '):
            result.append((line[4:].strip() + '\n', 'BULLET_2'))

        # Tables (convert to simple text for now)
        elif line.startswith('|'):
            if '---' in line:
                continue  # Skip separator
            cells = [c.strip() for c in line.split('|')[1:-1]]
            result.append((' | '.join(cells) + '\n', 'NORMAL_TEXT'))

        # Block quotes
        elif line.startswith('> '):
            result.append((line[2:].strip() + '\n', 'NORMAL_TEXT'))

        # Bold text markers (keep as is, Google Docs will handle)
        else:
            # Clean up markdown formatting
            text = line.strip()
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Remove bold markers
            text = re.sub(r'\*([^*]+)\*', r'\1', text)  # Remove italic markers
            result.append((text + '\n', 'NORMAL_TEXT'))

    return result


def insert_content_with_formatting(service, doc_id: str, start_index: int,
                                    content_parts: List[Tuple[str, str]]) -> int:
    """
    Insert content with proper Google Docs formatting.

    Returns the end index after insertion.
    """
    requests = []

    # First pass: insert all text
    full_text = ''.join([p[0] for p in content_parts])
    requests.append({
        'insertText': {
            'location': {'index': start_index},
            'text': full_text
        }
    })

    # Execute text insertion
    service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()

    # Second pass: apply styles
    requests = []
    current_index = start_index
    bullet_ranges = []  # Track bullet ranges for batch application

    for text, style in content_parts:
        end_index = current_index + len(text)

        if style in ('HEADING_1', 'HEADING_2', 'HEADING_3', 'NORMAL_TEXT'):
            requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': current_index, 'endIndex': end_index},
                    'paragraphStyle': {'namedStyleType': style},
                    'fields': 'namedStyleType'
                }
            })
        elif style == 'BULLET_1':
            bullet_ranges.append((current_index, end_index, 0))
        elif style == 'BULLET_2':
            bullet_ranges.append((current_index, end_index, 1))

        current_index = end_index

    # Apply paragraph styles
    if requests:
        service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()

    # Apply bullets in contiguous ranges
    if bullet_ranges:
        # Group contiguous bullet ranges
        bullet_groups = []
        current_group = None

        for start, end, level in bullet_ranges:
            if current_group is None:
                current_group = {'start': start, 'end': end, 'items': [(start, end, level)]}
            elif start == current_group['end']:
                current_group['end'] = end
                current_group['items'].append((start, end, level))
            else:
                bullet_groups.append(current_group)
                current_group = {'start': start, 'end': end, 'items': [(start, end, level)]}

        if current_group:
            bullet_groups.append(current_group)

        # Apply bullets to each group
        for group in bullet_groups:
            requests = [{
                'createParagraphBullets': {
                    'range': {'startIndex': group['start'], 'endIndex': group['end']},
                    'bulletPreset': 'BULLET_DISC_CIRCLE_SQUARE'
                }
            }]
            service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()

            # Apply indentation for nested bullets
            for start, end, level in group['items']:
                if level > 0:
                    indent_requests = [{
                        'updateParagraphStyle': {
                            'range': {'startIndex': start, 'endIndex': end},
                            'paragraphStyle': {
                                'indentStart': {'magnitude': 36 * level, 'unit': 'PT'},
                                'indentFirstLine': {'magnitude': 18 * level, 'unit': 'PT'}
                            },
                            'fields': 'indentStart,indentFirstLine'
                        }
                    }]
                    service.documents().batchUpdate(documentId=doc_id, body={'requests': indent_requests}).execute()

    return start_index + len(full_text)


@app.command()
def init(
    doc_id: Annotated[str, typer.Option(help="Google Doc ID")],
    source_dir: Annotated[str, typer.Option(help="Directory containing markdown sections")],
    clear: Annotated[bool, typer.Option(help="Clear existing content first")] = True,
):
    """Initialize a Google Doc from markdown source files."""
    credentials = load_credentials()
    service = build('docs', 'v1', credentials=credentials)

    source_path = Path(source_dir)
    if not source_path.exists():
        print(f"Error: Source directory not found: {source_dir}", file=sys.stderr)
        raise typer.Exit(1)

    # Find all section files
    section_files = sorted(source_path.glob('*.md'))
    if not section_files:
        print(f"Error: No markdown files found in {source_dir}", file=sys.stderr)
        raise typer.Exit(1)

    print(f"Found {len(section_files)} section files")

    # Clear document if requested
    if clear:
        doc = service.documents().get(documentId=doc_id).execute()
        content = doc.get('body', {}).get('content', [])
        if len(content) > 1:
            end_index = content[-1].get('endIndex', 1) - 1
            if end_index > 1:
                service.documents().batchUpdate(
                    documentId=doc_id,
                    body={'requests': [{'deleteContentRange': {'range': {'startIndex': 1, 'endIndex': end_index}}}]}
                ).execute()
                print("Document cleared")

    # Insert each section
    current_index = 1

    for section_file in section_files:
        print(f"Processing: {section_file.name}")
        content = section_file.read_text()
        parsed = parse_markdown(content)

        if parsed:
            current_index = insert_content_with_formatting(service, doc_id, current_index, parsed)
            # Add separator between sections
            service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': [{'insertText': {'location': {'index': current_index}, 'text': '\n'}}]}
            ).execute()
            current_index += 1

    print(f"\nDone! Document initialized with {len(section_files)} sections")
    print(f"URL: https://docs.google.com/document/d/{doc_id}/edit")


@app.command()
def push(
    doc_id: Annotated[str, typer.Option(help="Google Doc ID")],
    section: Annotated[str, typer.Option(help="Section name (e.g., '03-collaboration' or filename)")],
    source_dir: Annotated[str, typer.Option(help="Directory containing markdown sections")],
):
    """Push a markdown section to Google Doc (replaces existing section)."""
    credentials = load_credentials()
    service = build('docs', 'v1', credentials=credentials)
    client = DocsClient()

    source_path = Path(source_dir)

    # Find the section file
    section_file = None
    for f in source_path.glob('*.md'):
        if section in f.name:
            section_file = f
            break

    if not section_file:
        print(f"Error: Section file not found for '{section}'", file=sys.stderr)
        raise typer.Exit(1)

    print(f"Source: {section_file}")

    # Parse the markdown
    content = section_file.read_text()
    parsed = parse_markdown(content)

    # Find the section title (first H1 or H2)
    section_title = None
    for text, style in parsed:
        if style in ('HEADING_1', 'HEADING_2'):
            section_title = text.strip()
            break

    if not section_title:
        print("Error: Could not find section title in markdown", file=sys.stderr)
        raise typer.Exit(1)

    print(f"Section title: {section_title}")

    # Find the section in the Google Doc
    headings = client.list_headings(doc_id)

    target_heading = None
    next_heading = None

    for i, h in enumerate(headings):
        if section_title.lower() in h['text'].lower():
            target_heading = h
            # Find next heading at same or higher level
            for j in range(i + 1, len(headings)):
                next_h = headings[j]
                # Check if it's a major section (starts with number or is same level)
                if next_h['text'][0].isdigit() or next_h['style'] in ('HEADING_1', 'HEADING_2'):
                    next_heading = next_h
                    break
            break

    if not target_heading:
        print(f"Error: Section '{section_title}' not found in document", file=sys.stderr)
        print("Available sections:", file=sys.stderr)
        for h in headings:
            print(f"  - {h['text']}", file=sys.stderr)
        raise typer.Exit(1)

    # Calculate range to replace
    start_index = target_heading['start_index']
    end_index = next_heading['start_index'] if next_heading else None

    if end_index is None:
        # Get document end
        doc = service.documents().get(documentId=doc_id).execute()
        end_index = doc['body']['content'][-1]['endIndex'] - 1

    print(f"Replacing range: {start_index} to {end_index}")

    # Delete existing content
    service.documents().batchUpdate(
        documentId=doc_id,
        body={'requests': [{'deleteContentRange': {'range': {'startIndex': start_index, 'endIndex': end_index}}}]}
    ).execute()

    # Insert new content
    insert_content_with_formatting(service, doc_id, start_index, parsed)

    print(f"\nDone! Section '{section_title}' updated")
    print(f"URL: https://docs.google.com/document/d/{doc_id}/edit")


@app.command()
def pull(
    doc_id: Annotated[str, typer.Option(help="Google Doc ID")],
    section: Annotated[str, typer.Option(help="Section name to pull")],
    output_dir: Annotated[str, typer.Option(help="Output directory for markdown")],
):
    """Pull a section from Google Doc to markdown file."""
    client = DocsClient()

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Get section content
    section_data = client.get_section_content(doc_id, section)

    if not section_data:
        print(f"Error: Section '{section}' not found", file=sys.stderr)
        raise typer.Exit(1)

    # Convert to markdown (basic conversion)
    # Note: This is a simplified conversion - complex formatting may be lost
    content = section_data.content

    # Try to preserve some structure
    lines = content.split('\n')
    md_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            md_lines.append('')
        elif stripped.startswith('•') or stripped.startswith('●'):
            md_lines.append(f"- {stripped[1:].strip()}")
        elif stripped.startswith('○'):
            md_lines.append(f"  - {stripped[1:].strip()}")
        else:
            md_lines.append(stripped)

    md_content = '\n'.join(md_lines)

    # Determine output filename
    safe_name = re.sub(r'[^\w\s-]', '', section.lower())
    safe_name = re.sub(r'[\s]+', '-', safe_name)
    output_file = output_path / f"{safe_name}.md"

    output_file.write_text(md_content)
    print(f"Pulled section to: {output_file}")


@app.command()
def status(
    doc_id: Annotated[str, typer.Option(help="Google Doc ID")],
    source_dir: Annotated[str, typer.Option(help="Directory containing markdown sections")],
):
    """Show sync status between markdown sources and Google Doc."""
    client = DocsClient()

    source_path = Path(source_dir)
    section_files = sorted(source_path.glob('*.md'))

    print("Google Doc sections:")
    headings = client.list_headings(doc_id)
    for h in headings:
        if h['style'] in ('HEADING_1', 'TITLE') or h['text'][0].isdigit():
            print(f"  [{h['start_index']:5}] {h['text']}")

    print(f"\nLocal markdown files ({source_path}):")
    for f in section_files:
        print(f"  - {f.name}")

    print("\nNote: Detailed diff not yet implemented")


if __name__ == "__main__":
    app()
