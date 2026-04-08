"""
Layer 1 — PII detection.

Regex-based detection of personally identifiable information.
Zero-cost: no external calls, no LLM, no database queries.
Runs on every request.

Interview talking points:
- Why regex over NER? Speed and determinism. NER models add latency and
  can produce false negatives on names not in training data. Regex catches
  the high-impact patterns (emails, phones, NI numbers) reliably.
- Why UK-specific patterns (NI numbers)? Because the workshop is built
  for a UK audience. In production you'd add country-specific patterns
  for each market you serve.
- What does this NOT catch? Names, addresses without postcodes, free-form
  PII. For comprehensive PII detection you'd combine regex with NER and
  an LLM-based check. We layer those in Layer 3 if needed.
"""

import re
from dataclasses import dataclass


@dataclass
class PIIMatch:
    """A single PII detection."""

    type: str
    value: str
    start: int
    end: int

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "value": self.value,
            "start": self.start,
            "end": self.end,
        }


# PII patterns — ordered by specificity
PII_PATTERNS: dict[str, re.Pattern[str]] = {
    "email": re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    ),
    "phone_uk": re.compile(
        # UK mobile (07xxx xxxxxx) and landline (+44 or 0xxxx)
        r"(?:\+44|0)\s?\d{2,4}[\s-]?\d{3,4}[\s-]?\d{3,4}\b"
    ),
    "phone_intl": re.compile(
        # International format: +X XXX XXX XXXX
        r"\+\d{1,3}[\s-]?\(?\d{1,4}\)?[\s-]?\d{3,4}[\s-]?\d{3,4}"
    ),
    "ni_number": re.compile(
        # UK National Insurance number: 2 letters, 6 digits, 1 letter
        r"\b[A-CEGHJ-PR-TW-Z][A-CEGHJ-NPR-TW-Z]\s?\d{2}\s?\d{2}\s?\d{2}\s?[A-D]\b"
    ),
    "uk_postcode": re.compile(
        # UK postcodes: SW1A 1AA, M1 1AE, etc.
        r"\b[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}\b"
    ),
    "credit_card": re.compile(
        # Loose 13-19 digit pattern with optional separators
        r"\b(?:\d[ -]?){13,19}\b"
    ),
}


def detect_pii(text: str) -> list[PIIMatch]:
    """Scan text for PII patterns and return all matches.

    Returns:
        List of PIIMatch objects with type, value, and position.
        Empty list if no PII found.
    """
    matches: list[PIIMatch] = []
    for pii_type, pattern in PII_PATTERNS.items():
        for m in pattern.finditer(text):
            matches.append(PIIMatch(
                type=pii_type,
                value=m.group(),
                start=m.start(),
                end=m.end(),
            ))
    # Sort by position
    matches.sort(key=lambda m: m.start)
    return matches


def has_pii(text: str) -> bool:
    """Quick boolean check for PII presence."""
    return len(detect_pii(text)) > 0


def redact_pii(text: str, replacement: str = "[REDACTED]") -> str:
    """Replace all detected PII in text with a placeholder.

    Useful for logging or sending text to less-trusted contexts.
    """
    matches = detect_pii(text)
    if not matches:
        return text

    # Replace from end to start to preserve positions
    result = text
    for match in reversed(matches):
        result = result[: match.start] + replacement + result[match.end :]
    return result
