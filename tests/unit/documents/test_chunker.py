"""
Unit tests for the semantic chunker.

Tests section detection, token-aware splitting, overlap handling,
and edge cases. No database or external services needed.
"""

import pytest

from src.documents.chunker import (
    count_tokens,
    detect_sections,
    semantic_chunk,
    split_section_into_chunks,
)


class TestCountTokens:
    """Token counting with tiktoken cl100k_base encoding."""

    def test_empty_string(self) -> None:
        assert count_tokens("") == 0

    def test_simple_text(self) -> None:
        tokens = count_tokens("Hello, world!")
        assert tokens > 0
        assert tokens < 10

    def test_longer_text(self) -> None:
        text = "The quick brown fox jumps over the lazy dog. " * 10
        tokens = count_tokens(text)
        assert tokens > 50


class TestDetectSections:
    """Section detection from document headings."""

    def test_markdown_headings(self) -> None:
        text = "## Experience\nWorked at Google.\n## Education\nBSc Computer Science."
        sections = detect_sections(text)
        assert len(sections) == 2
        assert "Experience" in sections[0]
        assert "Education" in sections[1]

    def test_all_caps_headings(self) -> None:
        text = "WORK EXPERIENCE\nSenior developer at Acme.\n\nEDUCATION\nMIT, 2015."
        sections = detect_sections(text)
        assert len(sections) == 2
        assert "WORK EXPERIENCE" in sections[0]
        assert "EDUCATION" in sections[1]

    def test_colon_headings(self) -> None:
        text = "Skills:\nPython, Java, SQL\n\nExperience:\nSenior dev at startup."
        sections = detect_sections(text)
        assert len(sections) == 2

    def test_no_headings_falls_back_to_paragraphs(self) -> None:
        text = "First paragraph about work.\n\nSecond paragraph about education."
        sections = detect_sections(text)
        assert len(sections) == 2

    def test_preamble_before_first_heading(self) -> None:
        text = "John Doe - Software Engineer\n\n## Experience\nWorked at Google."
        sections = detect_sections(text)
        assert len(sections) == 2
        assert "John Doe" in sections[0]

    def test_empty_text(self) -> None:
        sections = detect_sections("")
        assert len(sections) == 0

    def test_single_section(self) -> None:
        text = "Just a block of text with no headings or paragraph breaks."
        sections = detect_sections(text)
        assert len(sections) == 1


class TestSplitSectionIntoChunks:
    """Token-aware splitting within a single section."""

    def test_short_section_single_chunk(self) -> None:
        text = "A short section that fits in one chunk."
        chunks = split_section_into_chunks(text, max_tokens=100)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_long_section_multiple_chunks(self) -> None:
        # Create a section with many sentences
        text = ". ".join(f"Sentence number {i} with some extra words" for i in range(30))
        chunks = split_section_into_chunks(text, max_tokens=50, overlap_tokens=10)
        assert len(chunks) > 1
        # Each chunk should be within the token limit (approximately)
        for chunk in chunks:
            tokens = count_tokens(chunk)
            # Allow some slack for sentence boundary alignment
            assert tokens <= 80, f"Chunk has {tokens} tokens, expected <= ~50+slack"

    def test_overlap_produces_shared_content(self) -> None:
        text = ". ".join(f"Sentence {i} with additional context words here" for i in range(20))
        chunks = split_section_into_chunks(text, max_tokens=50, overlap_tokens=20)
        if len(chunks) >= 2:
            # There should be some overlap between consecutive chunks
            # (shared sentences at boundaries)
            words_0 = set(chunks[0].split())
            words_1 = set(chunks[1].split())
            overlap = words_0 & words_1
            assert len(overlap) > 0, "Expected some word overlap between consecutive chunks"

    def test_zero_overlap(self) -> None:
        text = ". ".join(f"Sentence {i} with words" for i in range(20))
        chunks = split_section_into_chunks(text, max_tokens=50, overlap_tokens=0)
        assert len(chunks) > 1


class TestSemanticChunk:
    """End-to-end semantic chunking."""

    def test_structured_document(self) -> None:
        text = """## Summary
Experienced software engineer with 10 years in backend systems.

## Experience
Senior Engineer at Google, 2018-2023. Led the design of a distributed caching system serving 1M requests per second. Reduced P99 latency by 40%.

Staff Engineer at Meta, 2015-2018. Built the recommendation pipeline for News Feed. Managed a team of 5 engineers.

## Education
BSc Computer Science, Stanford University, 2015.

## Skills
Python, Go, Java, Kubernetes, PostgreSQL, Redis, gRPC."""

        chunks = semantic_chunk(text, max_tokens=100, overlap_tokens=20)
        assert len(chunks) >= 3  # At least summary, experience, education/skills

        # Each chunk should have required fields
        for chunk in chunks:
            assert "content" in chunk
            assert "chunk_index" in chunk
            assert "token_count" in chunk
            assert chunk["token_count"] > 0
            assert isinstance(chunk["chunk_index"], int)

        # Chunk indices should be sequential
        indices = [c["chunk_index"] for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_empty_document(self) -> None:
        chunks = semantic_chunk("")
        assert len(chunks) == 0

    def test_short_document_single_chunk(self) -> None:
        text = "A very short document."
        chunks = semantic_chunk(text, max_tokens=100)
        assert len(chunks) == 1
        assert chunks[0]["content"] == text

    def test_respects_max_tokens(self) -> None:
        # Long document should produce chunks within token limits
        text = """EXPERIENCE
""" + ". ".join(f"Worked on project {i} involving complex distributed systems" for i in range(30))

        chunks = semantic_chunk(text, max_tokens=80, overlap_tokens=10)
        for chunk in chunks:
            # Allow reasonable slack for sentence-boundary alignment
            assert chunk["token_count"] <= 120, (
                f"Chunk {chunk['chunk_index']} has {chunk['token_count']} tokens"
            )

    def test_sections_not_merged(self) -> None:
        """Chunks should not mix content from different sections."""
        text = """## Skills
Python, Java, SQL, Kubernetes.

## Education
BSc Computer Science, MIT, 2020."""

        chunks = semantic_chunk(text, max_tokens=200)
        # With a generous token limit, each section should be its own chunk
        assert len(chunks) == 2
        assert "Python" in chunks[0]["content"]
        assert "MIT" in chunks[1]["content"]
        # Skills chunk shouldn't contain education content
        assert "MIT" not in chunks[0]["content"]
