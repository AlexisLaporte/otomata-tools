# oto — CLI toolkit for AI agents

Your LLM already uses `gh` for GitHub, `aws` for AWS, `gcloud` for GCP.
**oto** covers the long tail — the SaaS products that don't have a CLI.

Each connector ships with a **SKILL.md** — an instruction manual that teaches your AI agent how to use it. Run `oto skills enable --all` and your Claude Code / Cursor / Aider gets instant context on 15+ APIs.

## Why CLI over MCP?

| | CLI | MCP |
|---|---|---|
| Token cost | ~80 tokens (prompt + `--help`) | 4-32x more (full schema in context) |
| Reliability | 100% | ~72% ([source](https://scalekit.com)) |
| Setup | `pipx install oto-cli` | Server + transport + config |
| Composability | Pipes: `oto sirene search "fintech" \| jq '.[]'` | None |
| Works with | Every LLM, every framework | MCP-compatible clients only |

## Installation

```bash
# Standalone CLI
pipx install oto-cli

# With specific connectors
pipx install "oto-cli[google,browser]"

# All connectors
pipx install "oto-cli[all]"

# Development
git clone https://github.com/AlexisLaporte/oto.git
cd oto && pip install -e ".[all]"
```

## Connectors

| Command | What it does | Extra |
|---------|-------------|-------|
| `oto google` | Gmail, Drive, Docs, Sheets, Slides, Calendar | `google` |
| `oto browser` | LinkedIn, Crunchbase, Pappers, Indeed, G2 | `browser` |
| `oto notion` | Search, pages, databases | — |
| `oto sirene` | French company data (INSEE SIRENE) | — |
| `oto search` | Web & news search (Serper/Google) | — |
| `oto enrichment` | Contact enrichment (Kaspr, Hunter, Lemlist) | — |
| `oto pennylane` | Accounting (Pennylane API) | — |
| `oto anthropic` | API usage & cost tracking | `anthropic` |
| `oto whatsapp` | Send & read WhatsApp messages | — |
| `oto folk` | Folk CRM (contacts, companies, deals) | — |
| `oto company` | French company lookup (multi-source) | — |
| `oto audio` | Audio recording, transcription, summaries | — |

Connectors without an "Extra" only need `requests` (included in base install).

## Quick start

```bash
# Configure secrets
mkdir -p ~/.otomata
cat > ~/.otomata/secrets.env << 'EOF'
SERPER_API_KEY=xxx
NOTION_API_KEY=secret_xxx
SIRENE_API_KEY=xxx
EOF

# Check config
oto config

# Search the web
oto search web "AI agents 2026"

# Google OAuth setup (per account)
oto google auth myaccount
oto google gmail-search "from:bob" -a myaccount

# Browse LinkedIn
oto browser linkedin profile https://linkedin.com/in/someone

# French company data
oto sirene search "fintech"
```

## Skills for AI agents

The killer feature: each connector comes with a SKILL.md that teaches your LLM how to use it.

```bash
# Enable all skills for Claude Code
oto skills enable --all

# Or pick specific ones
oto skills enable oto-google
oto skills enable oto-search
```

Once enabled, your AI agent sees these instructions in its context and knows exactly which `oto` commands to use, with what arguments, and what output to expect.

## Create your own connector

A connector is 3 files:

```
oto/commands/myservice.py    # CLI commands (Typer app)
oto/tools/myservice/         # API client
skills/oto-myservice/SKILL.md  # LLM instructions
```

See [docs/create-connector.md](docs/create-connector.md) for the full guide.

## How it works

**Auto-discovery** — `cli.py` scans `commands/` at startup. Any Python file exporting a Typer `app` becomes a sub-command. No registry, no config. Drop a file, it appears in `oto --help`.

**Three types of connectors** (same CLI contract: JSON stdout, lazy imports, `get_secret()`):
- **API** — call REST APIs via `requests`. Each client handles auth/pagination/rate-limiting as the API requires. (notion, sirene, search, pennylane, folk...)
- **Browser** — automate a real browser for sites without an API. Async, require `oto-cli[browser]`. (linkedin, crunchbase, pappers, indeed, g2)
- **SDK** — use an official client library. Currently Google Workspace via `google-api-python-client` + OAuth2. Require `oto-cli[google]`.

**Secrets** — 3-tier resolution (first found wins):
1. Environment variables
2. `.otomata/secrets.env` in project directory (walks up 4 levels)
3. `~/.otomata/secrets.env` (user-level)

**Output contract** — every command prints JSON to stdout, errors to stderr. Composable with `jq`, pipes, scripts.

**Lazy imports** — tool clients are imported inside functions, so the CLI starts fast regardless of how many connectors are installed.

See [docs/concepts.md](docs/concepts.md) for the full architecture guide.

## License

MIT
