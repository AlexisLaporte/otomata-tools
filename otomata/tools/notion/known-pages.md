# Known Notion Pages - 321founded Workspace

This document tracks known pages and databases in the 321founded Notion workspace.

## Workspace
- **Workspace**: 321founded
- **Base URL**: https://www.notion.so/321founded/

## Known Pages

### 1. Home
- **Title**: Home
- **Page ID**: `ea9e6565c8384c75a40ccfd49de0973e`
- **URL**: https://www.notion.so/321founded/Home-ea9e6565c8384c75a40ccfd49de0973e
- **Type**: Page
- **Description**: Main workspace home page

### 2. 321-AI
- **Title**: 321-AI
- **Page ID**: `febbd37372d54dd9bfb844a74757c441`
- **URL**: https://www.notion.so/321founded/321-AI-febbd37372d54dd9bfb844a74757c441
- **Type**: Page
- **Description**: 321-AI project page, parent of Orange CDN databases
- **Children**:
  - Orange CDN Competitors Database (29cf0db746d581248d0cf5dac8b5b3f0)

## Known Databases

### Orange CDN Competitors
- **Database ID**: `29cf0db7-46d5-8124-8d0c-f5dac8b5b3f0`
- **URL**: https://www.notion.so/29cf0db746d581248d0cf5dac8b5b3f0
- **Parent Page**: 321-AI (febbd37372d54dd9bfb844a74757c441)
- **Project**: Orange CDN Boost
- **Schema**: See `create_competitors_database.py` for full schema
- **Created**: October 2025

## Integration Setup

To access these pages via the Notion API:

1. Go to https://www.notion.so/my-integrations
2. Select or create your integration
3. Copy the integration token
4. Update `tools/.env.keys` with `NOTION_API_KEY=<token>`
5. **Important**: Share each page/database with the integration:
   - Open the page in Notion
   - Click "..." → "Add connections"
   - Select your integration

## Testing Access

Test API access with:

```bash
# List all accessible teamspaces
tools/notion/notion list-teamspaces

# Get specific page
tools/notion/notion get-page ea9e6565c8384c75a40ccfd49de0973e

# Search workspace
tools/notion/notion search "321"
```

## Current Status

**Token Status**: ⚠️ Current token returns 403 Access denied
**Last Verified**: 2025-10-30
**Action Required**: Regenerate token and share pages with integration

## References

- Notion API Docs: https://developers.notion.com/
- API Version: 2025-09-03
- Integration Setup: https://www.notion.so/my-integrations
