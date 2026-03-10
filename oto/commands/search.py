"""Search commands (web and news via Serper)."""

import typer
from typing import Optional

app = typer.Typer(help="Web and news search (Serper)")


@app.command("web")
def web(
    query: str = typer.Option(..., "--query", "-q", help="Search query"),
    num: int = typer.Option(10, "--num", "-n", help="Number of results"),
    tbs: Optional[str] = typer.Option(None, help="Time filter (e.g. qdr:y)"),
):
    """Search the web via Serper (Google)."""
    import json
    from oto.tools.serper import SerperClient

    client = SerperClient()
    result = client.search(query, num=num, tbs=tbs)
    print(json.dumps(result, indent=2, ensure_ascii=False))


@app.command("news")
def news(
    query: str = typer.Option(..., "--query", "-q", help="Search query"),
    num: int = typer.Option(10, "--num", "-n", help="Number of results"),
    tbs: Optional[str] = typer.Option(None, help="Time filter (e.g. qdr:y)"),
):
    """Search news via Serper (Google News)."""
    import json
    from oto.tools.serper import SerperClient

    client = SerperClient()
    result = client.search_news(query, num=num, tbs=tbs)
    print(json.dumps(result, indent=2, ensure_ascii=False))
