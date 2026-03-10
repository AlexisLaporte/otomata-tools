#!/usr/bin/env python3
"""Search Gmail messages."""

import json
import sys

import typer
from typing_extensions import Annotated

from lib.gmail_client import GmailClient, GmailClientError

app = typer.Typer(help="Search Gmail messages")


@app.command()
def main(
    query: Annotated[str, typer.Option(help="Gmail search query (e.g. 'is:unread', 'from:user@example.com')")],
    max_results: Annotated[int, typer.Option(help="Max messages to return")] = 20,
):
    """Search Gmail messages using Gmail query syntax."""
    try:
        client = GmailClient()
        messages = client.search(query=query, max_results=max_results)
        print(json.dumps({'status': 'success', 'count': len(messages), 'messages': messages}, indent=2))
    except GmailClientError as e:
        print(f"Gmail error: {e}", file=sys.stderr)
        raise typer.Exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
