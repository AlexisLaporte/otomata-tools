#!/usr/bin/env python3
"""Get a Google Keep note by ID."""

import json
import sys

import typer
from typing_extensions import Annotated

from lib.keep_client import KeepClient, KeepClientError

app = typer.Typer(help="Get a Google Keep note")


@app.command()
def main(
    note_id: Annotated[str, typer.Argument(help="Note ID")],
):
    """Get full details of a Google Keep note."""
    try:
        client = KeepClient()
        note = client.get_note(note_id)
        print(json.dumps({'status': 'success', **note}, indent=2))
    except KeepClientError as e:
        print(f"Keep error: {e}", file=sys.stderr)
        raise typer.Exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
