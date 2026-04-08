"""
Unit tests for the fallback chain pattern.
"""

import pytest

from src.resilience.fallback import FallbackProvider, fallback_chain


class TestFallbackChain:
    def test_first_provider_succeeds(self) -> None:
        providers = [
            FallbackProvider(name="primary", func=lambda: "primary_result"),
            FallbackProvider(name="secondary", func=lambda: "secondary_result"),
        ]
        result = fallback_chain(providers)
        assert result.success is True
        assert result.value == "primary_result"
        assert result.provider_used == "primary"
        assert len(result.attempts) == 1

    def test_falls_back_to_secondary(self) -> None:
        def failing():
            raise RuntimeError("primary down")

        providers = [
            FallbackProvider(name="primary", func=failing),
            FallbackProvider(name="secondary", func=lambda: "secondary_result"),
        ]
        result = fallback_chain(providers)
        assert result.success is True
        assert result.value == "secondary_result"
        assert result.provider_used == "secondary"
        assert len(result.attempts) == 2
        assert result.attempts[0].success is False
        assert result.attempts[1].success is True

    def test_all_providers_fail(self) -> None:
        def failing(name):
            def f():
                raise RuntimeError(f"{name} failed")
            return f

        providers = [
            FallbackProvider(name="a", func=failing("a")),
            FallbackProvider(name="b", func=failing("b")),
            FallbackProvider(name="c", func=failing("c")),
        ]
        result = fallback_chain(providers)
        assert result.success is False
        assert result.value is None
        assert result.provider_used is None
        assert len(result.attempts) == 3

    def test_records_errors(self) -> None:
        def failing():
            raise ValueError("specific error")

        providers = [
            FallbackProvider(name="failing", func=failing),
            FallbackProvider(name="working", func=lambda: "ok"),
        ]
        result = fallback_chain(providers)
        assert result.success is True
        assert "specific error" in result.attempts[0].error

    def test_empty_chain(self) -> None:
        result = fallback_chain([])
        assert result.success is False
        assert len(result.attempts) == 0
