"""
Groq API client for fast LLM inference.

Requires: requests

Authentication:
    GROQ_API_KEY: API key from https://console.groq.com/
"""

import json
from typing import Optional, List, Dict, Any

import requests

from ...config import require_secret


class GroqClient:
    """
    Groq API client for fast LLM inference.

    Features:
    - Chat completions
    - JSON mode
    - Multiple model support
    """

    BASE_URL = "https://api.groq.com/openai/v1"

    def __init__(self, api_key: str = None, model: str = "llama-3.1-8b-instant"):
        """
        Initialize Groq client.

        Args:
            api_key: Groq API key (defaults to GROQ_API_KEY env)
            model: Default model to use
        """
        self.api_key = api_key or require_secret("GROQ_API_KEY")
        self.model = model

    def _get_headers(self) -> dict:
        """Get authorization headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        json_mode: bool = False,
        model: str = None,
    ) -> Dict[str, Any]:
        """
        Send a chat completion request.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            json_mode: If True, response will be valid JSON
            model: Override default model

        Returns:
            Full API response dict
        """
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
            timeout=30,
        )

        if not resp.ok:
            raise Exception(f"Groq API error: {resp.status_code} {resp.text}")

        return resp.json()

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        json_mode: bool = False,
        model: str = None,
    ) -> str:
        """
        Simple completion with system and user prompts.

        Args:
            system_prompt: System message
            user_prompt: User message
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            json_mode: If True, response will be valid JSON
            model: Override default model

        Returns:
            Generated text content
        """
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
        max_tokens: int = 1024,
        model: str = None,
    ) -> Dict[str, Any]:
        """
        Completion that returns parsed JSON.

        Args:
            system_prompt: System message
            user_prompt: User message
            temperature: Sampling temperature (lower for JSON)
            max_tokens: Maximum tokens
            model: Override default model

        Returns:
            Parsed JSON response
        """
        content = self.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True,
            model=model,
        )

        # Clean markdown code blocks if present
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        return json.loads(content)
