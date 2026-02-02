#!/usr/bin/env python3
"""Count entries in Orange CDN Competitors database"""

import sys
import os
from typing_extensions import Annotated
import typer

# Add lib to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))
from notion_client import NotionClient

DATABASE_ID = "29cf0db746d581248d0cf5dac8b5b3f0"

app = typer.Typer(help="Count entries in Notion database")

@app.command()
def main():
    client = NotionClient()

    # Query database
    results = client._request("POST", f"databases/{DATABASE_ID}/query", data={}, use_cache=False)

    entries = results.get("results", [])
    print(f"📊 Database has {len(entries)} entries")

    # Count by category
    categories = {}
    for entry in entries:
        cat = entry.get("properties", {}).get("Category", {}).get("select", {})
        if cat:
            cat_name = cat.get("name", "Unknown")
            categories[cat_name] = categories.get(cat_name, 0) + 1

    print("\n📂 By category:")
    for cat, count in sorted(categories.items()):
        print(f"   {cat}: {count}")

    # List names
    print("\n📋 Entries:")
    for i, entry in enumerate(entries, 1):
        name_prop = entry.get("properties", {}).get("Name", {}).get("title", [])
        name = name_prop[0].get("plain_text", "Untitled") if name_prop else "Untitled"
        print(f"   {i}. {name}")

if __name__ == "__main__":
    app()
