"""Notion commands (search, page, database)."""

import typer
from typing import Optional

app = typer.Typer(help="Notion tools")


@app.command("search")
def search(
    query: str = typer.Argument(..., help="Search query"),
    filter_type: Optional[str] = typer.Option(None, help="Filter by type (page, database)"),
):
    """Search Notion workspace."""
    from oto.tools.notion.lib.notion_client import NotionClient
    import json

    client = NotionClient()
    results = client.search(query, filter_type=filter_type)
    print(json.dumps(results, indent=2, ensure_ascii=False))


@app.command("page")
def page(
    page_id: str = typer.Argument(..., help="Notion page ID"),
    blocks: bool = typer.Option(False, "--blocks", "-b", help="Include page blocks/content"),
):
    """Get a Notion page."""
    from oto.tools.notion.lib.notion_client import NotionClient
    import json

    client = NotionClient()
    page = client.get_page(page_id)

    if blocks:
        page["blocks"] = client.get_page_blocks(page_id, recursive=True)

    print(json.dumps(page, indent=2, ensure_ascii=False))


@app.command("database")
def database(
    database_id: str = typer.Argument(..., help="Notion database ID"),
    query: bool = typer.Option(False, "--query", "-q", help="Query database entries"),
    limit: int = typer.Option(100, help="Max results when querying"),
):
    """Get a Notion database schema or query its entries."""
    from oto.tools.notion.lib.notion_client import NotionClient
    import json

    client = NotionClient()

    if query:
        results = client.query_database(database_id, page_size=limit)
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        db = client.get_database(database_id)
        print(json.dumps(db, indent=2, ensure_ascii=False))
