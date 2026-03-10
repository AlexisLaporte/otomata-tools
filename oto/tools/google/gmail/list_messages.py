#!/usr/bin/env python3
"""List Gmail messages."""

import json
import sys
from typing import Optional

import typer
from typing_extensions import Annotated

from lib.gmail_client import GmailClient, GmailClientError

app = typer.Typer(help="List Gmail messages")


@app.command()
def main(
    query: Annotated[Optional[str], typer.Option(help="Gmail search query")] = None,
    label: Annotated[Optional[str], typer.Option(help="Filter by label ID")] = None,
    max_results: Annotated[int, typer.Option(help="Max messages to return")] = 20,
):
    """List recent Gmail messages with metadata."""
    try:
        client = GmailClient()
        label_ids = [label] if label else None
        messages = client.list_messages(query=query, label_ids=label_ids, max_results=max_results)
        print(json.dumps({'status': 'success', 'count': len(messages), 'messages': messages}, indent=2))
    except GmailClientError as e:
        print(f"Gmail error: {e}", file=sys.stderr)
        raise typer.Exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
