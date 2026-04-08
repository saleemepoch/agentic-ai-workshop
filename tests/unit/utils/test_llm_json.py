"""
Unit tests for the LLM JSON parsing helper.

Pure logic — covers all the variations of code-fenced and raw JSON we've
seen LLMs produce in practice.
"""

import json

import pytest

from src.utils.llm_json import (
    parse_llm_json,
    parse_llm_json_strict,
    strip_code_fences,
)


class TestStripCodeFences:
    def test_no_fences(self) -> None:
        assert strip_code_fences('{"a": 1}') == '{"a": 1}'

    def test_json_fence(self) -> None:
        text = '```json\n{"a": 1}\n```'
        assert strip_code_fences(text) == '{"a": 1}'

    def test_plain_fence(self) -> None:
        text = '```\n{"a": 1}\n```'
        assert strip_code_fences(text) == '{"a": 1}'

    def test_fence_with_leading_whitespace(self) -> None:
        text = '   ```json\n{"a": 1}\n```   '
        assert strip_code_fences(text) == '{"a": 1}'

    def test_unclosed_fence(self) -> None:
        # Sometimes LLMs forget the closing fence — should still strip the opening
        text = '```json\n{"a": 1}'
        assert strip_code_fences(text) == '{"a": 1}'

    def test_multiline_json_in_fence(self) -> None:
        text = '```json\n{\n  "a": 1,\n  "b": 2\n}\n```'
        assert strip_code_fences(text) == '{\n  "a": 1,\n  "b": 2\n}'

    def test_empty_string(self) -> None:
        assert strip_code_fences("") == ""

    def test_only_whitespace(self) -> None:
        assert strip_code_fences("   \n   ") == ""


class TestParseLLMJSON:
    def test_raw_json(self) -> None:
        assert parse_llm_json('{"score": 8, "reasoning": "good"}') == {
            "score": 8,
            "reasoning": "good",
        }

    def test_fenced_json(self) -> None:
        text = '```json\n{"score": 8}\n```'
        assert parse_llm_json(text) == {"score": 8}

    def test_invalid_json_returns_none(self) -> None:
        assert parse_llm_json("not json at all") is None

    def test_invalid_json_returns_fallback(self) -> None:
        fallback = {"score": 0}
        assert parse_llm_json("not json", fallback=fallback) == fallback

    def test_empty_string(self) -> None:
        assert parse_llm_json("") is None

    def test_array_response(self) -> None:
        assert parse_llm_json("[1, 2, 3]") == [1, 2, 3]

    def test_nested_object(self) -> None:
        text = '```json\n{"outer": {"inner": [1, 2]}}\n```'
        assert parse_llm_json(text) == {"outer": {"inner": [1, 2]}}


class TestParseLLMJSONStrict:
    def test_valid_returns_parsed(self) -> None:
        assert parse_llm_json_strict('{"a": 1}') == {"a": 1}

    def test_fenced_returns_parsed(self) -> None:
        assert parse_llm_json_strict('```json\n{"a": 1}\n```') == {"a": 1}

    def test_invalid_raises(self) -> None:
        with pytest.raises(json.JSONDecodeError):
            parse_llm_json_strict("not json")
