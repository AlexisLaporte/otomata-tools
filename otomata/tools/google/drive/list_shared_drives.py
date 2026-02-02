#!/usr/bin/env python3
"""List Shared Drives (Team Drives) accessible to service account"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "lib"))

from drive_client import DriveClient

creds_path = Path(__file__).parent / ".keys" / "gdrive-key.json"

print("Listing Shared Drives...")
client = DriveClient(str(creds_path))

# List Shared Drives
drives = client.service.drives().list(pageSize=50).execute()

drives_list = drives.get('drives', [])

if not drives_list:
    print("\n⚠ No Shared Drives found")
    print("\nTo use a Shared Drive:")
    print("1. Create a Shared Drive in Google Drive")
    print("2. Add the service account as a member:")
    print("   memento-drive@agents-475314.iam.gserviceaccount.com")
else:
    print(f"\n✓ Found {len(drives_list)} Shared Drive(s):\n")
    for i, drive in enumerate(drives_list, 1):
        print(f"{i}. {drive.get('name')}")
        print(f"   ID: {drive.get('id')}")
        print()
