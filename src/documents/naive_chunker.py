"""
Naive fixed-size chunker: the baseline for comparison.

Splits text into chunks of a fixed token count with optional overlap.
No awareness of document structure — headings, sections, and sentence
boundaries are all ignored.

This chunker exists to demonstrate *why* semantic chunking matters.
The frontend shows both strategies side-by-side on the same document,
making it immediately visible how naive splitting destroys semantic
coherence at chunk boundaries.

Interview talking points:
- Why include a naive chunker at all? Because "semantic chunking is better"
  is a claim. Showing the evidence — the same document split two ways,
  with visibly different chunk quality — is more convincing than any
  explanation. This is how you demonstrate engineering judgment.
- What's wrong with naive chunking? It splits mid-sentence, mid-section,
  and mid-thought. A chunk might contain "...proficient in Python. EDUCATION
  Bachelor of Science in..." — mixing skills and education into a single
  embedding vector that represents neither concept well.

See ADR-001 for the full chunking strategy decision.
"""

import tiktoken

_encoder = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """Count tokens using cl100k_base encoding."""
    return len(_encoder.encode(text))


def naive_chunk(
    text: str,
    max_tokens: int = 256,
    overlap_tokens: int = 50,
) -> list[dict[str, str | int]]:
    """Chunk text by splitting at fixed token intervals.

    No section awareness, no sentence boundary detection. Just raw token splitting.
    Overlap is applied by rewinding the token pointer by overlap_tokens.

    Args:
        text: The full document text to chunk.
        max_tokens: Maximum tokens per chunk.
        overlap_tokens: Number of overlapping tokens between consecutive chunks.

    Returns:
        List of dicts: [{"content": str, "chunk_index": int, "token_count": int}, ...]
    """
    tokens = _encoder.encode(text)

    if len(tokens) <= max_tokens:
        return [
            {
                "content": text,
                "chunk_index": 0,
                "token_count": len(tokens),
            }
        ]

    chunks: list[dict[str, str | int]] = []
    start = 0
    step = max(1, max_tokens - overlap_tokens)

    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = _encoder.decode(chunk_tokens)

        chunks.append(
            {
                "content": chunk_text,
                "chunk_index": len(chunks),
                "token_count": len(chunk_tokens),
            }
        )

        # If we've reached the end, stop
        if end >= len(tokens):
            break

        start += step

    return chunks
