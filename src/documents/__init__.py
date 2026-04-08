"""
Pillar 1: Document Processing & Chunking

Handles ingestion, storage, and chunking of documents (CVs and job descriptions).
Two chunking strategies are implemented side-by-side for comparison:

1. **Semantic chunker** (primary): Section-aware, token-aware splitting that preserves
   document structure. Detects headings, section boundaries, and splits at sentence
   boundaries within sections.

2. **Naive chunker** (baseline): Fixed-size token splitting with overlap. Exists to
   demonstrate why semantic chunking matters — the frontend shows both strategies
   on the same document.

Interview talking points:
- Why two chunkers? The comparison is the teaching tool. Showing a naive chunk that
  splits "5 years of Python" across two chunks vs a semantic chunk that keeps the
  skills section intact makes the case for semantic chunking immediately obvious.
- Why token-aware, not character-aware? Downstream models (embeddings, LLMs) have
  token limits. A 500-character chunk might be 100 or 200 tokens depending on content.
  Token counting with tiktoken is fast and deterministic.
- Why regex-based section detection? It covers 80% of structured documents (CVs, JDs)
  without LLM cost. For unstructured text, you'd consider LLM-based chunking (ADR-001).

See ADR-001 for the full decision record on chunking strategy.
"""
