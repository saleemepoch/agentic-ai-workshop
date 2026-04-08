"""
Pillars 2 & 3: Embeddings, Retrieval, and RAG Pipeline

Pillar 2 handles the embedding and retrieval layer:
- Voyage AI embedding client for converting text to vectors
- pgvector similarity search with multiple distance metrics
- Distance metric comparison (cosine, euclidean, dot product)

Pillar 3 extends this into a full RAG pipeline:
- Reranking retrieved chunks for relevance
- Token-budgeted prompt construction
- LLM generation grounded in retrieved context

Interview talking points:
- Why separate embedding from the LLM provider? Embedding-specialised models
  (Voyage AI) outperform general-purpose LLMs at vector representation.
  Production systems often use multiple providers for different capabilities.
- Why pgvector over Pinecone/Weaviate? For our dataset size (<1000 chunks),
  pgvector is simpler and sufficient. One database for relational + vector data.
  The teaching point: "start with pgvector, move to a dedicated vector DB
  when you have millions of vectors."
- Why support multiple distance metrics? To teach the trade-offs. For normalised
  embeddings, cosine and dot product produce identical rankings — demonstrating
  this builds intuition about what these metrics actually measure.

See ADR-002 for embedding model and vector storage decisions.
See ADR-003 for RAG pipeline design decisions.
"""
