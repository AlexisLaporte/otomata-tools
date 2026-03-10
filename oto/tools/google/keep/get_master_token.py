#!/usr/bin/env python3
"""Get Google Keep master token via browser OAuth flow.

Opens a browser for Google login, extracts the oauth_token cookie,
then exchanges it for a master token via gpsoauth.
"""

import asyncio
import sys

import gpsoauth
import typer
from typing_extensions import Annotated

app = typer.Typer(help="Get Google Keep master token")

EMBEDDED_SETUP_URL = "https://accounts.google.com/EmbeddedSetup"


async def _get_oauth_token() -> str:
    """Open browser, let user login, extract oauth_token cookie."""
    from patchright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, channel="chrome")
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(EMBEDDED_SETUP_URL)

        print("Log in to your Google account in the browser window.", file=sys.stderr)
        print("Click 'I agree' when prompted, then wait...", file=sys.stderr)

        # Wait for the oauth_token cookie to appear
        oauth_token = None
        while oauth_token is None:
            cookies = await context.cookies("https://accounts.google.com")
            for cookie in cookies:
                if cookie["name"] == "oauth_token":
                    oauth_token = cookie["value"]
                    break
            if oauth_token is None:
                await page.wait_for_timeout(1000)

        await browser.close()

    return oauth_token


def _exchange_token(email: str, oauth_token: str, android_id: str = "0123456789abcdef") -> str:
    """Exchange oauth_token for a master token."""
    result = gpsoauth.exchange_token(email, oauth_token, android_id)
    token = result.get("Token")
    if not token:
        error = result.get("Error", "Unknown error")
        print(f"Token exchange failed: {error}", file=sys.stderr)
        print(f"Full response: {result}", file=sys.stderr)
        raise typer.Exit(1)
    return token


@app.command()
def main(
    email: Annotated[str, typer.Option(help="Google account email")],
    save: Annotated[bool, typer.Option(help="Save to ~/.otomata/secrets.env")] = False,
):
    """Get a Google master token for Keep API access.

    Opens a browser for login, then exchanges the OAuth cookie for a master token.
    """
    oauth_token = asyncio.run(_get_oauth_token())
    print("Got OAuth token from browser, exchanging for master token...", file=sys.stderr)

    master_token = _exchange_token(email, oauth_token)

    if save:
        from oto.config import get_config_dir
        secrets_file = get_config_dir() / "secrets.env"
        lines = secrets_file.read_text().splitlines() if secrets_file.exists() else []

        # Update or append each key
        for key, value in [("GOOGLE_KEEP_EMAIL", email), ("GOOGLE_KEEP_MASTER_TOKEN", master_token)]:
            found = False
            for i, line in enumerate(lines):
                if line.startswith(f"{key}="):
                    lines[i] = f"{key}={value}"
                    found = True
                    break
            if not found:
                lines.append(f"{key}={value}")

        secrets_file.write_text("\n".join(lines) + "\n")
        print(f"Saved to {secrets_file}", file=sys.stderr)
    else:
        print(f"\nGOOGLE_KEEP_EMAIL={email}")
        print(f"GOOGLE_KEEP_MASTER_TOKEN={master_token}")
        print("\nAdd these to ~/.otomata/secrets.env", file=sys.stderr)


if __name__ == "__main__":
    app()
