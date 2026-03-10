#!/usr/bin/env python3
"""
Get Notion database metadata and schema.

Usage:
    python3 get_database.py --database_id abc123
"""
import json
import sys
from pathlib import Path
from typing_extensions import Annotated
import typer

sys.path.insert(0, str(Path(__file__).parent / 'lib'))
from notion_client import NotionClient

app = typer.Typer(help="Get Notion database")


@app.command()
def main(
    database_id: Annotated[str, typer.Option(help="Database ID")],
    output: Annotated[str, typer.Option(help="Output file path (JSON)")] = None,
):
    try:
        client = NotionClient()
        db_id = database_id.replace('-', '')

        print(f"🗂️  Fetching database: {db_id}...")

        result = client.get_database(db_id)

        # Display summary
        title_array = result.get('title', [])
        title = title_array[0]['plain_text'] if title_array else '(Untitled)'

        print(f"\n✓ Database retrieved successfully\n")
        print(f"Title: {title}")
        print(f"ID: {result['id']}")
        print(f"Created: {result.get('created_time', 'N/A')}")
        print(f"Last edited: {result.get('last_edited_time', 'N/A')}")
        print(f"URL: {result.get('url', 'N/A')}")

        # Show properties
        properties = result.get('properties', {})
        print(f"\nProperties ({len(properties)}):")
        for prop_name, prop_data in properties.items():
            prop_type = prop_data.get('type', 'unknown')
            print(f"  - {prop_name}: {prop_type}")

        # Save output
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Database saved to: {output}")

        # Return as JSON
        print("\n" + "="*60)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        raise typer.Exit(1)


if __name__ == '__main__':
    app()
