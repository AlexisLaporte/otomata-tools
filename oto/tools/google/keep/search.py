#!/usr/bin/env python3
"""Search Google Keep notes."""

import json
import sys

import typer
from typing_extensions import Annotated

from lib.keep_client import KeepClient, KeepClientError

app = typer.Typer(help="Search Google Keep notes")


@app.command()
def main(
    query: Annotated[str, typer.Argument(help="Search query")],
    max_results: Annotated[int, typer.Option(help="Max notes to return")] = 20,
):
    """Search notes by text content."""
    try:
        client = KeepClient()
        notes = client.list_notes(query=query, max_results=max_results)
        print(json.dumps({'status': 'success', 'count': len(notes), 'notes': notes}, indent=2))
    except KeepClientError as e:
        print(f"Keep error: {e}", file=sys.stderr)
        raise typer.Exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
