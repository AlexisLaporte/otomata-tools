"""
Anthropic Batch API Client.

Requires: anthropic

Supports batch processing of messages with:
- Prompt templates
- Progress monitoring
- Result parsing
"""

import json
import time
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple

import anthropic

from ...config import require_secret


class AnthropicBatchClient:
    """
    Anthropic Batch API client for high-throughput processing.

    Usage:
        client = AnthropicBatchClient()

        # Prepare requests from data
        requests = client.prepare_requests(
            items=[{"id": "1", "text": "..."}, ...],
            system_prompt="You are a classifier.",
            user_template="Analyze: {data}"
        )

        # Submit and wait
        results = client.run_batch(requests)
    """

    DEFAULT_MODEL = "claude-sonnet-4-20250514"

    def __init__(self, api_key: str = None):
        """
        Initialize Anthropic Batch client.

        Args:
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or require_secret("ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def parse_prompt_file(self, prompt_path: str) -> Tuple[str, str]:
        """
        Parse prompt file into system and user template.

        Format:
            SYSTEM: System prompt here
            User message template with {data} placeholder

        Args:
            prompt_path: Path to prompt file

        Returns:
            Tuple of (system_prompt, user_template)
        """
        with open(prompt_path) as f:
            content = f.read()

        lines = content.split("\n")
        system_prompt = ""
        user_lines = []

        for i, line in enumerate(lines):
            if line.startswith("SYSTEM:"):
                system_prompt = line[7:].strip()
                # Check if system prompt continues on next lines (indented)
                for j in range(i + 1, len(lines)):
                    if lines[j].startswith("  ") or lines[j].startswith("\t"):
                        system_prompt += "\n" + lines[j].strip()
                    else:
                        user_lines = lines[j:]
                        break
                break
        else:
            user_lines = lines

        user_template = "\n".join(user_lines).strip()
        return system_prompt, user_template

    def prepare_requests(
        self,
        items: List[Dict],
        system_prompt: str = None,
        user_template: str = "{data}",
        model: str = None,
        max_tokens: int = 500,
    ) -> List[Dict]:
        """
        Prepare batch requests from items.

        Args:
            items: List of items with optional 'id' field
            system_prompt: System prompt
            user_template: User message template with {data} placeholder
            model: Model to use
            max_tokens: Max response tokens

        Returns:
            List of batch request objects
        """
        model = model or self.DEFAULT_MODEL
        requests = []

        for i, item in enumerate(items):
            custom_id = str(item.get("id", f"item_{i}"))

            # Format user message
            if "{data}" in user_template:
                user_content = user_template.replace(
                    "{data}", json.dumps(item, ensure_ascii=False, indent=2)
                )
            else:
                user_content = user_template + "\n\n" + json.dumps(item, ensure_ascii=False, indent=2)

            request = {
                "custom_id": custom_id,
                "params": {
                    "model": model,
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": user_content}]
                }
            }
            if system_prompt:
                request["params"]["system"] = system_prompt

            requests.append(request)

        return requests

    def prepare_from_file(
        self,
        input_file: str,
        prompt_file: str,
        model: str = None,
        max_tokens: int = 500,
    ) -> List[Dict]:
        """
        Prepare batch requests from input JSON and prompt file.

        Args:
            input_file: Path to input JSON (with 'items', 'profiles', or list)
            prompt_file: Path to prompt template file
            model: Model to use
            max_tokens: Max response tokens

        Returns:
            List of batch request objects
        """
        # Load input
        with open(input_file) as f:
            data = json.load(f)

        items = data.get("items", data.get("profiles", data.get("attendees", data)))
        if isinstance(items, dict):
            items = list(items.values())

        # Parse prompt
        system_prompt, user_template = self.parse_prompt_file(prompt_file)

        return self.prepare_requests(
            items=items,
            system_prompt=system_prompt,
            user_template=user_template,
            model=model,
            max_tokens=max_tokens,
        )

    def submit(self, requests: List[Dict]) -> str:
        """
        Submit batch to Anthropic API.

        Args:
            requests: List of batch request objects

        Returns:
            Batch ID
        """
        batch = self.client.messages.batches.create(requests=requests)
        return batch.id

    def get_status(self, batch_id: str) -> Dict[str, Any]:
        """
        Check batch status.

        Args:
            batch_id: Batch ID

        Returns:
            Status dict with 'status', 'succeeded', 'errored', 'total'
        """
        batch = self.client.messages.batches.retrieve(batch_id)
        rc = batch.request_counts
        total = rc.processing + rc.succeeded + rc.errored + rc.canceled + rc.expired

        return {
            "batch_id": batch.id,
            "status": batch.processing_status,
            "succeeded": rc.succeeded,
            "errored": rc.errored,
            "processing": rc.processing,
            "total": total,
            "completed": batch.processing_status == "ended",
        }

    def wait_for_completion(
        self,
        batch_id: str,
        poll_interval: int = 10,
        callback: callable = None,
    ) -> Dict[str, Any]:
        """
        Wait for batch to complete.

        Args:
            batch_id: Batch ID
            poll_interval: Seconds between status checks
            callback: Optional callback(status_dict) called each poll

        Returns:
            Final status dict
        """
        while True:
            status = self.get_status(batch_id)
            if callback:
                callback(status)
            if status["completed"]:
                return status
            time.sleep(poll_interval)

    def download_results(self, batch_id: str) -> List[Dict]:
        """
        Download batch results.

        Args:
            batch_id: Batch ID

        Returns:
            List of result dicts with 'id', 'success', 'response', 'parsed'
        """
        results = []

        for result in self.client.messages.batches.results(batch_id):
            item = {
                "id": result.custom_id,
                "success": result.result.type == "succeeded"
            }

            if result.result.type == "succeeded":
                text = result.result.message.content[0].text
                item["response"] = text
                # Try to parse JSON
                if "{" in text:
                    try:
                        item["parsed"] = json.loads(
                            text[text.index("{"):text.rindex("}") + 1]
                        )
                    except (json.JSONDecodeError, ValueError):
                        pass
            else:
                item["error"] = str(result.result)

            results.append(item)

        return results

    def run_batch(
        self,
        requests: List[Dict],
        poll_interval: int = 10,
        progress_callback: callable = None,
    ) -> List[Dict]:
        """
        Submit batch, wait for completion, and download results.

        Args:
            requests: List of batch request objects
            poll_interval: Seconds between status checks
            progress_callback: Optional callback(status_dict)

        Returns:
            List of result dicts
        """
        batch_id = self.submit(requests)
        self.wait_for_completion(batch_id, poll_interval, progress_callback)
        return self.download_results(batch_id)

    def run_from_file(
        self,
        input_file: str,
        prompt_file: str,
        output_file: str = None,
        model: str = None,
        max_tokens: int = 500,
        poll_interval: int = 10,
    ) -> Dict[str, Any]:
        """
        All-in-one: prepare from files, submit, wait, download.

        Args:
            input_file: Path to input JSON
            prompt_file: Path to prompt template file
            output_file: Optional path to save results
            model: Model to use
            max_tokens: Max response tokens
            poll_interval: Seconds between status checks

        Returns:
            Dict with 'results', 'count', 'batch_id'
        """
        requests = self.prepare_from_file(input_file, prompt_file, model, max_tokens)
        batch_id = self.submit(requests)
        self.wait_for_completion(batch_id, poll_interval)
        results = self.download_results(batch_id)

        output = {
            "results": results,
            "count": len(results),
            "batch_id": batch_id,
            "succeeded": sum(1 for r in results if r["success"]),
        }

        if output_file:
            with open(output_file, "w") as f:
                json.dump(output, f, indent=2, ensure_ascii=False)

        return output

    def save_requests_jsonl(self, requests: List[Dict], output_file: str):
        """Save requests to JSONL file."""
        with open(output_file, "w") as f:
            for req in requests:
                f.write(json.dumps(req) + "\n")

    def load_requests_jsonl(self, input_file: str) -> List[Dict]:
        """Load requests from JSONL file."""
        requests = []
        with open(input_file) as f:
            for line in f:
                if line.strip():
                    requests.append(json.loads(line))
        return requests
