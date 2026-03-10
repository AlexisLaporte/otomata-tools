#!/usr/bin/env python3
"""
Update Notion page properties.

Usage:
    python3 update_page.py --page_id abc123 --archive
    python3 update_page.py --page_id abc123 --unarchive
"""
import json
import sys
from pathlib import Path
from typing_extensions import Annotated
import typer

sys.path.insert(0, str(Path(__file__).parent / 'lib'))
from notion_client import NotionClient

app = typer.Typer(help="Update Notion page")


@app.command()
def main(
    page_id: Annotated[str, typer.Option(help="Page ID to update")],
    archive: Annotated[bool, typer.Option(help="Archive the page")] = False,
    unarchive: Annotated[bool, typer.Option(help="Unarchive the page")] = False,
    output: Annotated[str, typer.Option(help="Output file path (JSON)")] = None,
):
    try:
        client = NotionClient()
        page_id = page_id.replace('-', '')

        archived = None
        if archive:
            archived = True
        elif unarchive:
            archived = False

        print(f"✏️  Updating page: {page_id}...")

        result = client.update_page(
            page_id=page_id,
            archived=archived
        )

        print(f"\n✓ Page updated successfully")
        print(f"   ID: {result['id']}")
        print(f"   Archived: {result.get('archived', False)}")

        # Save output
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Result saved to: {output}")

        # Return as JSON
        print("\n" + "="*60)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        raise typer.Exit(1)


if __name__ == '__main__':
    app()
