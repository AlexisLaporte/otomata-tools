"""
Mistral API client (OpenAI-compatible REST API).

Requires: requests

Authentication:
    MISTRAL_API_KEY: API key from https://console.mistral.ai/
"""

import json
from typing import List, Dict, Any

import requests

from ...config import require_secret


class MistralClient:
    """
    Mistral API client.

    Features:
    - Chat completions
    - JSON mode
    - Multiple model support
    """

    BASE_URL = "https://api.mistral.ai/v1"

    def __init__(self, api_key: str = None, model: str = "mistral-small-latest"):
        self.api_key = api_key or require_secret("MISTRAL_API_KEY")
        self.model = model

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        json_mode: bool = False,
        model: str = None,
    ) -> Dict[str, Any]:
        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        resp = requests.post(
            f"{self.BASE_URL}/chat/completions",
            headers=self._get_headers(),
            json=payload,
            timeout=60,
        )

        if not resp.ok:
            raise Exception(f"Mistral API error: {resp.status_code} {resp.text}")

        return resp.json()

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        json_mode: bool = False,
        model: str = None,
    ) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        result = self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=json_mode,
            model=model,
        )

        return result["choices"][0]["message"]["content"]

    def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        model: str = None,
    ) -> Dict[str, Any]:
        content = self.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True,
            model=model,
        )

        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        return json.loads(content)

    def chat_with_tools(
        self,
        messages: List[Dict],
        tools: List[Dict],
        temperature: float = 0.3,
        max_tokens: int = 2048,
        model: str = None,
    ) -> Dict[str, Any]:
        """Chat completion with tool definitions. Returns raw API response.

        The agent loop (calling tools, appending results) is handled by the caller.
        """
        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "tools": tools,
            "tool_choice": "auto",
        }

        resp = requests.post(
            f"{self.BASE_URL}/chat/completions",
            headers=self._get_headers(),
            json=payload,
            timeout=120,
        )

        if not resp.ok:
            raise Exception(f"Mistral API error: {resp.status_code} {resp.text}")

        return resp.json()
