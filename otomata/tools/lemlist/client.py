"""
Lemlist API Client for email campaign management.

Requires: requests
"""

import json
import time
import base64
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

import requests

from ...config import require_secret


@dataclass
class Campaign:
    """Campaign data."""
    id: str
    name: str
    status: str
    senders: List[str]
    emoji: str = ""


@dataclass
class Lead:
    """Lead data for campaign. Uses camelCase to match Lemlist API."""
    email: str
    firstName: str = None
    lastName: str = None
    companyName: str = None
    phone: str = None
    picture: str = None
    linkedinUrl: str = None


class LemlistClient:
    """
    Lemlist API client for:
    - Campaign management (list, create, pause, update)
    - Lead management (add, delete, export)
    - Sequence/step management (get, add, update)
    - Campaign tree (structured view with branches)
    - Activities & stats
    """

    BASE_URL = "https://api.lemlist.com/api"

    def __init__(self, api_key: str = None):
        """
        Initialize Lemlist client.

        Args:
            api_key: Lemlist API key (or set LEMLIST_API_KEY env var)
        """
        self.api_key = api_key or require_secret("LEMLIST_API_KEY")
        self._last_request = 0.0

    @property
    def headers(self) -> dict:
        """Get auth headers dict."""
        return {
            "Authorization": self._get_auth_header(),
            "Content-Type": "application/json",
        }

    def _rate_limit(self):
        """Enforce minimum 100ms between requests."""
        elapsed = time.time() - self._last_request
        if elapsed < 0.1:
            time.sleep(0.1 - elapsed)
        self._last_request = time.time()

    def _get_auth_header(self) -> str:
        """Get Basic auth header."""
        credentials = f":{self.api_key}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Make API request with rate limiting."""
        self._rate_limit()

        url = f"{self.BASE_URL}/{endpoint}"
        headers = {"Authorization": self._get_auth_header()}

        response = requests.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()

        if response.content:
            return response.json()
        return {}

    # --- Campaigns ---

    def list_campaigns(self) -> List[Campaign]:
        """List all campaigns."""
        data = self._request("GET", "campaigns")
        return [
            Campaign(
                id=c["_id"],
                name=c.get("name", ""),
                status=c.get("status", ""),
                senders=c.get("senders", []),
                emoji=c.get("emoji", ""),
            )
            for c in data
        ]

    def get_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Get campaign details."""
        return self._request("GET", f"campaigns/{campaign_id}")

    def create_campaign(self, name: str) -> Dict[str, Any]:
        """Create a new campaign (returns campaign with sequenceId)."""
        return self._request("POST", "campaigns", json={"name": name})

    def pause_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Pause a campaign."""
        return self._request("POST", f"campaigns/{campaign_id}/pause")

    def update_campaign(self, campaign_id: str, data: dict) -> Dict[str, Any]:
        """Update campaign (e.g., senders)."""
        return self._request("PATCH", f"campaigns/{campaign_id}", json=data)

    # --- Sequences & Steps ---

    def get_sequences(self, campaign_id: str) -> Dict[str, Any]:
        """Get sequences for a campaign.

        Returns:
            Dict mapping sequence_id -> sequence data with steps and level.
        """
        return self._request("GET", f"campaigns/{campaign_id}/sequences")

    def get_sequence_steps(self, campaign_id: str, sequence_id: str) -> List[Dict]:
        """Get steps for a specific sequence."""
        sequences = self.get_sequences(campaign_id)
        if sequence_id in sequences:
            return sequences[sequence_id].get('steps', [])
        return []

    def add_step(self, sequence_id: str, step: dict) -> Dict[str, Any]:
        """Add a step to a sequence.

        Args:
            sequence_id: Sequence ID (e.g., 'seq_abc123')
            step: Step data including 'type' (email, linkedinVisit, etc.)
                  For email: {'type': 'email', 'subject': '...', 'message': '...', 'delay': 0}
        """
        return self._request("POST", f"sequences/{sequence_id}/steps", json=step)

    def update_step(self, sequence_id: str, step_id: str, data: dict) -> Dict[str, Any]:
        """Update a step.

        Args:
            sequence_id: Sequence ID
            step_id: Step ID
            data: Update data (must include 'type' field)
        """
        return self._request("PATCH", f"sequences/{sequence_id}/steps/{step_id}", json=data)

    # --- Campaign Tree ---

    def get_campaign_tree(self, campaign_id: str) -> Dict[str, Any]:
        """Get full campaign structure with sequences organized by level.

        Returns a tree structure with sequences dict, steps_flat list (depth-first),
        and branch information for conditionals.
        """
        campaign = self.get_campaign(campaign_id)
        sequences_raw = self.get_sequences(campaign_id)

        sequences = {}
        root_sequence = None

        for seq_id, seq_data in sequences_raw.items():
            level = seq_data.get('level', 0)
            if level == 0:
                root_sequence = seq_id

            steps = []
            for step in seq_data.get('steps', []):
                step_clean = {
                    'id': step.get('_id'),
                    'type': step.get('type'),
                    'delay': step.get('delay'),
                }
                if step.get('type') == 'email':
                    step_clean['subject'] = step.get('subject', '')
                    step_clean['message'] = step.get('message', '')
                elif step.get('type') in ('linkedinInvite', 'linkedinMessage', 'linkedinSend'):
                    step_clean['message'] = step.get('message', '')
                elif step.get('type') == 'conditional':
                    conditions = step.get('conditions', [])
                    step_clean['branches'] = []
                    for cond in conditions:
                        branch = {
                            'sequence_id': cond.get('sequenceId'),
                            'label': cond.get('label', 'Fallback' if cond.get('fallback') else 'Unknown'),
                            'fallback': cond.get('fallback', False),
                        }
                        if cond.get('key'):
                            branch['key'] = cond['key']
                        step_clean['branches'].append(branch)

                steps.append(step_clean)

            sequences[seq_id] = {
                'id': seq_id,
                'level': level,
                'steps': steps,
            }

        # Build flat list in execution order (depth-first traversal)
        steps_flat = []

        def traverse(seq_id: str, path: str = 'root'):
            if seq_id not in sequences:
                return
            seq = sequences[seq_id]
            for step in seq['steps']:
                steps_flat.append({
                    'sequence': seq_id,
                    'step': step,
                    'path': path,
                    'level': seq['level'],
                })
                if step.get('type') == 'conditional' and step.get('branches'):
                    for branch in step['branches']:
                        child_seq = branch.get('sequence_id')
                        if child_seq:
                            branch_label = branch.get('label', 'branch')
                            child_path = f"{path} > {branch_label}"
                            traverse(child_seq, child_path)

        if root_sequence:
            traverse(root_sequence)

        return {
            'id': campaign_id,
            'name': campaign.get('name', ''),
            'status': campaign.get('status', 'unknown'),
            'root_sequence': root_sequence,
            'sequences': sequences,
            'steps_flat': steps_flat,
        }

    def save_campaign_tree(self, campaign_id: str, directory: Path = None, tree: dict = None) -> Path:
        """Save campaign tree to local JSON file.

        Args:
            campaign_id: Campaign ID
            directory: Directory to save to (default: current directory)
            tree: Optional pre-fetched tree (will fetch if not provided)

        Returns:
            Path to saved file
        """
        if tree is None:
            tree = self.get_campaign_tree(campaign_id)

        save_dir = Path(directory) if directory else Path.cwd()
        save_dir.mkdir(parents=True, exist_ok=True)
        tree['synced_at'] = datetime.now().isoformat()

        filepath = save_dir / f"{campaign_id}.json"
        filepath.write_text(json.dumps(tree, indent=2, ensure_ascii=False))
        return filepath

    @staticmethod
    def load_campaign_tree(campaign_id: str, directory: Path = None) -> Optional[dict]:
        """Load campaign tree from local cache.

        Args:
            campaign_id: Campaign ID
            directory: Directory to load from (default: current directory)

        Returns:
            Campaign tree dict or None if not cached
        """
        load_dir = Path(directory) if directory else Path.cwd()
        filepath = load_dir / f"{campaign_id}.json"
        if filepath.exists():
            return json.loads(filepath.read_text())
        return None

    def sync_campaign(self, campaign_id: str, directory: Path = None) -> dict:
        """Fetch campaign tree from API and save locally.

        Returns:
            Campaign tree dict
        """
        tree = self.get_campaign_tree(campaign_id)
        self.save_campaign_tree(campaign_id, directory=directory, tree=tree)
        return tree

    # --- Tree helpers (work on tree dicts from get_campaign_tree) ---

    @staticmethod
    def find_step(tree: dict, step_id: str) -> Optional[dict]:
        """Find a step by ID in a campaign tree."""
        for item in tree.get('steps_flat', []):
            if item['step'].get('id') == step_id:
                return item
        return None

    @staticmethod
    def get_first_email(tree: dict) -> Optional[dict]:
        """Get the first email step in execution order."""
        for item in tree.get('steps_flat', []):
            if item['step'].get('type') == 'email':
                return item
        return None

    @staticmethod
    def get_emails(tree: dict) -> List[dict]:
        """Get all email steps from a campaign tree."""
        return [item for item in tree.get('steps_flat', []) if item['step'].get('type') == 'email']

    @staticmethod
    def print_tree(tree: dict):
        """Print campaign tree in a readable format."""
        print(f"Campaign: {tree['name']}")
        print(f"Status: {tree['status']}")
        if tree.get('synced_at'):
            print(f"Synced: {tree['synced_at'][:16].replace('T', ' ')}")
        print()
        print("Sequence:")
        for item in tree['steps_flat']:
            step = item['step']
            indent = '  ' * item['level']
            delay = f"J+{step['delay']}" if step['delay'] else 'J+0'

            if step['type'] == 'email':
                label = step.get('subject', '')[:45]
                print(f"{indent}[{delay}] 📧 {label}")
            elif step['type'] == 'conditional':
                branches = [b['label'][:20] for b in step.get('branches', [])]
                print(f"{indent}[{delay}] ❓ {' | '.join(branches)}")
            elif step['type'] == 'linkedinVisit':
                print(f"{indent}[{delay}] 👁️  LinkedIn visit")
            elif step['type'] == 'linkedinInvite':
                print(f"{indent}[{delay}] 🤝 LinkedIn invite")
            elif step['type'] in ('linkedinSend', 'linkedinMessage'):
                print(f"{indent}[{delay}] 💬 LinkedIn message")
            elif step['type'] == 'phone':
                print(f"{indent}[{delay}] 📞 Phone call")
            else:
                print(f"{indent}[{delay}] {step['type']}")

    # --- Leads ---

    def add_lead(self, campaign_id: str, lead) -> Dict[str, Any]:
        """Add lead to campaign.

        Args:
            campaign_id: Campaign ID
            lead: Lead dataclass or dict with email + optional fields
        """
        if isinstance(lead, Lead):
            data = {}
            if lead.firstName:
                data["firstName"] = lead.firstName
            if lead.lastName:
                data["lastName"] = lead.lastName
            if lead.companyName:
                data["companyName"] = lead.companyName
            if lead.phone:
                data["phone"] = lead.phone
            if lead.linkedinUrl:
                data["linkedinUrl"] = lead.linkedinUrl
            email = lead.email
        elif isinstance(lead, dict):
            lead = dict(lead)  # copy to avoid mutating
            email = lead.pop("email")
            data = lead
        else:
            raise TypeError(f"lead must be Lead or dict, got {type(lead)}")

        return self._request("POST", f"campaigns/{campaign_id}/leads/{email}", json=data)

    def get_all_leads(self, campaign_id: str) -> List[Dict[str, Any]]:
        """Get all leads from a campaign via CSV export."""
        import csv
        import io

        csv_text = self.export_leads(campaign_id)
        if not csv_text.strip():
            return []
        reader = csv.DictReader(io.StringIO(csv_text))
        return list(reader)

    def delete_lead(self, campaign_id: str, email: str) -> Dict[str, Any]:
        """Remove lead from campaign."""
        return self._request("DELETE", f"campaigns/{campaign_id}/leads/{email}")

    def export_leads(self, campaign_id: str, state: str = None) -> str:
        """Export leads from campaign as CSV."""
        self._rate_limit()
        params = {}
        if state:
            params["state"] = state

        response = requests.get(
            f"{self.BASE_URL}/campaigns/{campaign_id}/export",
            headers={"Authorization": self._get_auth_header()},
            params=params
        )
        response.raise_for_status()
        return response.text

    # --- Activities & Stats ---

    def get_activities(self, campaign_id: str = None, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get activities (lead interactions).

        Args:
            campaign_id: Optional campaign filter
            limit: Max results (default 100)
            offset: Pagination offset
        """
        params = {'limit': limit, 'offset': offset}
        if campaign_id:
            params['campaignId'] = campaign_id
        return self._request("GET", "activities", params=params)

    def sync_activities(self, campaign_id: str = None, since: str = None, max_pages: int = 50) -> List[Dict]:
        """Fetch all activities with pagination.

        Args:
            campaign_id: Optional campaign filter
            since: Optional ISO date string to filter activities after this date
            max_pages: Maximum number of pages to fetch (default 50 = 5000 activities)
        """
        all_activities = []
        offset = 0
        limit = 100
        pages = 0
        while pages < max_pages:
            batch = self.get_activities(campaign_id, limit, offset)
            if not batch:
                break
            if since:
                batch = [a for a in batch if a.get('createdAt', '') >= since]
            all_activities.extend(batch)
            offset += limit
            pages += 1
            if len(batch) < limit:
                break
            if since and batch and all(a.get('createdAt', '') < since for a in batch):
                break
        return all_activities

    def get_campaign_stats(self, campaign_id: str) -> Dict[str, Any]:
        """Get stats for a campaign from activities."""
        activities = self.get_activities(campaign_id=campaign_id, limit=1000)
        counts = Counter(a.get('type') for a in activities)
        return {
            'total_activities': len(activities),
            'emails_sent': counts.get('emailsSent', 0),
            'emails_opened': counts.get('emailsOpened', 0),
            'emails_replied': counts.get('emailsReplied', 0),
            'emails_bounced': counts.get('emailsBounced', 0),
            'linkedin_visits': counts.get('linkedinVisitDone', 0),
            'linkedin_invites': counts.get('linkedinInviteDone', 0),
            'linkedin_messages': counts.get('linkedinSent', 0),
            'linkedin_accepted': counts.get('linkedinInviteAccepted', 0),
            'by_type': dict(counts),
        }

    # --- Status ---

    def status(self) -> Dict[str, Any]:
        """Check API connection status."""
        try:
            campaigns = self.list_campaigns()
            return {"connected": True, "campaigns_count": len(campaigns)}
        except Exception as e:
            return {"connected": False, "error": str(e)}
