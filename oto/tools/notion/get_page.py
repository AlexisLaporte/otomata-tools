#!/usr/bin/env python3
"""
Get Notion page with full content.

Usage:
    python3 get_page.py --page_id abc123def456
    python3 get_page.py --page_id abc123 --no-content
    python3 get_page.py --page_id abc123 --output page.json
"""
import json
import sys
from pathlib import Path
from typing_extensions import Annotated
import typer

sys.path.insert(0, str(Path(__file__).parent / 'lib'))
from notion_client import NotionClient

app = typer.Typer(help="Get Notion page")


@app.command()
def main(
    page_id: Annotated[str, typer.Option(help="Page ID")],
    no_content: Annotated[bool, typer.Option(help="Skip page blocks (content)")] = False,
    recursive: Annotated[bool, typer.Option(help="Fetch children of blocks recursively")] = False,
    output: Annotated[str, typer.Option(help="Output file path (JSON)")] = None,
):
    try:
        client = NotionClient()
        page_id = page_id.replace('-', '')

        print(f"📄 Fetching page: {page_id}...")

        # Get page metadata
        page = client.get_page(page_id)

        # Get page content (blocks)
        if not no_content:
            print(f"   Fetching page content{' (recursive)' if recursive else ''}...")
            blocks = client.get_page_blocks(page_id, recursive=recursive)
            page['content'] = blocks

        # Display summary
        print(f"\n✓ Page retrieved successfully\n")

        # Extract title
        title_prop = page.get('properties', {}).get('title', {})
        title_array = title_prop.get('title', [])
        title = title_array[0]['plain_text'] if title_array else '(Untitled)'

        print(f"Title: {title}")
        print(f"ID: {page['id']}")
        print(f"Created: {page.get('created_time', 'N/A')}")
        print(f"Last edited: {page.get('last_edited_time', 'N/A')}")
        print(f"URL: {page.get('url', 'N/A')}")

        if not no_content and 'content' in page:
            num_blocks = len(page['content'].get('results', []))
            print(f"Blocks: {num_blocks}")

        # Save output if requested
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(page, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Page saved to: {output}")

        # Return as JSON
        print("\n" + "="*60)
        print(json.dumps(page, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        raise typer.Exit(1)


if __name__ == '__main__':
    app()
