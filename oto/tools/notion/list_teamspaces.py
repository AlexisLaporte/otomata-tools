#!/usr/bin/env python3
"""
List Notion teamspaces/workspaces accessible to the integration.

Since Notion API doesn't have a direct endpoint for listing teamspaces,
this script searches all accessible pages and databases to identify
the different workspaces/teamspaces.

Usage:
    python3 list_teamspaces.py
    python3 list_teamspaces.py --output teamspaces.json
"""

import sys
import os
import json
from pathlib import Path
from collections import defaultdict
from typing_extensions import Annotated
import typer

# Add lib to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))
from notion_client import NotionClient

app = typer.Typer(help="List Notion teamspaces")


def extract_workspace_info(item):
    """Extract workspace/teamspace information from a Notion object."""
    info = {
        'id': item.get('id'),
        'type': item.get('object'),
        'url': item.get('url', ''),
        'last_edited_time': item.get('last_edited_time'),
        'created_time': item.get('created_time'),
        'archived': item.get('archived', False)
    }

    # Extract title
    if item['object'] == 'page':
        title_prop = item.get('properties', {}).get('title', {})
        title_array = title_prop.get('title', [])
        info['title'] = title_array[0]['plain_text'] if title_array else '(Untitled)'
    else:  # database
        title_array = item.get('title', [])
        info['title'] = title_array[0]['plain_text'] if title_array else '(Untitled)'

    # Extract workspace from URL (workspace subdomain)
    url = item.get('url', '')
    if url and 'notion.so/' in url:
        parts = url.split('notion.so/')
        if len(parts) > 1:
            path_parts = parts[1].split('/')
            if len(path_parts) > 0:
                # First part might be workspace name
                workspace = path_parts[0] if not path_parts[0].startswith(('page', 'database')) else 'default'
                info['workspace'] = workspace

    # Extract parent information
    parent = item.get('parent', {})
    info['parent_type'] = parent.get('type')
    if parent.get('type') == 'workspace':
        info['parent'] = 'workspace'
        info['in_teamspace'] = True
    elif parent.get('type') == 'page_id':
        info['parent'] = parent.get('page_id')
        info['in_teamspace'] = False
    elif parent.get('type') == 'database_id':
        info['parent'] = parent.get('database_id')
        info['in_teamspace'] = False

    return info


def list_all_accessible_items(client):
    """Search for all accessible pages and databases."""
    print("🔍 Searching for all accessible Notion items...")

    all_items = []

    # Search with empty query to get all accessible items
    try:
        result = client.search(query="", sort="last_edited_time")
        items = result.get('results', [])
        all_items.extend(items)

        # Handle pagination
        has_more = result.get('has_more', False)
        next_cursor = result.get('next_cursor')

        while has_more and next_cursor:
            print(f"   Fetching more results (cursor: {next_cursor[:10]}...)...")
            # Note: The current NotionClient doesn't support pagination yet
            # This is a placeholder for future enhancement
            break

    except Exception as e:
        print(f"❌ Error searching: {e}")
        return []

    print(f"✓ Found {len(all_items)} accessible items\n")
    return all_items


def analyze_teamspaces(items):
    """Analyze items to identify teamspaces and their contents."""

    workspaces = defaultdict(lambda: {
        'pages': [],
        'databases': [],
        'root_items': []  # Items directly in workspace (not nested in pages)
    })

    for item in items:
        info = extract_workspace_info(item)
        workspace_name = info.get('workspace', 'unknown')

        # Add to workspace
        if info['type'] == 'page':
            workspaces[workspace_name]['pages'].append(info)
        elif info['type'] == 'database':
            workspaces[workspace_name]['databases'].append(info)

        # Check if it's a root item (directly in workspace)
        if info.get('in_teamspace') or info.get('parent_type') == 'workspace':
            workspaces[workspace_name]['root_items'].append(info)

    return dict(workspaces)


def print_teamspaces_summary(teamspaces):
    """Print a human-readable summary of teamspaces."""

    print("=" * 80)
    print("TEAMSPACES / WORKSPACES SUMMARY")
    print("=" * 80)
    print()

    if not teamspaces:
        print("⚠️  No teamspaces found or integration has no access")
        print("\nMake sure to:")
        print("  1. Share pages/databases with the integration")
        print("  2. Check integration permissions at https://www.notion.so/my-integrations")
        return

    for workspace_name, data in teamspaces.items():
        print(f"📁 Workspace: {workspace_name}")
        print(f"   Pages: {len(data['pages'])}")
        print(f"   Databases: {len(data['databases'])}")
        print(f"   Root items: {len(data['root_items'])}")
        print()

        # Show root items (main pages/dbs in teamspace)
        if data['root_items']:
            print("   Root items:")
            for item in data['root_items'][:5]:  # Show first 5
                icon = "📄" if item['type'] == 'page' else "🗂️"
                print(f"      {icon} {item['title']}")
                print(f"         ID: {item['id']}")
                print(f"         URL: {item['url']}")

            if len(data['root_items']) > 5:
                print(f"      ... and {len(data['root_items']) - 5} more")
        print()

    print("=" * 80)

    # Statistics
    total_pages = sum(len(ws['pages']) for ws in teamspaces.values())
    total_dbs = sum(len(ws['databases']) for ws in teamspaces.values())

    print(f"\n📊 Total Statistics:")
    print(f"   Teamspaces/Workspaces: {len(teamspaces)}")
    print(f"   Total Pages: {total_pages}")
    print(f"   Total Databases: {total_dbs}")
    print(f"   Total Items: {total_pages + total_dbs}")


@app.command()
def main(
    output: Annotated[str, typer.Option(help="Output JSON file path")] = None,
    json_only: Annotated[bool, typer.Option("--json", help="Output only JSON (no summary)")] = False,
):
    try:
        # Initialize client
        client = NotionClient()

        # Get all accessible items
        items = list_all_accessible_items(client)

        if not items:
            print("\n⚠️  No items found. This could mean:")
            print("   1. The integration token is invalid or expired")
            print("   2. No pages/databases are shared with the integration")
            print("   3. Integration doesn't have required permissions")
            print("\n   Check: https://www.notion.so/my-integrations")
            raise typer.Exit(1)

        # Analyze teamspaces
        teamspaces = analyze_teamspaces(items)

        # Output
        if json_only:
            print(json.dumps(teamspaces, indent=2, ensure_ascii=False))
        else:
            print_teamspaces_summary(teamspaces)

        # Save to file if requested
        if output:
            output_data = {
                'teamspaces': teamspaces,
                'summary': {
                    'total_workspaces': len(teamspaces),
                    'total_pages': sum(len(ws['pages']) for ws in teamspaces.values()),
                    'total_databases': sum(len(ws['databases']) for ws in teamspaces.values())
                },
                'raw_items': [extract_workspace_info(item) for item in items]
            }

            with open(output, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            print(f"\n💾 Full data saved to: {output}")

    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)
        print("\nSetup instructions:", file=sys.stderr)
        print("   1. Go to https://www.notion.so/my-integrations", file=sys.stderr)
        print("   2. Create or access your integration", file=sys.stderr)
        print("   3. Copy the token", file=sys.stderr)
        print("   4. Save to: tools/notion/.keys/notion-token.txt", file=sys.stderr)
        print("   5. Or set NOTION_API_KEY environment variable", file=sys.stderr)
        raise typer.Exit(1)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        raise typer.Exit(1)


if __name__ == '__main__':
    app()
