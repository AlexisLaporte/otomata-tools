"""
Anthropic Admin API client for usage and cost tracking.

Requires: requests

Authentication:
    ANTHROPIC_ADMIN_API_KEY: Admin API key (sk-ant-admin-...) from
    https://console.anthropic.com/settings/admin-keys
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any

import requests

from ...config import require_secret

# Pricing per million tokens (USD) — updated 2026-02
MODEL_PRICING = {
    "claude-opus-4-6":             {"input": 15.0,  "output": 75.0},
    "claude-sonnet-4-5-20250929":  {"input": 3.0,   "output": 15.0},
    "claude-sonnet-4-20250514":    {"input": 3.0,   "output": 15.0},
    "claude-haiku-4-5-20251001":   {"input": 0.80,  "output": 4.0},
    "claude-3-5-sonnet-20241022":  {"input": 3.0,   "output": 15.0},
    "claude-3-5-haiku-20241022":   {"input": 0.80,  "output": 4.0},
    "claude-3-opus-20240229":      {"input": 15.0,  "output": 75.0},
    "claude-3-sonnet-20240229":    {"input": 3.0,   "output": 15.0},
    "claude-3-haiku-20240307":     {"input": 0.25,  "output": 1.25},
}

# Cache pricing: write = 1.25x input, read = 0.1x input
CACHE_WRITE_MULTIPLIER = 1.25
CACHE_READ_MULTIPLIER = 0.10


def _get_model_pricing(model: str) -> dict:
    """Get pricing for a model, with fallback heuristic."""
    if model in MODEL_PRICING:
        return MODEL_PRICING[model]
    lower = model.lower()
    if "opus" in lower:
        return {"input": 15.0, "output": 75.0}
    if "haiku" in lower:
        return {"input": 0.80, "output": 4.0}
    # Default to sonnet
    return {"input": 3.0, "output": 15.0}


def _estimate_cost(model: str, input_tokens: int, output_tokens: int,
                   cache_read_tokens: int = 0, cache_create_tokens: int = 0) -> float:
    """Estimate cost in USD for a given token usage."""
    p = _get_model_pricing(model)
    input_price = p["input"]
    output_price = p["output"]

    cost = (
        input_tokens * input_price
        + output_tokens * output_price
        + cache_read_tokens * input_price * CACHE_READ_MULTIPLIER
        + cache_create_tokens * input_price * CACHE_WRITE_MULTIPLIER
    ) / 1_000_000
    return cost


class AnthropicAdminClient:
    """
    Anthropic Admin API client for usage and cost tracking.

    Provides access to:
    - Token usage reports (by model, workspace, API key)
    - Cost reports (daily, by workspace)
    - Local cost estimation from token counts
    """

    BASE_URL = "https://api.anthropic.com/v1/organizations"

    def __init__(self, api_key: str = None):
        """
        Initialize client.

        Args:
            api_key: Admin API key (sk-ant-admin-...). Defaults to
                     ANTHROPIC_ADMIN_API_KEY env var.
        """
        self.api_key = api_key or require_secret("ANTHROPIC_ADMIN_API_KEY")

    def _headers(self) -> dict:
        return {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

    def _get(self, path: str, params: dict = None) -> dict:
        """Make a GET request with pagination support."""
        resp = requests.get(
            f"{self.BASE_URL}{path}",
            headers=self._headers(),
            params=params,
            timeout=30,
        )
        if not resp.ok:
            raise Exception(f"Anthropic Admin API error: {resp.status_code} {resp.text}")
        return resp.json()

    def _get_all(self, path: str, params: dict = None) -> list:
        """Paginate through all results, merging data arrays."""
        params = dict(params or {})
        all_data = []
        while True:
            result = self._get(path, params)
            all_data.extend(result.get("data", []))
            if not result.get("has_more"):
                break
            params["page"] = result["next_page"]
        return all_data

    # ── Usage API ──────────────────────────────────────────────

    def get_usage(
        self,
        starting_at: str = None,
        ending_at: str = None,
        bucket_width: str = "1d",
        group_by: List[str] = None,
        models: List[str] = None,
        api_key_ids: List[str] = None,
        workspace_ids: List[str] = None,
        limit: int = None,
    ) -> list:
        """
        Get token usage report.

        Args:
            starting_at: Start time ISO8601 (default: 7 days ago)
            ending_at: End time ISO8601 (default: now)
            bucket_width: Aggregation: '1m', '1h', or '1d'
            group_by: Dimensions to group by: 'model', 'api_key_id',
                      'workspace_id', 'service_tier', 'context_window', 'inference_geo'
            models: Filter to specific models
            api_key_ids: Filter to specific API keys
            workspace_ids: Filter to specific workspaces
            limit: Max buckets to return

        Returns:
            List of usage data buckets
        """
        now = datetime.now(timezone.utc)
        if not starting_at:
            starting_at = (now - timedelta(days=7)).strftime("%Y-%m-%dT00:00:00Z")
        if not ending_at:
            ending_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")

        params = {
            "starting_at": starting_at,
            "ending_at": ending_at,
            "bucket_width": bucket_width,
        }
        if group_by:
            for g in group_by:
                params.setdefault("group_by[]", []).append(g)
        if models:
            for m in models:
                params.setdefault("models[]", []).append(m)
        if api_key_ids:
            for k in api_key_ids:
                params.setdefault("api_key_ids[]", []).append(k)
        if workspace_ids:
            for w in workspace_ids:
                params.setdefault("workspace_ids[]", []).append(w)
        if limit:
            params["limit"] = limit

        return self._get_all("/usage_report/messages", params)

    # ── Cost API ───────────────────────────────────────────────

    def get_costs(
        self,
        starting_at: str = None,
        ending_at: str = None,
        group_by: List[str] = None,
        workspace_ids: List[str] = None,
    ) -> list:
        """
        Get cost report (daily granularity, USD).

        Args:
            starting_at: Start time ISO8601 (default: 30 days ago)
            ending_at: End time ISO8601 (default: now)
            group_by: Dimensions: 'workspace_id', 'description'
            workspace_ids: Filter to specific workspaces

        Returns:
            List of cost data buckets
        """
        now = datetime.now(timezone.utc)
        if not starting_at:
            starting_at = (now - timedelta(days=30)).strftime("%Y-%m-%dT00:00:00Z")
        if not ending_at:
            ending_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")

        params = {
            "starting_at": starting_at,
            "ending_at": ending_at,
        }
        if group_by:
            for g in group_by:
                params.setdefault("group_by[]", []).append(g)
        if workspace_ids:
            for w in workspace_ids:
                params.setdefault("workspace_ids[]", []).append(w)

        return self._get_all("/cost_report", params)

    # ── Convenience methods ────────────────────────────────────

    def get_daily_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Get a daily summary with usage and estimated costs by model.

        Args:
            days: Number of days to look back

        Returns:
            Dict with daily breakdown and totals
        """
        now = datetime.now(timezone.utc)
        starting_at = (now - timedelta(days=days)).strftime("%Y-%m-%dT00:00:00Z")
        ending_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")

        data = self.get_usage(
            starting_at=starting_at,
            ending_at=ending_at,
            bucket_width="1d",
            group_by=["model"],
        )

        totals = {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_read_tokens": 0,
            "cache_create_tokens": 0,
            "estimated_cost_usd": 0.0,
        }
        by_model = {}
        daily = []

        for bucket in data:
            model = bucket.get("model", "unknown")
            inp = bucket.get("input_tokens", 0)
            out = bucket.get("output_tokens", 0)
            cache_read = bucket.get("input_cached_tokens", 0)
            cache_create = bucket.get("input_cache_creation_tokens", 0)
            cost = _estimate_cost(model, inp, out, cache_read, cache_create)

            totals["input_tokens"] += inp
            totals["output_tokens"] += out
            totals["cache_read_tokens"] += cache_read
            totals["cache_create_tokens"] += cache_create
            totals["estimated_cost_usd"] += cost

            by_model.setdefault(model, {
                "input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0,
            })
            by_model[model]["input_tokens"] += inp
            by_model[model]["output_tokens"] += out
            by_model[model]["estimated_cost_usd"] += cost

            daily.append({
                "date": bucket.get("bucket_start_time", ""),
                "model": model,
                "input_tokens": inp,
                "output_tokens": out,
                "cache_read_tokens": cache_read,
                "cache_create_tokens": cache_create,
                "estimated_cost_usd": round(cost, 6),
            })

        totals["estimated_cost_usd"] = round(totals["estimated_cost_usd"], 4)
        for m in by_model.values():
            m["estimated_cost_usd"] = round(m["estimated_cost_usd"], 4)

        return {
            "period": {"start": starting_at, "end": ending_at, "days": days},
            "totals": totals,
            "by_model": by_model,
            "daily": daily,
        }

    def get_today_cost(self) -> Dict[str, Any]:
        """Get today's usage and estimated cost."""
        now = datetime.now(timezone.utc)
        starting_at = now.strftime("%Y-%m-%dT00:00:00Z")
        ending_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")

        data = self.get_usage(
            starting_at=starting_at,
            ending_at=ending_at,
            bucket_width="1h",
            group_by=["model"],
        )

        total_cost = 0.0
        total_input = 0
        total_output = 0
        by_model = {}

        for bucket in data:
            model = bucket.get("model", "unknown")
            inp = bucket.get("input_tokens", 0)
            out = bucket.get("output_tokens", 0)
            cache_read = bucket.get("input_cached_tokens", 0)
            cache_create = bucket.get("input_cache_creation_tokens", 0)
            cost = _estimate_cost(model, inp, out, cache_read, cache_create)

            total_cost += cost
            total_input += inp
            total_output += out

            by_model.setdefault(model, {"input_tokens": 0, "output_tokens": 0, "cost": 0.0})
            by_model[model]["input_tokens"] += inp
            by_model[model]["output_tokens"] += out
            by_model[model]["cost"] += cost

        for m in by_model.values():
            m["cost"] = round(m["cost"], 4)

        return {
            "date": now.strftime("%Y-%m-%d"),
            "input_tokens": total_input,
            "output_tokens": total_output,
            "estimated_cost_usd": round(total_cost, 4),
            "by_model": by_model,
        }

    @staticmethod
    def estimate_cost(model: str, input_tokens: int, output_tokens: int,
                      cache_read_tokens: int = 0, cache_create_tokens: int = 0) -> float:
        """
        Estimate cost in USD for given token counts (no API call needed).

        Args:
            model: Model name (e.g. 'claude-sonnet-4-5-20250929')
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cache_read_tokens: Cached input tokens read
            cache_create_tokens: Cache creation tokens

        Returns:
            Estimated cost in USD
        """
        return _estimate_cost(model, input_tokens, output_tokens,
                              cache_read_tokens, cache_create_tokens)
