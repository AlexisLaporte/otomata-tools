"""
Logo search utilities using Clearbit-style APIs.

No API key required - uses public logo endpoints.
"""

import re
import urllib.request
from pathlib import Path
from typing import Dict, Any


def extract_domain(company_name: str) -> str:
    """
    Convert company name to likely domain.

    Examples:
        "Google" -> "google.com"
        "Microsoft" -> "microsoft.com"
        "Apple Inc." -> "apple.com"
    """
    company = company_name.lower()

    # Remove common suffixes
    suffixes = [
        " inc.", " inc", " corp.", " corp", " ltd.", " ltd",
        " llc", " plc", " sa", " gmbh", " ag", " nv", " bv"
    ]
    for suffix in suffixes:
        company = company.replace(suffix, "")

    # Remove special characters
    company = re.sub(r"[^\w\s-]", "", company)

    # Take first word
    company = company.strip().split()[0]

    return f"{company}.com"


def download_logo(
    domain: str,
    output_dir: str = None,
    size: int = 128,
) -> Dict[str, Any]:
    """
    Download company logo using multiple fallback sources.

    Args:
        domain: Company domain (e.g., "google.com")
        output_dir: Directory to save logo (default: current directory)
        size: Logo size in pixels (default: 128)

    Returns:
        Dict with status, image_path, filename, domain, source
    """
    # Logo sources in order of preference
    logo_sources = [
        {
            "name": "Logo.dev",
            "url": f"https://img.logo.dev/{domain}?token=pk_X-WvJk3RQQmflwLyTMHA3w&size={size}",
        },
        {
            "name": "Google Favicon",
            "url": f"https://www.google.com/s2/favicons?domain={domain}&sz={size}",
        },
        {
            "name": "Clearbit",
            "url": f"https://logo.clearbit.com/{domain}?size={size}",
        }
    ]

    # Determine output path
    if output_dir:
        output_path = Path(output_dir)
    else:
        output_path = Path.cwd()
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate filename
    company_name = domain.replace(".com", "").replace(".", "_")
    filename = f"logo_{company_name}_{size}px.png"
    file_path = output_path / filename

    # Try each source
    last_error = None
    for source in logo_sources:
        try:
            req = urllib.request.Request(
                source["url"],
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                logo_data = response.read()

                # Check for valid data
                if len(logo_data) < 100:
                    continue

            # Save logo
            with open(file_path, "wb") as f:
                f.write(logo_data)

            return {
                "status": "success",
                "image_path": str(file_path.absolute()),
                "filename": filename,
                "domain": domain,
                "size": size,
                "source": source["name"],
                "url": source["url"]
            }

        except Exception as e:
            last_error = f"{source['name']}: {str(e)}"
            continue

    # All sources failed
    return {
        "status": "error",
        "error": f"All sources failed. Last error: {last_error}",
        "domain": domain
    }
