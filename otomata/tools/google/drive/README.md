# Google Drive API Tool

Google Drive integration for file operations (list, download, upload) using Service Account authentication.

## Features

- **List files** with filtering by folder, custom queries
- **Download files** from Google Drive
- **Upload files** to Google Drive
- **Move files** between folders
- **Create folders** in Drive
- Built-in caching for list operations (1-hour TTL)
- Support for large file uploads with resumable transfers

## Setup

### 1. Create a Google Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable **Google Drive API**:
   - In the console, search for "Google Drive API" and enable it
4. Create a Service Account:
   - Navigate to **Credentials** → **Create Credentials** → **Service Account**
   - Fill in the name and click **Create and Continue**
   - Grant the service account the **Editor** role (or create a custom role with Drive scopes)
   - Click **Create and Continue**, then **Done**
5. Create a JSON key:
   - In **Service Accounts**, click on the created service account
   - Go to **Keys** → **Add Key** → **Create new key**
   - Select **JSON** and download the file

### 2. Configure Credentials

Save the downloaded JSON file as `tools/google-drive/.keys/gdrive-key.json`

```bash
cp /path/to/service-account-key.json tools/google-drive/.keys/gdrive-key.json
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### List Files

```bash
python3 list_files.py \
  --folder-id "123abc..." \
  --query "name contains 'report'" \
  --page-size 50 \
  --format json
```

**Parameters:**
- `--folder-id`: Filter by parent folder ID (optional)
- `--query`: Custom query (e.g., `"name contains 'report'"`)
- `--page-size`: Results per page (default: 100)
- `--fields`: Fields to retrieve (default: id, name, mimeType, modifiedTime, size, webViewLink)
- `--format`: Output format: `json` or `table` (default: json)

**Example output:**
```json
{
  "status": "success",
  "count": 2,
  "files": [
    {
      "id": "1abc...",
      "name": "report_2024.pdf",
      "mimeType": "application/pdf",
      "size": "2048576",
      "modifiedTime": "2024-10-28T12:00:00Z",
      "webViewLink": "https://drive.google.com/file/d/1abc.../view"
    }
  ]
}
```

### Download File

```bash
python3 download_file.py \
  --file-id "1abc..." \
  --output "/tmp/downloaded_file.pdf"
```

**Parameters:**
- `--file-id`: Google Drive file ID (required)
- `--output`: Local path to save file (required)

**Example output:**
```json
{
  "status": "success",
  "file_id": "1abc...",
  "filename": "report_2024.pdf",
  "output_path": "/tmp/downloaded_file.pdf",
  "size": "2048576",
  "mime_type": "application/pdf"
}
```

### Upload File

```bash
python3 upload_file.py \
  --file "/path/to/local/file.pdf" \
  --folder-id "123abc..." \
  --name "custom_filename.pdf"
```

**Parameters:**
- `--file`: Local file path (required)
- `--folder-id`: Target folder ID (optional, uses root if not specified)
- `--name`: Custom filename on Drive (optional, uses original name if not specified)

**Example output:**
```json
{
  "status": "success",
  "file_id": "1abc...",
  "filename": "custom_filename.pdf",
  "web_link": "https://drive.google.com/file/d/1abc.../view",
  "size": "2048576",
  "local_path": "/path/to/local/file.pdf"
}
```

### Move File

```bash
python3 move_file.py \
  --file-id "1abc..." \
  --destination-folder-id "123xyz..."
```

**Parameters:**
- `--file-id`: Google Drive file ID to move (required)
- `--destination-folder-id`: Target folder ID (required)

**Example output:**
```json
{
  "status": "success",
  "file_id": "1abc...",
  "filename": "presentation.pdf",
  "new_parents": ["123xyz..."],
  "web_link": "https://drive.google.com/file/d/1abc.../view"
}
```

### Create Folder

```bash
python3 create_folder.py \
  --name "Partners" \
  --parent-folder-id "123abc..."
```

**Parameters:**
- `--name`: Folder name (required)
- `--parent-folder-id`: Parent folder ID (optional, uses root if not specified)

**Example output:**
```json
{
  "status": "success",
  "folder_id": "456def...",
  "folder_name": "Partners",
  "web_link": "https://drive.google.com/drive/folders/456def..."
}
```

## Usage in Memento Runs

Example agent that uses this tool:

```yaml
name: document-collector
version: 1.0.0
description: Collect documents from shared Google Drive folder

steps:
  - phase: list_documents
    description: List all PDFs in client folder
    tool: google-drive
    method: list_files
    params:
      folder_id: "{{ env.CLIENT_FOLDER_ID }}"
      query: "mimeType='application/pdf'"
      format: json

  - phase: download_documents
    description: Download all collected PDFs
    tool: google-drive
    method: download_file
    for_each: "{{ outputs.list_documents.files }}"
    params:
      file_id: "{{ item.id }}"
      output: "{{ run.dir }}/downloads/{{ item.name }}"
```

## API Query Examples

### Find files by name
```bash
--query "name contains 'report'"
```

### Find files by MIME type
```bash
--query "mimeType='application/pdf'"
```

### Find files modified in last 7 days
```bash
--query "modifiedTime > '2024-10-21T00:00:00'"
```

### Combine multiple queries
```bash
--query "name contains 'report' and mimeType='application/pdf'"
```

### Find files NOT in trash
```bash
--query "trashed = false"
```

See [Google Drive API documentation](https://developers.google.com/drive/api/guides/search-files) for more query syntax.

## Troubleshooting

### "Credentials file not found"
- Ensure `gdrive-key.json` exists in `tools/google-drive/.keys/`
- Verify the file is a valid JSON service account key

### "Permission denied" errors
- The service account needs Drive API access
- Ensure you granted it the Editor role when creating the service account
- If uploading/modifying files, share the target folder with the service account email

### Rate limiting
- Google Drive API has rate limits (10,000 queries per day)
- Results are cached for 1 hour to reduce API calls
- Clear cache manually by deleting files in `tools/.cache/google-drive/`

## Caching

List results are cached for 1 hour (3600 seconds) in `tools/.cache/google-drive/`.

To disable caching or change TTL in Python:
```python
from lib.drive_client import DriveClient

# Disable caching (TTL = 0)
client = DriveClient(creds_path, cache_ttl=0)

# Or set custom TTL (in seconds)
client = DriveClient(creds_path, cache_ttl=7200)  # 2 hours
```

## Implementation Details

### Service Account Authentication
Uses `google-auth` with Service Account JSON credentials. The service account runs operations without requiring user interaction.

### Resumable Uploads
Large file uploads use Google Drive API's resumable upload protocol for reliability.

### File Download
Media downloads are streamed directly to disk to handle large files efficiently.

### Caching Strategy
- Cache key: MD5 hash of (folder_id + query + page_size)
- TTL: Configurable (default 1 hour)
- Storage: `tools/.cache/google-drive/`

## Error Handling

All operations return structured JSON responses:

```json
{
  "status": "error",
  "error": "File not found"
}
```

See script outputs for detailed error messages.

## Security Notes

- Service account JSON keys are sensitive - keep them in `.keys/` (gitignored)
- Never commit credentials to version control
- Use IAM roles to limit service account permissions to required scopes
- Consider using folder-level access if uploading to specific folders

## References

- [Google Drive API v3 Documentation](https://developers.google.com/drive/api/v3/about-sdk)
- [Service Account Authentication](https://developers.google.com/identity/protocols/oauth2/service-account)
- [Drive API Query Operators](https://developers.google.com/drive/api/guides/search-files)
