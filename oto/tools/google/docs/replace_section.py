#!/usr/bin/env python3
"""Replace content of a section in a Google Doc."""

import json
import sys
from pathlib import Path
import typer
from typing_extensions import Annotated
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))
from lib.docs_client import DocsClient

app = typer.Typer(help="Replace section content in a Google Doc")


@app.command()
def main(
    doc_id: Annotated[str, typer.Option(help="Google Doc ID")],
    heading: Annotated[str, typer.Option(help="Section heading (partial match)")],
    text: Annotated[Optional[str], typer.Option(help="New content")] = None,
    file: Annotated[Optional[str], typer.Option(help="File containing new content")] = None,
):
    """Replace a section's content (keeps heading, replaces body)."""
    try:
        if not text and not file:
            print("Error: Either --text or --file is required", file=sys.stderr)
            raise typer.Exit(1)

        if file:
            with open(file, 'r') as f:
                text = f.read()

        client = DocsClient()
        result = client.replace_section(doc_id, heading, text)
        print(json.dumps(result, indent=2))

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
