#!/usr/bin/env python3
"""
Create new Notion page.

Usage:
    python3 create_page.py --parent_id db123 --title "New Task" --parent_type database
    python3 create_page.py --parent_id page456 --title "Sub-page" --parent_type page
"""
import json
import sys
from pathlib import Path
from typing_extensions import Annotated
import typer

sys.path.insert(0, str(Path(__file__).parent / 'lib'))
from notion_client import NotionClient

app = typer.Typer(help="Create Notion page")


@app.command()
def main(
    parent_id: Annotated[str, typer.Option(help="Parent database or page ID")],
    title: Annotated[str, typer.Option(help="Page title")],
    parent_type: Annotated[str, typer.Option(help="Parent type")] = "database",
    output: Annotated[str, typer.Option(help="Output file path (JSON)")] = None,
):
    if parent_type not in ['database', 'page']:
        print("❌ Error: parent_type must be 'database' or 'page'", file=sys.stderr)
        raise typer.Exit(1)

    try:
        client = NotionClient()
        parent_id = parent_id.replace('-', '')

        print(f"📝 Creating page in {parent_type}: {parent_id}...")
        print(f"   Title: {title}")

        result = client.create_page(
            parent_id=parent_id,
            parent_type=parent_type,
            title=title
        )

        print(f"\n✓ Page created successfully")
        print(f"   ID: {result['id']}")
        print(f"   URL: {result.get('url', 'N/A')}")

        # Save output
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Page saved to: {output}")

        # Return as JSON
        print("\n" + "="*60)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        raise typer.Exit(1)


if __name__ == '__main__':
    app()
