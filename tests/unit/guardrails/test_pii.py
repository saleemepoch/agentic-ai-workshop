"""
Unit tests for PII detection (Layer 1).

Pure regex tests — no external dependencies.
"""

import pytest

from src.guardrails.pii import detect_pii, has_pii, redact_pii


class TestEmailDetection:
    def test_simple_email(self) -> None:
        matches = detect_pii("Contact me at john.doe@example.com")
        assert len(matches) == 1
        assert matches[0].type == "email"
        assert matches[0].value == "john.doe@example.com"

    def test_multiple_emails(self) -> None:
        text = "Email a@b.com or c.d@example.co.uk for help."
        matches = detect_pii(text)
        emails = [m for m in matches if m.type == "email"]
        assert len(emails) == 2

    def test_no_email(self) -> None:
        matches = detect_pii("Contact me through the form")
        emails = [m for m in matches if m.type == "email"]
        assert len(emails) == 0


class TestPhoneDetection:
    def test_uk_mobile(self) -> None:
        matches = detect_pii("Call me on 07700 900123")
        phones = [m for m in matches if "phone" in m.type]
        assert len(phones) >= 1

    def test_uk_landline_with_country_code(self) -> None:
        matches = detect_pii("Phone: +44 20 7946 0958")
        phones = [m for m in matches if "phone" in m.type]
        assert len(phones) >= 1


class TestNINumberDetection:
    def test_valid_ni_number(self) -> None:
        matches = detect_pii("My NI number is AB 12 34 56 C")
        ni = [m for m in matches if m.type == "ni_number"]
        assert len(ni) == 1

    def test_no_spaces(self) -> None:
        matches = detect_pii("NI: AB123456C")
        ni = [m for m in matches if m.type == "ni_number"]
        assert len(ni) == 1


class TestUKPostcodeDetection:
    def test_london_postcode(self) -> None:
        matches = detect_pii("I live in SW1A 1AA")
        postcodes = [m for m in matches if m.type == "uk_postcode"]
        assert len(postcodes) == 1

    def test_short_postcode(self) -> None:
        matches = detect_pii("Office at M1 1AE")
        postcodes = [m for m in matches if m.type == "uk_postcode"]
        assert len(postcodes) == 1


class TestHasPII:
    def test_clean_text(self) -> None:
        assert has_pii("This is a clean message with no personal data") is False

    def test_dirty_text(self) -> None:
        assert has_pii("Email me at test@example.com") is True


class TestRedactPII:
    def test_redacts_email(self) -> None:
        text = "Contact john@example.com for help"
        result = redact_pii(text)
        assert "john@example.com" not in result
        assert "[REDACTED]" in result

    def test_clean_text_unchanged(self) -> None:
        text = "No PII here"
        assert redact_pii(text) == text

    def test_multiple_pii_redacted(self) -> None:
        text = "Email john@example.com or call 07700 900123"
        result = redact_pii(text)
        assert "john@example.com" not in result
        assert "07700" not in result

    def test_custom_replacement(self) -> None:
        text = "Email: a@b.com"
        result = redact_pii(text, replacement="***")
        assert "***" in result
        assert "a@b.com" not in result
