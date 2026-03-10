"""INSEE Sirene API client for French company data."""

from pathlib import Path
from typing import Dict

from .client import SireneClient, EMPLOYEE_RANGES
from .entreprises import EntreprisesClient
from .stock import SireneStock


def load_naf_codes() -> Dict[str, str]:
    """
    Load NAF codes from data file.

    Returns:
        Dict mapping code to label (e.g., {'62.01Z': 'Programmation informatique'})
    """
    naf_file = Path(__file__).parent / "data" / "naf_codes.txt"
    codes = {}
    if naf_file.exists():
        for line in naf_file.read_text().splitlines():
            if ": " in line:
                code, label = line.strip().split(": ", 1)
                codes[code] = label
    return codes


__all__ = [
    "SireneClient",
    "EntreprisesClient",
    "SireneStock",
    "EMPLOYEE_RANGES",
    "load_naf_codes",
]
