"""
Semantic chunker: section-aware, token-aware document splitting.

This is the primary chunking strategy. It understands document structure —
headings, sections, paragraph boundaries — and splits at semantic boundaries
rather than arbitrary token counts.

Algorithm:
1. Detect sections by identifying headings (markdown, ALL CAPS, colon-terminated labels)
2. Split text into sections at heading boundaries
3. For each section:
   a. If it fits within max_tokens, keep it as a single chunk
   b. If it exceeds max_tokens, split at sentence boundaries
   c. Apply token overlap between chunks within the same section
4. Never merge content across section boundaries (a chunk won't contain
   the end of "Experience" and the start of "Education")

Interview talking points:
- Why sentence-level splitting within sections? Because a sentence is the smallest
  unit that carries complete meaning. Splitting mid-sentence produces incoherent chunks
  that confuse embedding models — "5 years of" and "Python experience at Google" would
  get different embeddings than "5 years of Python experience at Google".
- Why no overlap across section boundaries? Overlap helps preserve context at chunk
  edges, but across sections it would mix semantically unrelated content. The overlap
  between "...proficient in Python" and "Education: BSc Computer Science..." would
  create a misleading chunk.
- Why tiktoken? It's the standard tokeniser for modern transformer models. It gives
  us exact token counts without an API call. We use cl100k_base encoding which is
  compatible with Claude and most current models.

See ADR-001 for the full chunking strategy decision.
"""

import re

import tiktoken

# Heading patterns for section detection in CVs/JDs
# Ordered by specificity — more specific patterns first
HEADING_PATTERNS = [
    # Markdown headings: ## Experience, ### Skills
    re.compile(r"^#{1,4}\s+.+$", re.MULTILINE),
    # ALL CAPS headings: WORK EXPERIENCE, EDUCATION
    re.compile(r"^[A-Z][A-Z\s&/]{2,}$", re.MULTILINE),
    # Colon-terminated labels: Experience:, Skills:, Education:
    re.compile(r"^[A-Z][A-Za-z\s&/]+:\s*$", re.MULTILINE),
]

# Sentence boundary pattern — splits on ., !, ? followed by whitespace
SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")

_encoder = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """Count tokens using cl100k_base encoding.

    This is the same encoding used by Claude and GPT-4. It gives us accurate
    token counts without an API call — critical for token budgeting in the
    RAG pipeline (Pillar 3) and cost tracking (Pillar 5).
    """
    return len(_encoder.encode(text))


def detect_sections(text: str) -> list[str]:
    """Split text into sections based on heading detection.

    Returns a list of sections, where each section starts with its heading
    (if one was detected) and contains all text until the next heading.

    If no headings are detected, the entire text is returned as a single section.
    This handles unstructured documents gracefully — they just produce fewer,
    larger sections that get split by the token-aware logic downstream.
    """
    # Find all heading positions
    heading_positions: list[int] = []
    for pattern in HEADING_PATTERNS:
        for match in pattern.finditer(text):
            heading_positions.append(match.start())

    if not heading_positions:
        # No headings found — treat entire text as one section
        # Fall back to splitting on double newlines (paragraph boundaries)
        paragraphs = re.split(r"\n\s*\n", text)
        return [p.strip() for p in paragraphs if p.strip()]

    # Sort and deduplicate positions
    heading_positions = sorted(set(heading_positions))

    # Split text at heading positions
    sections: list[str] = []

    # Content before the first heading (if any)
    if heading_positions[0] > 0:
        preamble = text[: heading_positions[0]].strip()
        if preamble:
            sections.append(preamble)

    # Each heading starts a new section
    for i, pos in enumerate(heading_positions):
        end = heading_positions[i + 1] if i + 1 < len(heading_positions) else len(text)
        section = text[pos:end].strip()
        if section:
            sections.append(section)

    return sections


def split_section_into_chunks(
    section: str,
    max_tokens: int = 256,
    overlap_tokens: int = 50,
) -> list[str]:
    """Split a single section into token-bounded chunks at sentence boundaries.

    If the section fits within max_tokens, it's returned as-is (single chunk).
    Otherwise, sentences are accumulated until the token budget is reached,
    then a new chunk starts — with overlap from the end of the previous chunk.
    """
    section_tokens = count_tokens(section)

    if section_tokens <= max_tokens:
        return [section]

    # Split into sentences
    sentences = SENTENCE_BOUNDARY.split(section)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return [section]

    chunks: list[str] = []
    current_sentences: list[str] = []
    current_tokens = 0

    for sentence in sentences:
        sentence_tokens = count_tokens(sentence)

        # If a single sentence exceeds max_tokens, include it as its own chunk
        # This is a pragmatic choice — we never split mid-sentence
        if sentence_tokens > max_tokens:
            if current_sentences:
                chunks.append(" ".join(current_sentences))
                current_sentences = []
                current_tokens = 0
            chunks.append(sentence)
            continue

        # Would adding this sentence exceed the budget?
        if current_tokens + sentence_tokens > max_tokens and current_sentences:
            chunks.append(" ".join(current_sentences))

            # Apply overlap: keep sentences from the end of the current chunk
            # that fit within the overlap budget
            overlap_sentences: list[str] = []
            overlap_count = 0
            for s in reversed(current_sentences):
                s_tokens = count_tokens(s)
                if overlap_count + s_tokens > overlap_tokens:
                    break
                overlap_sentences.insert(0, s)
                overlap_count += s_tokens

            current_sentences = overlap_sentences
            current_tokens = overlap_count

        current_sentences.append(sentence)
        current_tokens += sentence_tokens

    # Don't forget the last chunk
    if current_sentences:
        last_chunk = " ".join(current_sentences)
        # Avoid duplicating the last chunk if it's identical to the previous
        if not chunks or last_chunk != chunks[-1]:
            chunks.append(last_chunk)

    return chunks


def semantic_chunk(
    text: str,
    max_tokens: int = 256,
    overlap_tokens: int = 50,
) -> list[dict[str, str | int]]:
    """Chunk text using section-aware, token-aware semantic splitting.

    Returns a list of chunk dicts with content, index, and token count.
    This is the primary chunking strategy for the workshop.

    Args:
        text: The full document text to chunk.
        max_tokens: Maximum tokens per chunk (default 256).
        overlap_tokens: Token overlap between chunks within the same section.

    Returns:
        List of dicts: [{"content": str, "chunk_index": int, "token_count": int}, ...]
    """
    sections = detect_sections(text)
    chunks: list[dict[str, str | int]] = []

    for section in sections:
        section_chunks = split_section_into_chunks(section, max_tokens, overlap_tokens)
        for chunk_text in section_chunks:
            chunks.append(
                {
                    "content": chunk_text,
                    "chunk_index": len(chunks),
                    "token_count": count_tokens(chunk_text),
                }
            )

    return chunks
