#!/usr/bin/env python3
"""Check Google Drive storage quota"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "lib"))

from drive_client import DriveClient

creds_path = Path(__file__).parent / ".keys" / "gdrive-key.json"

print("Checking Drive quota...")
client = DriveClient(str(creds_path))

# Get storage info
about = client.service.about().get(fields="storageQuota,user").execute()

quota = about.get('storageQuota', {})
user = about.get('user', {})

print(f"\nUser: {user.get('emailAddress', 'Unknown')}")
print(f"\nStorage Quota:")
print(f"  Limit: {int(quota.get('limit', 0)) / (1024**3):.2f} GB")
print(f"  Usage: {int(quota.get('usage', 0)) / (1024**3):.2f} GB")
print(f"  Usage in Drive: {int(quota.get('usageInDrive', 0)) / (1024**3):.2f} GB")
print(f"  Usage in Trash: {int(quota.get('usageInDriveTrash', 0)) / (1024**3):.2f} GB")

if quota.get('limit'):
    usage_pct = (int(quota.get('usage', 0)) / int(quota.get('limit'))) * 100
    print(f"\n  Usage: {usage_pct:.1f}%")
