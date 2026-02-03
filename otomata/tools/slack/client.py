"""
Slack API Client.

Requires: requests
"""

import hmac
import hashlib
from typing import Optional, Dict, Any, List

import requests

from ...config import require_secret


def verify_slack_signature(
    signing_secret: str,
    body: bytes,
    timestamp: str,
    signature: str,
) -> bool:
    """
    Verify Slack webhook signature.

    Args:
        signing_secret: Slack signing secret
        body: Request body bytes
        timestamp: X-Slack-Request-Timestamp header
        signature: X-Slack-Signature header

    Returns:
        True if valid
    """
    sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
    my_signature = "v0=" + hmac.new(
        signing_secret.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(my_signature, signature)


class SlackClient:
    """
    Slack API client for:
    - Sending messages
    - Updating messages
    - Channel management
    - User info
    """

    BASE_URL = "https://slack.com/api"

    def __init__(self, bot_token: str = None):
        """
        Initialize Slack client.

        Args:
            bot_token: Slack bot token (or set SLACK_BOT_TOKEN env var)
        """
        self.bot_token = bot_token or require_secret("SLACK_BOT_TOKEN")

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make API request."""
        url = f"{self.BASE_URL}/{endpoint}"
        headers = {"Authorization": f"Bearer {self.bot_token}"}

        response = requests.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()

        data = response.json()
        if not data.get("ok"):
            raise Exception(f"Slack API error: {data.get('error')}")

        return data

    def post_message(
        self,
        channel: str,
        text: str = None,
        blocks: List[Dict] = None,
        thread_ts: str = None,
    ) -> Dict[str, Any]:
        """
        Send a message to a channel.

        Args:
            channel: Channel ID or name
            text: Message text (fallback for blocks)
            blocks: Block Kit blocks
            thread_ts: Thread timestamp for reply

        Returns:
            Message data with ts
        """
        data = {"channel": channel}
        if text:
            data["text"] = text
        if blocks:
            data["blocks"] = blocks
        if thread_ts:
            data["thread_ts"] = thread_ts

        return self._request("POST", "chat.postMessage", json=data)

    def update_message(
        self,
        channel: str,
        ts: str,
        text: str = None,
        blocks: List[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Update an existing message.

        Args:
            channel: Channel ID
            ts: Message timestamp
            text: New text
            blocks: New blocks

        Returns:
            Updated message data
        """
        data = {"channel": channel, "ts": ts}
        if text:
            data["text"] = text
        if blocks:
            data["blocks"] = blocks

        return self._request("POST", "chat.update", json=data)

    def post_ephemeral(
        self,
        channel: str,
        user: str,
        text: str = None,
        blocks: List[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Send an ephemeral message (visible only to one user).

        Args:
            channel: Channel ID
            user: User ID
            text: Message text
            blocks: Block Kit blocks

        Returns:
            Message data
        """
        data = {"channel": channel, "user": user}
        if text:
            data["text"] = text
        if blocks:
            data["blocks"] = blocks

        return self._request("POST", "chat.postEphemeral", json=data)

    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get user information.

        Args:
            user_id: User ID

        Returns:
            User data
        """
        return self._request("GET", "users.info", params={"user": user_id})

    def list_channels(self, types: str = "public_channel") -> List[Dict[str, Any]]:
        """
        List channels.

        Args:
            types: Channel types (public_channel, private_channel, mpim, im)

        Returns:
            List of channels
        """
        data = self._request("GET", "conversations.list", params={"types": types})
        return data.get("channels", [])

    def add_reaction(self, channel: str, ts: str, name: str) -> Dict[str, Any]:
        """
        Add a reaction to a message.

        Args:
            channel: Channel ID
            ts: Message timestamp
            name: Emoji name (without colons)

        Returns:
            Response data
        """
        return self._request("POST", "reactions.add", json={
            "channel": channel,
            "timestamp": ts,
            "name": name,
        })
