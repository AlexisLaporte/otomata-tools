#!/usr/bin/env python3
"""Create a Google Keep note."""

import json
import sys
from typing import Optional

import typer
from typing_extensions import Annotated

from lib.keep_client import KeepClient, KeepClientError

app = typer.Typer(help="Create a Google Keep note")


@app.command()
def main(
    title: Annotated[str, typer.Option(help="Note title")],
    text: Annotated[str, typer.Option(help="Note body text")] = "",
    pinned: Annotated[bool, typer.Option(help="Pin the note")] = False,
    color: Annotated[Optional[str], typer.Option(help="Note color (e.g. Red, Blue, Green)")] = None,
    label: Annotated[Optional[str], typer.Option(help="Label name (created if missing)")] = None,
):
    """Create a new text note in Google Keep."""
    try:
        client = KeepClient()
        labels = [label] if label else None
        note = client.create_note(
            title=title, text=text, pinned=pinned,
            color=color, labels=labels,
        )
        print(json.dumps({'status': 'success', **note}, indent=2))
    except KeepClientError as e:
        print(f"Keep error: {e}", file=sys.stderr)
        raise typer.Exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
