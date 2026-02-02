"""Otomata CLI - unified entry point for all tools."""

import typer
from typing import Optional

app = typer.Typer(
    name="otomata",
    help="CLI tools for automating tasks with Google, Notion, and more.",
    no_args_is_help=True,
)


# Google subcommands
google_app = typer.Typer(help="Google Workspace tools (Drive, Docs, Sheets, Slides)")
app.add_typer(google_app, name="google")


@google_app.command("drive-list")
def google_drive_list(
    folder_id: Optional[str] = typer.Option(None, help="Filter by parent folder ID"),
    query: Optional[str] = typer.Option(None, help="Custom query filter"),
    limit: int = typer.Option(100, help="Max results"),
):
    """List files in Google Drive."""
    from otomata.tools.google.drive.lib.drive_client import DriveClient
    from otomata.tools.google.credentials import get_credentials
    import json

    creds = get_credentials()
    client = DriveClient()
    files = client.list_files(folder_id=folder_id, query=query, page_size=limit)
    print(json.dumps({"count": len(files), "files": files}, indent=2))


@google_app.command("drive-download")
def google_drive_download(
    file_id: str = typer.Argument(..., help="Google Drive file ID"),
    output: str = typer.Argument(..., help="Output path"),
):
    """Download a file from Google Drive."""
    from otomata.tools.google.drive.lib.drive_client import DriveClient

    client = DriveClient()
    result = client.download_file(file_id, output)
    print(f"Downloaded: {result['filename']} -> {result['output_path']}")


@google_app.command("docs-headings")
def google_docs_headings(
    doc_id: str = typer.Argument(..., help="Google Docs document ID"),
):
    """List headings in a Google Doc."""
    from otomata.tools.google.docs.lib.docs_client import DocsClient
    import json

    client = DocsClient()
    headings = client.list_headings(doc_id)
    print(json.dumps(headings, indent=2))


@google_app.command("docs-section")
def google_docs_section(
    doc_id: str = typer.Argument(..., help="Google Docs document ID"),
    heading: str = typer.Argument(..., help="Heading text to find"),
):
    """Get content of a section in a Google Doc."""
    from otomata.tools.google.docs.lib.docs_client import DocsClient

    client = DocsClient()
    section = client.get_section_content(doc_id, heading)
    if section:
        print(f"# {section.title}\n")
        print(section.content)
    else:
        print(f"Section not found: {heading}")
        raise typer.Exit(1)


# Notion subcommands
notion_app = typer.Typer(help="Notion tools")
app.add_typer(notion_app, name="notion")


@notion_app.command("search")
def notion_search(
    query: str = typer.Argument(..., help="Search query"),
    filter_type: Optional[str] = typer.Option(None, help="Filter by type (page, database)"),
):
    """Search Notion workspace."""
    from otomata.tools.notion.lib.notion_client import NotionClient
    import json

    client = NotionClient()
    results = client.search(query, filter_type=filter_type)
    print(json.dumps(results, indent=2, ensure_ascii=False))


@notion_app.command("page")
def notion_page(
    page_id: str = typer.Argument(..., help="Notion page ID"),
    blocks: bool = typer.Option(False, "--blocks", "-b", help="Include page blocks/content"),
):
    """Get a Notion page."""
    from otomata.tools.notion.lib.notion_client import NotionClient
    import json

    client = NotionClient()
    page = client.get_page(page_id)

    if blocks:
        page["blocks"] = client.get_page_blocks(page_id, recursive=True)

    print(json.dumps(page, indent=2, ensure_ascii=False))


@notion_app.command("database")
def notion_database(
    database_id: str = typer.Argument(..., help="Notion database ID"),
    query: bool = typer.Option(False, "--query", "-q", help="Query database entries"),
    limit: int = typer.Option(100, help="Max results when querying"),
):
    """Get a Notion database schema or query its entries."""
    from otomata.tools.notion.lib.notion_client import NotionClient
    import json

    client = NotionClient()

    if query:
        results = client.query_database(database_id, page_size=limit)
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        db = client.get_database(database_id)
        print(json.dumps(db, indent=2, ensure_ascii=False))


# Config commands
@app.command("config")
def show_config():
    """Show current configuration and detected secrets."""
    from otomata.config import find_env_file, get_secret

    env_file = find_env_file()
    print(f"Env file: {env_file or 'Not found'}")
    print()
    print("Secrets status:")
    print(f"  GOOGLE_SERVICE_ACCOUNT: {'✓ Found' if get_secret('GOOGLE_SERVICE_ACCOUNT') else '✗ Not found'}")
    print(f"  NOTION_API_KEY: {'✓ Found' if get_secret('NOTION_API_KEY') else '✗ Not found'}")


if __name__ == "__main__":
    app()
