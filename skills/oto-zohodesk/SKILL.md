---
name: oto-zohodesk
description: Zoho Desk — tickets, threads (replies), contacts, departments. Use for support / helpdesk ticket management.
---

# Zoho Desk

Use `oto zohodesk` commands via Bash. All output is JSON.

## Prerequisites

Secrets in `~/.otomata/secrets.env`:
```
ZOHO_DESK_CLIENT_ID=...
ZOHO_DESK_CLIENT_SECRET=...
ZOHO_DESK_REFRESH_TOKEN=...
ZOHO_DESK_ORG_ID=...           # found in Setup → Developer Space → API
# Optional (defaults to US data center):
# ZOHO_DESK_API_DOMAIN=https://desk.zoho.eu
# ZOHO_DESK_ACCOUNTS_URL=https://accounts.zoho.eu
```

OAuth scopes required when generating the refresh token:
`Desk.tickets.ALL,Desk.contacts.READ,Desk.basic.READ,Desk.settings.READ`

Setup walkthrough: `docs/zoho-desk-oauth-setup.md`.

## Commands

```bash
# Tickets
oto zohodesk tickets -n 50
oto zohodesk tickets --status Open --sort -createdTime
oto zohodesk tickets --department-id 12345 -n 100

oto zohodesk ticket <ticket_id> --include contacts,assignee

oto zohodesk add-ticket \
    --subject "Bug X" \
    --department-id 12345 \
    --contact-id 67890 \
    --description "Plein de détails" \
    --priority High

oto zohodesk update-ticket <ticket_id> -f status=Closed -f priority=Low
oto zohodesk delete-ticket <ticket_id>

oto zohodesk search-tickets --q status=Open --q priority=High -n 20

# Threads (replies on a ticket)
oto zohodesk threads <ticket_id>
oto zohodesk thread <ticket_id> <thread_id>

# Contacts
oto zohodesk contacts -n 50
oto zohodesk contact <contact_id>
oto zohodesk add-contact --last-name Doe --first-name John --email john@doe.com

# Departments / Agents
oto zohodesk departments
oto zohodesk agents
```

## Notes

- Pagination uses `--from` (1-indexed) and `--max-results` (max 100).
- `--sort` accepts a field name; prefix with `-` for descending (e.g. `-createdTime`).
- `update-ticket` takes flat key=value; for nested fields (e.g. `customFields.cf_xxx`) use `-f customFields.cf_severity=P1`.
