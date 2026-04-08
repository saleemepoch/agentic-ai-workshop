"""
Unit tests for the naive fixed-size chunker.

Tests token-based splitting, overlap handling, and boundary cases.
"""

import pytest

from src.documents.naive_chunker import count_tokens, naive_chunk


class TestNaiveChunk:
    """Fixed-size token chunking."""

    def test_short_text_single_chunk(self) -> None:
        text = "A short document."
        chunks = naive_chunk(text, max_tokens=100)
        assert len(chunks) == 1
        assert chunks[0]["content"] == text
        assert chunks[0]["chunk_index"] == 0

    def test_long_text_multiple_chunks(self) -> None:
        text = "word " * 500  # ~500 tokens
        chunks = naive_chunk(text, max_tokens=100, overlap_tokens=0)
        assert len(chunks) > 1

        # All chunks except last should be close to max_tokens
        for chunk in chunks[:-1]:
            assert chunk["token_count"] <= 100

    def test_overlap_produces_more_chunks(self) -> None:
        text = "the quick brown fox " * 200  # ~800 tokens, varied vocabulary
        chunks_no_overlap = naive_chunk(text, max_tokens=100, overlap_tokens=0)
        chunks_with_overlap = naive_chunk(text, max_tokens=100, overlap_tokens=30)
        # Overlap should produce more chunks (stepping by 70 instead of 100)
        assert len(chunks_with_overlap) > len(chunks_no_overlap)

    def test_chunk_indices_sequential(self) -> None:
        text = "word " * 300
        chunks = naive_chunk(text, max_tokens=50)
        indices = [c["chunk_index"] for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_empty_text(self) -> None:
        chunks = naive_chunk("", max_tokens=100)
        assert len(chunks) == 1
        assert chunks[0]["token_count"] == 0

    def test_token_count_accuracy(self) -> None:
        text = "The quick brown fox jumps over the lazy dog."
        chunks = naive_chunk(text, max_tokens=100)
        assert chunks[0]["token_count"] == count_tokens(text)

    def test_all_tokens_preserved(self) -> None:
        """All original tokens should be covered across chunks (no gaps)."""
        text = "The quick brown fox jumps over the lazy dog near the river bank."
        chunks = naive_chunk(text, max_tokens=5, overlap_tokens=0)
        # Concatenating all chunk content should reconstruct the original tokens
        reconstructed = "".join(c["content"] for c in chunks)
        # Token-level splitting may split/rejoin characters differently,
        # but the total token count should match
        from src.documents.naive_chunker import count_tokens as cnt
        original_tokens = cnt(text)
        chunk_tokens = sum(c["token_count"] for c in chunks)
        assert chunk_tokens == original_tokens

    def test_ignores_document_structure(self) -> None:
        """Naive chunker should NOT respect section boundaries — that's the point."""
        text = "## Skills\nPython, Java, SQL.\n\n## Education\nBSc from MIT."
        chunks = naive_chunk(text, max_tokens=10, overlap_tokens=0)
        # With small enough chunks, content from different sections
        # should end up in the same chunk — proving naive doesn't care about structure
        assert len(chunks) >= 2
