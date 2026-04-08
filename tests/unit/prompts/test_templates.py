"""
Unit tests for prompt template loading and rendering.

Tests YAML loading, variable injection, version selection.
No external dependencies.
"""

import pytest

from src.prompts.loader import (
    Prompt,
    PromptVersion,
    list_prompts,
    load_prompt,
)


class TestListPrompts:
    def test_finds_seed_prompts(self) -> None:
        names = list_prompts()
        assert "match_scorer" in names
        assert "cv_parser" in names
        assert "outreach_email" in names


class TestLoadPrompt:
    def test_load_match_scorer(self) -> None:
        p = load_prompt("match_scorer")
        assert p.name == "match_scorer"
        assert "candidate" in p.variables
        assert "job" in p.variables
        assert len(p.versions) >= 2

    def test_load_nonexistent_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_prompt("does_not_exist")

    def test_versions_are_parsed(self) -> None:
        p = load_prompt("cv_parser")
        v1 = p.get_version(1)
        assert v1 is not None
        assert v1.version == 1
        assert "cv_text" in v1.template


class TestPromptVersion:
    def test_render_with_variables(self) -> None:
        p = load_prompt("match_scorer")
        v = p.get_version(1)
        rendered = v.render(candidate="Senior Python dev", job="Backend Engineer")
        assert "Senior Python dev" in rendered
        assert "Backend Engineer" in rendered

    def test_render_missing_variable_raises(self) -> None:
        p = load_prompt("match_scorer")
        v = p.get_version(1)
        with pytest.raises(KeyError):
            v.render(candidate="John")  # missing 'job'


class TestPrompt:
    def test_latest_version(self) -> None:
        p = load_prompt("match_scorer")
        # Latest should be the highest version number
        assert p.latest.version == max(v.version for v in p.versions)

    def test_get_version(self) -> None:
        p = load_prompt("match_scorer")
        v1 = p.get_version(1)
        v2 = p.get_version(2)
        assert v1.version == 1
        assert v2.version == 2
        assert v1.template != v2.template

    def test_get_invalid_version_returns_none(self) -> None:
        p = load_prompt("match_scorer")
        assert p.get_version(99) is None

    def test_render_uses_latest_by_default(self) -> None:
        p = load_prompt("match_scorer")
        rendered = p.render(candidate="Alice", job="ML Engineer")
        # Latest version (v2) has "recruitment consultant" — v1 doesn't
        assert "recruitment consultant" in rendered.lower()

    def test_render_specific_version(self) -> None:
        p = load_prompt("match_scorer")
        rendered = p.render(version=1, candidate="Alice", job="ML Engineer")
        # v1 doesn't mention "recruitment consultant"
        assert "recruitment consultant" not in rendered.lower()

    def test_render_invalid_version_raises(self) -> None:
        p = load_prompt("match_scorer")
        with pytest.raises(ValueError):
            p.render(version=99, candidate="Alice", job="X")
