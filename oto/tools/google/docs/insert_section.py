#!/usr/bin/env python3
"""Insert content before or after a heading in a Google Doc."""

import json
import sys
from pathlib import Path
import typer
from typing_extensions import Annotated
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))
from lib.docs_client import DocsClient

app = typer.Typer(help="Insert content in a Google Doc")


@app.command()
def main(
    doc_id: Annotated[str, typer.Option(help="Google Doc ID")],
    heading: Annotated[str, typer.Option(help="Target heading (partial match)")],
    text: Annotated[Optional[str], typer.Option(help="Text to insert")] = None,
    file: Annotated[Optional[str], typer.Option(help="File containing text to insert")] = None,
    position: Annotated[str, typer.Option(help="Insert 'before' or 'after' heading")] = "before",
):
    """Insert content before or after a heading."""
    try:
        if not text and not file:
            print("Error: Either --text or --file is required", file=sys.stderr)
            raise typer.Exit(1)

        if file:
            with open(file, 'r') as f:
                text = f.read()

        client = DocsClient()

        if position == "before":
            result = client.insert_before_heading(doc_id, heading, text)
        elif position == "after":
            result = client.insert_after_heading(doc_id, heading, text)
        else:
            print(f"Error: position must be 'before' or 'after'", file=sys.stderr)
            raise typer.Exit(1)

        print(json.dumps(result, indent=2))

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
