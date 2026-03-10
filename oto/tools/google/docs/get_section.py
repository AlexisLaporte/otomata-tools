#!/usr/bin/env python3
"""Get content of a section in a Google Doc."""

import json
import sys
from pathlib import Path
import typer
from typing_extensions import Annotated

sys.path.insert(0, str(Path(__file__).parent))
from lib.docs_client import DocsClient

app = typer.Typer(help="Get section content from a Google Doc")


@app.command()
def main(
    doc_id: Annotated[str, typer.Option(help="Google Doc ID")],
    heading: Annotated[str, typer.Option(help="Section heading (partial match)")],
    format: Annotated[str, typer.Option(help="Output format: text or json")] = "text",
):
    """Get the content of a section."""
    try:
        client = DocsClient()
        section = client.get_section_content(doc_id, heading)

        if section is None:
            print(f"Section not found: {heading}", file=sys.stderr)
            raise typer.Exit(1)

        if format == "json":
            print(json.dumps({
                'title': section.title,
                'start_index': section.start_index,
                'end_index': section.end_index,
                'heading_type': section.heading_type,
                'content': section.content,
                'content_length': len(section.content)
            }, indent=2))
        else:
            print(f"=== {section.title} ===")
            print(f"Position: {section.start_index} - {section.end_index}")
            print(f"Length: {len(section.content)} chars")
            print()
            print(section.content)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
