---
name: oto-whatsapp
description: WhatsApp messaging. Use for sending/reading WhatsApp messages, listing chats.
---

# WhatsApp (oto whatsapp)

Prerequisite: `oto` installed, WhatsApp authenticated via QR code.

## Setup

```bash
oto whatsapp auth    # scan QR code with phone
```

## Commands

```bash
# Send a message
oto whatsapp send "+33612345678" "Hello from oto"

# List recent chats
oto whatsapp list-chats -n 10

# Read messages from a chat (use JID from list-chats)
oto whatsapp read "33612345678@s.whatsapp.net" -n 20
oto whatsapp read "+33612345678" -n 20
```

## Output

JSON. Chat JIDs: `<number>@s.whatsapp.net` (individual), `<id>@g.us` (group).
French numbers are auto-normalized (06... → 336...).
