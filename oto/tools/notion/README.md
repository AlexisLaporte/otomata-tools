# Notion Tool

Notion API integration for the 654 MEMENTO platform. Provides atomic methods for managing Notion workspaces, databases, and pages.

## Features

- 🔍 **Search** - Search across all pages and databases
- 📄 **Pages** - Get, create, update, and archive pages
- 🗂️ **Databases** - Query and manage databases
- 📊 **CSV Import** - Create databases from CSV with auto-detected schema and registry tracking
- 📝 **Content** - Append blocks to pages
- 💾 **Caching** - Automatic response caching (24h TTL for reads)
- 🔐 **Secure** - Token stored in `.keys/` directory

## Setup

### 1. Create Notion Integration

1. Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click "New integration"
3. Name it (e.g., "MEMENTO Integration")
4. Select capabilities:
   - ✅ Read content
   - ✅ Update content
   - ✅ Insert content
5. Copy the **Internal Integration Token**

### 2. Configure Token

```bash
# Create keys directory
mkdir -p /tools/notion/.keys

# Save token
echo "secret_xxxxxxxxxxxxx" > /tools/notion/.keys/notion-token.txt
chmod 600 /tools/notion/.keys/notion-token.txt
```

### 3. Share Databases/Pages

For each database or page you want to access:
1. Open the database/page in Notion
2. Click "..." → "Add connections"
3. Select your integration

## Available Methods

### notion_search
Search workspace for pages and databases.

```bash
python3 search.py --query "project management"
python3 search.py --query "tasks" --filter page
python3 search.py --query "db" --filter database --sort last_edited_time
```

### notion_get_page
Retrieve page with full content.

```bash
python3 get_page.py --page_id abc123def456
python3 get_page.py --page_id abc123 --no-content
python3 get_page.py --page_id abc123 --output page.json
```

### notion_query_database
Query database with pagination.

```bash
python3 query_database.py --database_id xyz789
python3 query_database.py --database_id xyz789 --page_size 50
python3 query_database.py --database_id xyz789 --output results.json
```

### notion_get_database
Get database schema and metadata.

```bash
python3 get_database.py --database_id xyz789
python3 get_database.py --database_id xyz789 --output schema.json
```

**Note:** With Notion API v2025-09-03, database properties are not returned in the GET database endpoint. Properties are only accessible through the `data_sources` field or by querying actual pages. The database structure is correctly created, this is just a limitation of the API response format.

### notion_create_page
Create new page in database or as child page.

```bash
# In database
python3 create_page.py --parent_id db123 --title "New Task" --parent_type database

# As child page
python3 create_page.py --parent_id page456 --title "Sub-page" --parent_type page
```

### notion_update_page
Update page properties or archive.

```bash
python3 update_page.py --page_id abc123 --archive
python3 update_page.py --page_id abc123 --unarchive
```

### notion_append_blocks
Append content blocks to page.

```bash
# Using wrapper with markdown file
./notion append PAGE_ID file.md

# Direct Python usage
python3 append_blocks.py --page_id abc123 --markdown-file report.md
```

### notion_push_markdown
Push markdown file to Notion as a new page with registry tracking.

```bash
# Create page from markdown
./notion append \
  --parent-id abc123 \
  --markdown-file partners_landscape.md \
  --title "Partners & Integrators Landscape"

# To update registry after manual page creation
# Add to notion-registry.json manually:
{
  "pages": {
    "landscape": {
      "id": "page-id",
      "url": "https://notion.so/...",
      "source_md": "partners_landscape.md",
      "title": "Partners & Integrators Landscape",
      "created_at": "2025-11-03T17:00:00Z"
    }
  }
}
```

**Note:** Currently requires manual registry update for pages. Automatic tracking coming soon.

### notion_create_database_from_csv
Create database from CSV with auto-detected schema and registry tracking.

**Note:** The `--registry` parameter should point to `notion-registry.json` (the tracking file for created databases), not `tools/notion/notion.json` (the tool credentials file).

