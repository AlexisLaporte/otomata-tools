# Oto

CLI toolkit for AI agents — covers the long tail of SaaS APIs that don't have a CLI.

Repo: `AlexisLaporte/oto`. Package: `oto-cli` on PyPI. Command: `oto`.

## Philosophy

- **CLI-first**: everything goes through `oto <command>`, no MCP, no server
- **For AI agents**: JSON on stdout, errors on stderr, composable with pipes
- **Modular**: each connector is a separate file, auto-discovered at startup
- **No over-engineering**: no plugin registry, no ABC, no MCP

## Stack

- Python 3.10+, Typer (CLI), Hatchling (build)
- Google APIs (auth, drive, docs, sheets, slides, gmail, keep)
- o-browser (browser automation, Patchright) — optional
- Requests (HTTP), python-dotenv (secrets)

## Architecture

```
oto/
├── oto/
│   ├── cli.py                  # Dynamic command discovery + main()
│   ├── config.py               # Secrets 3-tier (.otomata/secrets.env)
│   ├── commands/               # 1 file = 1 sub-command (auto-discovered)
│   │   ├── google.py           # drive, docs, sheets, slides, gmail, calendar, auth
│   │   ├── notion.py           # search, page, database
│   │   ├── browser.py          # linkedin, crunchbase, pappers, indeed, g2
│   │   ├── sirene.py           # SIRENE API (search, get, stock)
│   │   ├── search.py           # web, news (serper)
│   │   ├── enrichment.py       # kaspr, hunter, lemlist
│   │   ├── pennylane.py        # accounting
│   │   ├── anthropic.py        # usage, cost, summary
│   │   ├── company.py          # SIREN lookup multi-source
│   │   ├── whatsapp.py         # WhatsApp messaging
│   │   └── skills.py           # Claude Code skills (enable/disable)
│   └── tools/                  # API clients
│       ├── google/             # gmail, drive, docs, sheets, slides, calendar, keep
│       ├── notion/             # pages, databases, search
│       ├── browser/            # linkedin, crunchbase, pappers, indeed, g2
│       ├── whatsapp/           # Node.js bridge (whatsapp-web.js)
│       ├── sirene/             # INSEE SIRENE API
│       ├── serper/             # Google search (web, news)
│       ├── anthropic/          # Admin API (usage, costs)
│       ├── pennylane/          # Accounting
│       ├── kaspr/, hunter/, lemlist/  # Enrichment & outreach
│       └── folk/, slack/, resend/     # CRM & messaging
├── skills/                     # Claude Code skills
│   └── oto-*/SKILL.md          # LLM instruction manuals
└── pyproject.toml              # entry point: oto = "oto.cli:main"
```

## Adding a new connector

A connector = 3 files:

1. **`commands/myservice.py`** — Typer app, exports `app`
2. **`tools/myservice/`** — API client(s)
3. **`skills/oto-myservice/SKILL.md`** — LLM instructions

See `docs/create-connector.md` for details.

## Command pattern

Each `commands/*.py` file:
```python
import typer
import json
from typing import Optional

app = typer.Typer(help="My service description")

@app.command("do-thing")
def do_thing(
    query: str = typer.Argument(..., help="What to do"),
    max_results: int = typer.Option(20, "--max-results", "-n"),
):
    """Do a thing."""
    from oto.tools.myservice.client import MyServiceClient
    client = MyServiceClient()
    results = client.do_thing(query=query, max_results=max_results)
    print(json.dumps(results, indent=2))
```

Key rules:
- `app = typer.Typer()` exported, auto-discovered by `cli.py`
- Tool imports **inside functions** (lazy) so the CLI stays fast
- Always `print(json.dumps(..., indent=2))` for output
- Missing secrets raise `ValueError`, caught by `main()` → clean stderr message

## Secrets

3-tier resolution (first found wins):
1. Environment variables
2. `.otomata/secrets.env` in project directory (walks up 4 levels)
3. `~/.otomata/secrets.env` (user-level)

## Google OAuth

Tokens stored in `~/.otomata/google-oauth-token-{name}.json`.

Add an account: `oto google auth <name>` — opens browser for OAuth flow.
List accounts: `oto google auth --list`.

## Skills (Claude Code)

Skills = SKILL.md files in `skills/oto-*/`, symlinked to `~/.claude/skills/`.

```bash
oto skills list                    # see status
oto skills enable --all            # enable all
oto skills enable oto-google       # enable one
oto skills disable oto-pennylane   # disable one
```
