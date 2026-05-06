"""Zoho Desk commands — tickets, contacts, departments."""

import json
import typer
from typing import Optional

app = typer.Typer(help="Zoho Desk — tickets, contacts, departments")


def _out(data):
    print(json.dumps(data, indent=2, ensure_ascii=False))


def _client():
    from oto.tools.zohodesk import ZohoDeskClient
    return ZohoDeskClient()


def _parse_fields(fields: list[str]) -> dict:
    """Parse --field key=value pairs into a dict (no nesting)."""
    result: dict = {}
    for f in fields:
        if "=" not in f:
            raise typer.BadParameter(f"Invalid field format: {f!r} (expected key=value)")
        key, value = f.split("=", 1)
        result[key] = value
    return result


# --- Tickets ---


@app.command("tickets")
def tickets(
    max_results: int = typer.Option(20, "--max-results", "-n"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Open / On Hold / Escalated / Closed"),
    department_id: Optional[str] = typer.Option(None, "--department-id", "-d"),
    sort_by: Optional[str] = typer.Option(None, "--sort", help="e.g. -createdTime, priority, modifiedTime"),
    from_index: int = typer.Option(1, "--from", help="Pagination start (1-indexed)"),
    fields: Optional[str] = typer.Option(None, "--fields", help="Comma-separated extra fields, e.g. customFields"),
):
    """List tickets."""
    data = _client().list_tickets(
        from_index=from_index,
        limit=max_results,
        department_id=department_id,
        status=status,
        sort_by=sort_by,
        fields=fields,
    )
    items = data.get("data", [])
    _out({"count": len(items), "tickets": items})


@app.command("ticket")
def ticket(
    ticket_id: str = typer.Argument(..., help="Ticket ID"),
    include: Optional[str] = typer.Option(None, "--include", help="contacts,products,assignee,team,..."),
):
    """Get a single ticket."""
    _out(_client().get_ticket(ticket_id, include=include))


@app.command("add-ticket")
def add_ticket(
    subject: str = typer.Option(..., "--subject"),
    department_id: str = typer.Option(..., "--department-id", "-d"),
    contact_id: Optional[str] = typer.Option(None, "--contact-id"),
    description: Optional[str] = typer.Option(None, "--description"),
    priority: Optional[str] = typer.Option(None, "--priority", help="Low / Medium / High"),
    status: Optional[str] = typer.Option(None, "--status"),
    channel: Optional[str] = typer.Option(None, "--channel", help="Email / Web / Phone / ..."),
    category: Optional[str] = typer.Option(None, "--category"),
    fields: list[str] = typer.Option([], "--field", "-f", help="Extra field key=value (repeatable)"),
):
    """Create a ticket. Provide subject + department-id + contact-id."""
    data: dict = {
        "subject": subject,
        "departmentId": department_id,
    }
    if contact_id:
        data["contactId"] = contact_id
    if description:
        data["description"] = description
    if priority:
        data["priority"] = priority
    if status:
        data["status"] = status
    if channel:
        data["channel"] = channel
    if category:
        data["category"] = category
    data.update(_parse_fields(fields))
    _out(_client().create_ticket(data))


@app.command("update-ticket")
def update_ticket(
    ticket_id: str = typer.Argument(..., help="Ticket ID"),
    fields: list[str] = typer.Option(..., "--field", "-f", help="key=value (repeatable)"),
):
    """Patch ticket fields."""
    data = _parse_fields(fields)
    _out(_client().update_ticket(ticket_id, data))


@app.command("delete-ticket")
def delete_ticket(ticket_id: str = typer.Argument(..., help="Ticket ID")):
    """Move ticket to trash."""
    _out(_client().delete_ticket(ticket_id))


@app.command("search-tickets")
def search_tickets(
    query: list[str] = typer.Option(..., "--q", help="Field filter, e.g. priority=High (repeatable)"),
    max_results: int = typer.Option(20, "--max-results", "-n"),
    from_index: int = typer.Option(1, "--from"),
):
    """Search tickets. Pass field filters via --q (e.g. --q status=Open --q priority=High)."""
    q = _parse_fields(query)
    data = _client().search_tickets(q, from_index=from_index, limit=max_results)
    items = data.get("data", [])
    _out({"count": len(items), "tickets": items})


# --- Threads ---


@app.command("threads")
def threads(ticket_id: str = typer.Argument(..., help="Ticket ID")):
    """List threads (replies/comments) of a ticket."""
    data = _client().list_threads(ticket_id)
    items = data.get("data", [])
    _out({"count": len(items), "threads": items})


@app.command("thread")
def thread(
    ticket_id: str = typer.Argument(..., help="Ticket ID"),
    thread_id: str = typer.Argument(..., help="Thread ID"),
):
    """Get a single thread (full body)."""
    _out(_client().get_thread(ticket_id, thread_id))


# --- Contacts ---


@app.command("contacts")
def contacts(
    max_results: int = typer.Option(20, "--max-results", "-n"),
    from_index: int = typer.Option(1, "--from"),
):
    """List contacts."""
    data = _client().list_contacts(from_index=from_index, limit=max_results)
    items = data.get("data", [])
    _out({"count": len(items), "contacts": items})


@app.command("contact")
def contact(contact_id: str = typer.Argument(..., help="Contact ID")):
    """Get a single contact."""
    _out(_client().get_contact(contact_id))


@app.command("add-contact")
def add_contact(
    last_name: str = typer.Option(..., "--last-name"),
    first_name: Optional[str] = typer.Option(None, "--first-name"),
    email: Optional[str] = typer.Option(None, "--email"),
    phone: Optional[str] = typer.Option(None, "--phone"),
    account_id: Optional[str] = typer.Option(None, "--account-id"),
    fields: list[str] = typer.Option([], "--field", "-f"),
):
    """Create a contact."""
    data: dict = {"lastName": last_name}
    if first_name:
        data["firstName"] = first_name
    if email:
        data["email"] = email
    if phone:
        data["phone"] = phone
    if account_id:
        data["accountId"] = account_id
    data.update(_parse_fields(fields))
    _out(_client().create_contact(data))


@app.command("search-contacts")
def search_contacts(
    query: list[str] = typer.Option(..., "--q", help="Field filter, e.g. email=foo@bar.com"),
):
    """Search contacts."""
    q = _parse_fields(query)
    _out(_client().search_contacts(q))


# --- Departments / Agents ---


@app.command("departments")
def departments():
    """List departments."""
    data = _client().list_departments()
    items = data.get("data", [])
    _out({"count": len(items), "departments": items})


@app.command("agents")
def agents():
    """List agents."""
    data = _client().list_agents()
    items = data.get("data", [])
    _out({"count": len(items), "agents": items})
