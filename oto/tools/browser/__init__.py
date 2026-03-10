"""
Browser automation tools.

BrowserClient comes from o-browser package.
Domain-specific clients (LinkedIn, Crunchbase...) live here.
"""

from o_browser import BrowserClient
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
