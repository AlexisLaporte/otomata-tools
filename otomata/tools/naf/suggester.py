"""
NAF code suggestion using Groq AI.

Suggests appropriate NAF codes from activity descriptions.
"""

from dataclasses import dataclass
from typing import List, Optional

from ..groq import GroqClient
from ..sirene import load_naf_codes


@dataclass
class NAFSuggestion:
    """A suggested NAF code with confidence and reasoning."""

    code: str
    label: str
    confidence: float
    reason: str


class NAFSuggester:
    """
    Suggest NAF codes from activity descriptions using AI.

    Uses Groq for fast inference with validation against
    the official 732 NAF codes list.
    """

    def __init__(self, groq_client: GroqClient = None):
        """
        Initialize NAF suggester.

        Args:
            groq_client: Optional GroqClient instance (creates one if not provided)
        """
        self.groq = groq_client or GroqClient()
        self._naf_codes = None

    @property
    def naf_codes(self) -> dict:
        """Lazy load NAF codes."""
        if self._naf_codes is None:
            self._naf_codes = load_naf_codes()
        return self._naf_codes

    def _get_sections_overview(self) -> str:
        """Build compact section overview for prompt."""
        sections = {}
        for code, label in self.naf_codes.items():
            section = code[:2]
            if section not in sections:
                sections[section] = []
            if len(sections[section]) < 3:
                sections[section].append(f"{code}: {label}")

        lines = []
        for section in sorted(sections.keys()):
            examples = sections[section]
            lines.append(f"Section {section}: {', '.join(examples)}")

        return "\n".join(lines)

    def suggest(
        self,
        description: str,
        limit: int = 3,
        temperature: float = 0.3,
    ) -> List[NAFSuggestion]:
        """
        Suggest NAF codes for an activity description.

        Args:
            description: Activity description in French
            limit: Maximum number of suggestions (1-5)
            temperature: Model temperature (lower = more deterministic)

        Returns:
            List of NAFSuggestion objects, sorted by confidence
        """
        if not description or not description.strip():
            return []

        sections_text = self._get_sections_overview()

        system_prompt = (
            "Tu es un expert en classification NAF française. "
            "Réponds uniquement en JSON valide. "
            "Utilise UNIQUEMENT les codes exacts de la liste fournie."
        )

        user_prompt = f"""Codes NAF par section (exemples):
{sections_text}

Activité: "{description}"

Choisis 1-{limit} codes NAF EXACTS de la liste. Réponds en JSON:
{{"suggestions": [{{"code": "XX.XXZ", "label": "description", "confidence": 0.9, "reason": "pourquoi"}}]}}"""

        try:
            result = self.groq.complete_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                max_tokens=500,
            )

            suggestions = []
            for s in result.get("suggestions", []):
                code = s.get("code", "")
                # Validate against official codes
                if code in self.naf_codes:
                    suggestions.append(
                        NAFSuggestion(
                            code=code,
                            label=self.naf_codes[code],
                            confidence=float(s.get("confidence", 0.5)),
                            reason=s.get("reason", ""),
                        )
                    )

            return sorted(suggestions, key=lambda x: -x.confidence)[:limit]

        except Exception as e:
            # Return empty on error rather than crashing
            return []

    def validate_code(self, code: str) -> Optional[str]:
        """
        Validate a NAF code.

        Args:
            code: NAF code to validate

        Returns:
            Label if valid, None if invalid
        """
        return self.naf_codes.get(code)
