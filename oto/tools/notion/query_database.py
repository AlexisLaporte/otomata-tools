#!/usr/bin/env python3
"""
Query Notion database.

Usage:
    python3 query_database.py --database_id abc123
    python3 query_database.py --database_id abc123 --page_size 50
    python3 query_database.py --database_id abc123 --output results.json
"""
import json
import sys
from pathlib import Path
from typing_extensions import Annotated
import typer

sys.path.insert(0, str(Path(__file__).parent / 'lib'))
from notion_client import NotionClient

app = typer.Typer(help="Query Notion database")


@app.command()
def main(
    database_id: Annotated[str, typer.Option(help="Database ID")],
    page_size: Annotated[int, typer.Option(help="Results per page (max 100)")] = 100,
    output: Annotated[str, typer.Option(help="Output file path (JSON)")] = None,
):
    try:
        client = NotionClient()
        db_id = database_id.replace('-', '')

        print(f"🗂️  Querying database: {db_id}...")

        result = client.query_database(
            database_id=db_id,
            page_size=page_size
        )

        results = result.get('results', [])
        print(f"\n✓ Found {len(results)} page(s)\n")

        # Display results
        for i, page in enumerate(results, 1):
            # Extract title
            title_prop = page.get('properties', {}).get('Name') or page.get('properties', {}).get('title', {})
            if 'title' in title_prop:
                title_array = title_prop['title']
                title = title_array[0]['plain_text'] if title_array else '(Untitled)'
            else:
                title = '(Untitled)'

            page_id = page['id']
            url = page.get('url', '')
            last_edited = page.get('last_edited_time', 'N/A')

            print(f"{i}. {title}")
            print(f"   ID: {page_id}")
            print(f"   Last edited: {last_edited}")
            print(f"   URL: {url}\n")

        # Save output
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"💾 Results saved to: {output}")

        # Return as JSON
        print("\n" + "="*60)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        raise typer.Exit(1)


if __name__ == '__main__':
    app()
