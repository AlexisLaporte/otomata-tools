#!/usr/bin/env python3
"""Send a Gmail message."""

import json
import sys
from typing import Optional

import typer
from typing_extensions import Annotated

from lib.gmail_client import GmailClient, GmailClientError

app = typer.Typer(help="Send a Gmail message")


@app.command()
def main(
    to: Annotated[str, typer.Option(help="Recipient email address")],
    subject: Annotated[str, typer.Option(help="Email subject")],
    body: Annotated[str, typer.Option(help="Email body (plain text)")],
    html: Annotated[Optional[str], typer.Option(help="Email body (HTML, optional)")] = None,
    cc: Annotated[Optional[str], typer.Option(help="CC recipients")] = None,
    bcc: Annotated[Optional[str], typer.Option(help="BCC recipients")] = None,
):
    """Send an email via Gmail."""
    try:
        client = GmailClient()
        result = client.send(to=to, subject=subject, body=body, html=html, cc=cc, bcc=bcc)
        print(json.dumps({'status': 'success', **result}, indent=2))
    except GmailClientError as e:
        print(f"Gmail error: {e}", file=sys.stderr)
        raise typer.Exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
