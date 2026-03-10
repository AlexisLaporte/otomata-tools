#!/usr/bin/env python3
"""List Google Keep notes."""

import json
import sys
from typing import Optional

import typer
from typing_extensions import Annotated

from lib.keep_client import KeepClient, KeepClientError

app = typer.Typer(help="List Google Keep notes")


@app.command()
def main(
    query: Annotated[Optional[str], typer.Option(help="Search text in title/body")] = None,
    pinned: Annotated[Optional[bool], typer.Option(help="Filter by pinned status")] = None,
    label: Annotated[Optional[str], typer.Option(help="Filter by label name")] = None,
    archived: Annotated[bool, typer.Option(help="Include archived notes")] = False,
    max_results: Annotated[int, typer.Option(help="Max notes to return")] = 50,
):
    """List Google Keep notes with optional filters."""
    try:
        client = KeepClient()
        labels = [label] if label else None
        notes = client.list_notes(
            query=query, pinned=pinned, labels=labels,
            archived=archived, max_results=max_results,
        )
        print(json.dumps({'status': 'success', 'count': len(notes), 'notes': notes}, indent=2))
    except KeepClientError as e:
        print(f"Keep error: {e}", file=sys.stderr)
        raise typer.Exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
