"""
Browser automation tools using Patchright (undetectable Playwright).

All browser clients inherit from BrowserClient for consistent:
- Session management (profile or cookie-based)
- Browser lifecycle
- Navigation and interaction helpers
"""

from .lib.browser_client import BrowserClient
from .linkedin import LinkedInClient
from .crunchbase import CrunchbaseClient
from .pappers import PappersClient
from .g2 import G2Client
from .indeed import IndeedClient

__all__ = [
    "BrowserClient",
    "LinkedInClient",
    "CrunchbaseClient",
    "PappersClient",
    "G2Client",
    "IndeedClient",
]
