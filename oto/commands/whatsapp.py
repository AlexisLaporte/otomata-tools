"""WhatsApp commands (auth, send, read, list chats)."""

import json
import typer
from typing import Optional

app = typer.Typer(help="WhatsApp messaging")


@app.command("auth")
def auth():
    """Authenticate WhatsApp via QR code scan."""
    from oto.tools.whatsapp import WhatsAppClient
    result = WhatsAppClient().auth()
    print(json.dumps(result, indent=2, ensure_ascii=False))


@app.command("send")
def send(
    to: str = typer.Argument(..., help="Phone number (+33612345678) or JID"),
    message: str = typer.Argument(..., help="Message text"),
):
    """Send a WhatsApp message."""
    from oto.tools.whatsapp import WhatsAppClient
    result = WhatsAppClient().send(to=to, message=message)
    print(json.dumps(result, indent=2, ensure_ascii=False))


@app.command("list-chats")
def list_chats(
    limit: int = typer.Option(20, "--limit", "-n", help="Max chats to return"),
):
    """List recent WhatsApp chats."""
    from oto.tools.whatsapp import WhatsAppClient
    result = WhatsAppClient().list_chats(limit=limit)
    print(json.dumps(result, indent=2, ensure_ascii=False))


@app.command("read")
def read_chat(
    chat: str = typer.Argument(..., help="Chat JID or phone number"),
    limit: int = typer.Option(20, "--limit", "-n", help="Max messages"),
):
    """Read messages from a WhatsApp chat."""
    from oto.tools.whatsapp import WhatsAppClient
    result = WhatsAppClient().read(chat=chat, limit=limit)
    print(json.dumps(result, indent=2, ensure_ascii=False))
