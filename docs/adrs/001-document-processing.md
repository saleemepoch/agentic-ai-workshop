# ADR-001: Document Processing & Chunking Strategy

## Status
Accepted

## Context

The workshop's RAG pipeline requires documents (CVs and job descriptions) to be split into chunks before embedding and retrieval. Chunking quality directly affects retrieval quality — poor chunks produce poor search results regardless of how good the embedding model or LLM is.

We need a chunking strategy that:
1. Preserves semantic meaning within each chunk (a chunk about "work experience" shouldn't bleed into "education")
2. Respects token limits of downstream models (embedding models and LLMs have context windows)
3. Is explainable for teaching purposes — users should understand *why* chunks are split where they are

## Options Considered

### Option A: Naive Fixed-Size Chunking
Split text into chunks of N tokens with optional overlap.

- **Pro**: Simple to implement and explain. Predictable chunk sizes. Good baseline for comparison.
- **Con**: Splits mid-sentence, mid-section, or mid-thought. A chunk might contain the end of "Work Experience" and the start of "Education", making it semantically incoherent. Retrieval suffers because the chunk doesn't represent a single concept.

### Option B: Semantic Chunking (Section-Aware)
Detect document structure (headings, sections, blank-line boundaries) and split at semantic boundaries. Within large sections, split at sentence boundaries respecting a token budget.

- **Pro**: Each chunk represents a coherent unit of meaning. Better retrieval because chunks align with how humans organise information. CV sections (experience, education, skills) naturally become separate chunks.
- **Con**: More complex. Relies on heuristics for section detection (regex for headings, blank lines, topic shifts). May produce uneven chunk sizes.

### Option C: LLM-Based Chunking
Use an LLM to identify semantic boundaries and split accordingly.

- **Pro**: Most accurate semantic splitting. Can understand context and meaning.
- **Con**: Expensive (LLM call per document), slow, non-deterministic. Overkill for structured documents like CVs and JDs. Adds a dependency on the LLM being available just to chunk.

### Option D: Recursive Character Splitting (LangChain-style)
Split by paragraph → sentence → word, recursively, until chunks fit within a size limit.

- **Pro**: Well-known pattern. Available in LangChain.
- **Con**: Doesn't leverage document structure. Treats all text equally — a heading is just another line. Misses the opportunity to teach section-aware processing.

## Decision

**Implement both Option A (naive) and Option B (semantic) side-by-side.**

Option B is the primary strategy used throughout the pipeline. Option A exists solely for comparison — the frontend shows both strategies on the same document so users can see exactly how chunking quality affects downstream retrieval.

Option C is referenced in teaching materials as "what you'd consider for unstructured documents where section detection heuristics fail" but is not implemented.

## Rationale

- **Teaching value**: The side-by-side comparison is the most powerful way to demonstrate why chunking matters. Users can see a naive chunk that splits "5 years of Python experience" across two chunks vs a semantic chunk that keeps the entire skills section together.
- **Practical value**: Semantic chunking with section detection works well for structured documents (CVs, JDs, reports). The heuristics (heading detection, blank-line boundaries) cover 80% of cases without LLM cost.
- **Token-awareness**: Both chunkers are token-aware (using `tiktoken`), not character-aware. This is important because downstream models have token limits, not character limits. A chunk of 500 characters might be 100 tokens or 200 tokens depending on content.

## Consequences

- Both chunkers must be maintained and tested independently
- The semantic chunker's section detection heuristics may need tuning for different document formats — this is acceptable for a teaching platform with a known document set
- Token counting adds a dependency on `tiktoken` but this is lightweight and deterministic
- The comparison endpoint returns both strategies' results, doubling the response size — acceptable for a teaching tool

## Implementation Notes

- **Overlap**: Configurable token overlap between chunks (default: 50 tokens). Overlap ensures that context at chunk boundaries isn't lost. The semantic chunker applies overlap only within sections, never across section boundaries.
- **Token counting**: Uses `tiktoken` with the `cl100k_base` encoding (used by Claude and most modern models). This gives accurate token counts without calling an API.
- **Section detection**: Regex-based heading detection (markdown headings, ALL CAPS lines, colon-terminated labels like "Experience:") plus blank-line paragraph boundaries.