```bash
# Using wrapper
./notion create-db \
  --registry runs/[run-id]/notion-registry.json \
  --csv partners.csv \
  --parent-id abc123 \
  --key partners \
  --db-name "Partners Database"

# With optional parameters
./notion create-db \
  --registry runs/xxx/notion-registry.json \
  --csv data.csv \
  --parent-id abc123 \
  --key mydb \
  --db-name "My Database" \
  --icon "🎯" \
  --skip-if-exists
```

**Features:**
- Auto-detects schema from CSV columns (select, text, url types)
- Creates database with properties
- Imports all CSV rows as pages
- Tracks database IDs in registry JSON for traceability
- `--skip-if-exists` prevents duplicates

**Requirements:**
- CSV must have a column named `Name` or `title` (case-insensitive for title)
- This column will become the database title/Name field
- Place this column first in your CSV for best results

**Registry format:**
```json
{
  "parent_id": "abc123",
  "databases": {
    "partners": {
      "id": "146b953c-2288-4a4a-89e9-6237e3b02e87",
      "url": "https://www.notion.so/146b953c22884a4a89e96237e3b02e87",
      "source_csv": "partners.csv",
      "parent_id": "abc123",
      "entries_count": 78,
      "created_at": "2025-11-03T09:22:31Z",
      "last_sync": "2025-11-03T09:22:31Z"
    }
  },
  "pages": {
    "landscape_analysis": {
      "id": "xyz789",
      "url": "https://www.notion.so/xyz789",
      "source_md": "partners_integrators_landscape.md",
      "title": "Partners & Integrators Landscape",
      "created_at": "2025-11-03T17:00:00Z",
      "last_sync": "2025-11-03T17:00:00Z"
    }
  }
}
```

**View in webapp:**
The registry can be viewed with a specialized UI at:
`http://localhost:8001/runs/{run-id}/notion-registry.json`

## Caching

All **GET requests** are automatically cached for **24 hours**:

- Location: `tools/.cache/notion/`
- Strategy: Hash-based (endpoint + parameters)
- TTL: 86400 seconds (24h)

**Write operations** (POST, PATCH) are never cached.

### Clear Cache

```bash
# Clear all Notion cache
rm -rf tools/.cache/notion/

# Clear specific cache file
rm tools/.cache/notion/{hash}.json
```

## API Reference

### NotionClient

Python client library with methods:

- `search(query, filter_type, sort)` - Search workspace
- `get_page(page_id)` - Get page metadata
- `get_page_blocks(page_id)` - Get page content
- `query_database(database_id, filter_obj, sorts, page_size)` - Query DB
- `get_database(database_id)` - Get DB schema
- `create_page(parent_id, parent_type, title, properties, content)` - Create page
- `update_page(page_id, properties, archived)` - Update page
- `append_blocks(page_id, blocks)` - Append blocks

### Usage in Python

```python
from lib.notion_client import NotionClient

client = NotionClient()

# Search
results = client.search("project")

# Get page
page = client.get_page("abc123")
blocks = client.get_page_blocks("abc123")

# Query database
items = client.query_database("xyz789", page_size=50)

# Create page
new_page = client.create_page(
    parent_id="db123",
    parent_type="database",
    title="New Task"
)
```

## Error Handling

All scripts exit with status codes:
- `0` - Success
- `1` - Error (token not found, API error, etc.)

Error messages are printed to stderr:
```bash
❌ Error: Notion API error: Unauthorized
```

## Dependencies

```bash
pip install requests
```

All dependencies are standard Python libraries or commonly available.

## Security

⚠️ **Important:**
- Token file is in `.gitignore`
- Never commit `notion-token.txt`
- Keep token file permissions restrictive (`chmod 600`)
- Rotate tokens if compromised

## Integration with MEMENTO

This tool is registered in the MEMENTO tools registry and can be discovered at:
- Web: http://localhost:8001/tools/notion/
- JSON: `/tools/notion/notion.json`

## Support

For Notion API documentation:
- https://developers.notion.com/

For MEMENTO platform issues:
- See main repository documentation
