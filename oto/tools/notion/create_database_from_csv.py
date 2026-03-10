#!/usr/bin/env python3
"""
Create Notion database from CSV file with registry tracking
"""

import sys
import os
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from typing_extensions import Annotated
import typer

# Add lib to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))
from notion_client import NotionClient

app = typer.Typer(help="Create Notion database from CSV")


def detect_property_type(column_name: str, sample_values: List[str]) -> Dict[str, Any]:
    """Detect Notion property type from CSV column name and sample values"""

    column_lower = column_name.lower()

    # Check column name patterns first
    if column_name == "Name" or column_lower == "title":
        return {"title": {}}

    if "url" in column_lower or "website" in column_lower or "link" in column_lower:
        return {"url": {}}

    # Check for select types (limited unique values with common suffixes)
    if any(suffix in column_lower for suffix in ["type", "status", "priority", "category", "role", "relationship"]):
        # Get unique non-empty values
        unique_values = set(v for v in sample_values if v)
        if len(unique_values) <= 20:  # Reasonable limit for select options
            options = [{"name": val, "color": "default"} for val in sorted(unique_values)]
            return {"select": {"options": options}}

    # Default to rich_text
    return {"rich_text": {}}


def infer_schema_from_csv(csv_path: str) -> Dict[str, Any]:
    """Infer Notion database schema from CSV file"""

    schema = {}

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

        if not rows:
            raise ValueError(f"CSV file {csv_path} is empty")

        # Get column names
        columns = list(rows[0].keys())

        # Validate that there's a title column
        has_title = any(col == "Name" or col.lower() == "title" for col in columns)
        if not has_title:
            raise ValueError(
                f"CSV must have a 'Name' or 'title' column as the first column. "
                f"Found columns: {', '.join(columns)}\n"
                f"Rename your primary column to 'Name' to use it as the database title field."
            )

        # Collect sample values for each column (first 100 rows)
        sample_data = {col: [] for col in columns}
        for row in rows[:100]:
            for col in columns:
                if row.get(col):
                    sample_data[col].append(row[col])

        # Detect types for each column
        for col in columns:
            # Replace underscores with spaces for display names
            display_name = col.replace('_', ' ')
            schema[display_name] = detect_property_type(col, sample_data[col])

    return schema


def create_database(client: NotionClient, parent_id: str, db_name: str,
                   schema: Dict[str, Any], icon_emoji: str = "📊") -> str:
    """Create Notion database with schema"""

    print(f"🏗️  Creating database: {db_name}")

    # API v2025-09-03: properties go inside initial_data_source
    payload = {
        "parent": {"type": "page_id", "page_id": parent_id},
        "title": [{"type": "text", "text": {"content": db_name}}],
        "icon": {"type": "emoji", "emoji": icon_emoji},
        "initial_data_source": {
            "properties": schema
        }
    }

    response = client._request("POST", "databases", data=payload, use_cache=False)
    database_id = response["id"]

    print(f"✅ Database created: {database_id}")
    print(f"   URL: https://www.notion.so/{database_id.replace('-', '')}")

    return database_id


def create_page_properties(row: Dict[str, str], schema: Dict[str, Any]) -> Dict[str, Any]:
    """Convert CSV row to Notion page properties"""

    properties = {}

    for display_name, prop_type in schema.items():
        # Map display name back to CSV column (handle underscore conversion)
        csv_col = display_name.replace(' ', '_')
        if csv_col not in row:
            csv_col = display_name  # Try exact match

        value = row.get(csv_col, "")

        if not value:
            continue

        # Convert based on property type
        if "title" in prop_type:
            properties[display_name] = {
                "title": [{"text": {"content": value}}]
            }
        elif "rich_text" in prop_type:
            properties[display_name] = {
                "rich_text": [{"text": {"content": value[:2000]}}]  # Notion limit
            }
        elif "select" in prop_type:
            properties[display_name] = {"select": {"name": value}}
        elif "url" in prop_type:
            properties[display_name] = {"url": value}
        elif "number" in prop_type:
            try:
                properties[display_name] = {"number": float(value)}
            except ValueError:
                pass

    return properties


def import_csv_data(client: NotionClient, database_id: str, csv_path: str,
                   schema: Dict[str, Any]) -> int:
    """Import CSV data into database"""

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"\n📝 Importing {len(rows)} entries...")

    success_count = 0
    for i, row in enumerate(rows, 1):
        try:
            properties = create_page_properties(row, schema)

            # Get name for logging (first column or Name column)
            name = row.get('Name', row.get(list(row.keys())[0], f"Entry {i}"))

            payload = {
                "parent": {"database_id": database_id},
                "properties": properties
            }

            client._request("POST", "pages", data=payload, use_cache=False)
            print(f"   [{i}/{len(rows)}] ✅ {name}")
            success_count += 1

        except Exception as e:
            print(f"   [{i}/{len(rows)}] ❌ Error: {e}")
            continue

    print(f"\n✅ Imported {success_count}/{len(rows)} entries")
    return success_count


def update_registry(registry_path: str, key: str, database_id: str,
                   csv_path: str, parent_id: str, entries_count: int):
    """Update or create registry JSON file"""

    # Load existing registry or create new
    if os.path.exists(registry_path):
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
    else:
        registry = {"databases": {}}

    # Ensure databases key exists
    if "databases" not in registry:
        registry["databases"] = {}

    # Add/update entry
    registry["databases"][key] = {
        "id": database_id,
        "url": f"https://www.notion.so/{database_id.replace('-', '')}",
        "source_csv": os.path.basename(csv_path),
        "parent_id": parent_id,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "entries_count": entries_count,
        "last_sync": datetime.utcnow().isoformat() + "Z"
    }

    # Create directory if needed
    os.makedirs(os.path.dirname(registry_path), exist_ok=True)

    # Write registry
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Registry updated: {registry_path}")


@app.command()
def main(
    registry: Annotated[str, typer.Option(help="Path to registry JSON file")],
    csv: Annotated[str, typer.Option(help="Path to CSV file")],
    parent_id: Annotated[str, typer.Option(help="Parent page ID")],
    key: Annotated[str, typer.Option(help="Registry key for this database")],
    db_name: Annotated[str, typer.Option(help="Database name/title")],
    icon: Annotated[str, typer.Option(help="Database icon emoji")] = "📊",
    skip_if_exists: Annotated[bool, typer.Option(help="Skip creation if key already exists in registry")] = False,
):
    try:
        # Check if already exists
        if skip_if_exists and os.path.exists(registry):
            with open(registry, 'r') as f:
                registry_data = json.load(f)
                if key in registry_data.get("databases", {}):
                    print(f"⏭️  Database '{key}' already exists in registry, skipping")
                    print(f"   URL: {registry_data['databases'][key]['url']}")
                    return

        # Initialize client
        client = NotionClient()

        # Infer schema from CSV
        print(f"📊 Analyzing CSV: {csv}")
        schema = infer_schema_from_csv(csv)
        print(f"   Detected {len(schema)} columns")

        # Create database
        database_id = create_database(client, parent_id, db_name,
                                     schema, icon)

        # Import data
        entries_count = import_csv_data(client, database_id, csv, schema)

        # Update registry
        update_registry(registry, key, database_id, csv,
                       parent_id, entries_count)

        print(f"\n🎉 All done! View database at:")
        print(f"   https://www.notion.so/{database_id.replace('-', '')}")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
