#!/usr/bin/env python3
"""Move a section in a Google Doc."""

import json
import sys
from pathlib import Path
import typer
from typing_extensions import Annotated

sys.path.insert(0, str(Path(__file__).parent))
from lib.docs_client import DocsClient

app = typer.Typer(help="Move a section in a Google Doc")


@app.command()
def main(
    doc_id: Annotated[str, typer.Option(help="Google Doc ID")],
    section: Annotated[str, typer.Option(help="Section heading to move (partial match)")],
    before: Annotated[str, typer.Option(help="Move before this heading (partial match)")],
):
    """Move a section before another heading."""
    try:
        client = DocsClient()
        result = client.move_section(doc_id, section, before)
        print(json.dumps(result, indent=2))

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
