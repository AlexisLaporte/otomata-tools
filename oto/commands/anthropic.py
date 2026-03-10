"""Anthropic Admin API commands (usage & cost tracking)."""

import typer
from typing import Optional

app = typer.Typer(help="Anthropic Admin API (usage & cost tracking)")


@app.command("usage")
def usage(
    days: int = typer.Option(7, "--days", "-d", help="Number of days to look back"),
    bucket: str = typer.Option("1d", "--bucket", "-b", help="Bucket width: 1m, 1h, 1d"),
    group_by: Optional[str] = typer.Option("model", "--group-by", "-g", help="Group by: model, api_key_id, workspace_id, service_tier"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Filter to specific model"),
):
    """Get token usage report."""
    import json
    from oto.tools.anthropic import AnthropicAdminClient

    client = AnthropicAdminClient()
    groups = [g.strip() for g in group_by.split(",")] if group_by else None
    models = [model] if model else None
    data = client.get_usage(bucket_width=bucket, group_by=groups, models=models,
                            limit=days if bucket == "1d" else None)
    print(json.dumps(data, indent=2, ensure_ascii=False))


@app.command("cost")
def cost(
    days: int = typer.Option(30, "--days", "-d", help="Number of days to look back"),
    group_by: Optional[str] = typer.Option(None, "--group-by", "-g", help="Group by: workspace_id, description"),
):
    """Get cost report (daily, USD)."""
    import json
    from oto.tools.anthropic import AnthropicAdminClient

    client = AnthropicAdminClient()
    groups = [g.strip() for g in group_by.split(",")] if group_by else None
    data = client.get_costs(group_by=groups)
    print(json.dumps(data, indent=2, ensure_ascii=False))


@app.command("summary")
def summary(
    days: int = typer.Option(7, "--days", "-d", help="Number of days to look back"),
):
    """Daily usage summary with estimated costs by model."""
    import json
    from oto.tools.anthropic import AnthropicAdminClient

    client = AnthropicAdminClient()
    result = client.get_daily_summary(days=days)
    print(json.dumps(result, indent=2, ensure_ascii=False))


@app.command("today")
def today():
    """Today's usage and estimated cost."""
    import json
    from oto.tools.anthropic import AnthropicAdminClient

    client = AnthropicAdminClient()
    result = client.get_today_cost()
    print(json.dumps(result, indent=2, ensure_ascii=False))
