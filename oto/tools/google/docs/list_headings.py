#!/usr/bin/env python3
"""List all headings in a Google Doc."""

import json
import sys
from pathlib import Path
import typer
from typing_extensions import Annotated

sys.path.insert(0, str(Path(__file__).parent))
from lib.docs_client import DocsClient

app = typer.Typer(help="List headings in a Google Doc")


@app.command()
def main(
    doc_id: Annotated[str, typer.Option(help="Google Doc ID")],
    format: Annotated[str, typer.Option(help="Output format: json or text")] = "text",
):
    """List all headings with their positions."""
    try:
        client = DocsClient()
        headings = client.list_headings(doc_id)

        if format == "json":
            print(json.dumps(headings, indent=2))
        else:
            print(f"Found {len(headings)} headings:\n")
            for h in headings:
                indent = ""
                if h['style'] == 'HEADING_2':
                    indent = "  "
                elif h['style'] == 'HEADING_3':
                    indent = "    "
                print(f"[{h['start_index']:5d}] {indent}{h['text'][:70]}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
