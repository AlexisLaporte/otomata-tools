#!/usr/bin/env python3
"""Get a Gmail message by ID."""

import json
import sys

import typer
from typing_extensions import Annotated

from lib.gmail_client import GmailClient, GmailClientError

app = typer.Typer(help="Get a Gmail message")


@app.command()
def main(
    message_id: Annotated[str, typer.Argument(help="Gmail message ID")],
):
    """Get full content of a Gmail message."""
    try:
        client = GmailClient()
        message = client.get_message(message_id)
        print(json.dumps({'status': 'success', 'message': message}, indent=2, ensure_ascii=False))
    except GmailClientError as e:
        print(f"Gmail error: {e}", file=sys.stderr)
        raise typer.Exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
