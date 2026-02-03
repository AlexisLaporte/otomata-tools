# Otomata Tools

CLI tools for automating tasks with Google Workspace, Notion, and more.

## Installation

```bash
# For 321founded team
pipx install git+https://github.com/321founded/otomata-tools.git

# From source repo
pipx install git+https://github.com/AlexisLaporte/otomata-tools.git

# Verify
otomata --help
```

See [Installation Guide](docs/installation.md) for detailed instructions (Linux, macOS, Windows).

### Development

```bash
git clone https://github.com/AlexisLaporte/otomata-tools.git
cd otomata-tools
pip install -e ".[dev,browser]"
```

## Configuration

Secrets are loaded in this order:
1. Environment variables
2. `.env.local` in current working directory (or parent dirs)
3. User config in `~/.config/otomata/`

### Required secrets

| Secret | Description | Setup guide |
|--------|-------------|-------------|
| `GOOGLE_SERVICE_ACCOUNT` | Google service account JSON (as string) | [Setup guide](docs/google-service-account-setup.md) |
| `NOTION_API_KEY` | Notion integration token | [Notion integrations](https://www.notion.so/my-integrations) |

### Example `.env.local`

```bash
GOOGLE_SERVICE_ACCOUNT='{"type":"service_account","project_id":"...", ...}'
NOTION_API_KEY='secret_xxx'
```

## Usage

### CLI

```bash
# Show config status
otomata config

# Google Drive
otomata google drive-list
otomata google drive-list --folder-id=xxx
otomata google drive-download <file-id> <output-path>

# Google Docs
otomata google docs-headings <doc-id>
otomata google docs-section <doc-id> "Section Title"

# Notion
otomata notion search "query"
otomata notion page <page-id> --blocks
otomata notion database <db-id> --query
```

### As Python library

```python
from otomata.tools.google.drive.lib.drive_client import DriveClient
from otomata.tools.notion.lib.notion_client import NotionClient

# Google Drive
drive = DriveClient()
files = drive.list_files(folder_id="xxx")

# Notion
notion = NotionClient()
results = notion.search("query")
```

## Tools

### API clients
- **Google** - Drive, Docs, Sheets, Slides
- **Notion** - Search, pages, databases, blocks

### Browser clients (no public API)
- **Collective** - Collective.work job listings
- **Browser lib** - Patchright wrapper for session persistence

### Usage

```bash
# Scrape Collective.work jobs
python -m otomata.tools.collective.client \
  --url "https://app.collective.work/..." \
  --profile ~/.cache/browser-session-myprofile \
  --output jobs.json
```

```python
from otomata.tools.collective import CollectiveClient

client = CollectiveClient(profile_path="~/.cache/my-session")
result = await client.scrape_jobs(url="https://app.collective.work/...")

# Or use browser directly
from otomata.tools.browser import BrowserClient

async with BrowserClient(profile_path="~/.cache/my-session") as browser:
    await browser.goto("https://example.com")
    text = await browser.get_text()
```
