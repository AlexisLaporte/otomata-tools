# Otomata Tools

CLI tools for automating tasks with Google Workspace, Notion, and more.

## Installation

```bash
pip install -e .
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

- **Google**
  - Drive: list, download, upload, export
  - Docs: headings, sections, insert, replace
  - Sheets: create, read
  - Slides: generate presentations

- **Notion**
  - Search, pages, databases, blocks
