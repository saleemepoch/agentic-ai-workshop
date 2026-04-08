# ADR-002: Embedding Model & Vector Storage

## Status
Accepted

## Context

The workshop's retrieval pipeline (Pillar 2) needs to convert text chunks into vector embeddings and search for similar vectors. Two decisions are required:

1. **Which embedding model** to use for generating vectors
2. **Where to store vectors** and how to search them

## Options Considered

### Embedding Model

**Option A: Voyage AI (voyage-3)**
- 1024 dimensions, strong performance on retrieval benchmarks (MTEB)
- Dedicated embedding model — optimised for semantic similarity, not generation
- Affordable pricing, fast inference
- Python SDK available

**Option B: OpenAI Embeddings (text-embedding-3-large)**
- 3072 dimensions (configurable down to 256)
- Industry standard, well-documented
- Tight coupling to OpenAI ecosystem

**Option C: Claude Embeddings (via Anthropic API)**
- Not available — Anthropic does not offer a dedicated embedding endpoint
- Would require prompt-based embedding (expensive, slow)

**Option D: Open-source (sentence-transformers / Hugging Face)**
- Free to run, no API dependency
- Requires GPU for reasonable performance, or accept slower CPU inference
- Self-hosting adds operational complexity

### Vector Storage

**Option E: pgvector (PostgreSQL extension)**
- Adds vector similarity search to existing Postgres
- Supports cosine, euclidean, and inner product distance
- HNSW and IVFFlat indexes for approximate nearest neighbour search
- One database for everything — relational data and vectors

**Option F: Dedicated vector DB (Pinecone / Weaviate / Qdrant)**
- Purpose-built for vector search at scale
- Better performance at millions+ of vectors
- Additional infrastructure to manage, another service to learn

**Option G: In-memory (FAISS / Annoy)**
- Fast, no external dependency
- No persistence — vectors lost on restart
- Doesn't scale beyond single process

## Decision

**Voyage AI (voyage-3)** for embeddings. **pgvector** for vector storage.

## Rationale

### Why Voyage AI
- Embedding-specialised models outperform general-purpose LLMs at vector representation. This is a key teaching point — "use the right tool for the job."
- 1024 dimensions is a good balance of quality vs storage/compute cost. Higher dimensions give marginally better results but increase memory usage and search time linearly.
- Separating the embedding provider from the LLM provider (Anthropic) demonstrates that production AI systems often use multiple providers for different capabilities.

### Why pgvector
- The workshop's dataset is small (hundreds of chunks, not millions). pgvector handles this trivially — no need for dedicated vector infrastructure.
- One database simplifies the stack. Developers can use familiar SQL tooling and joins across relational and vector data (e.g., "find similar chunks AND join with document metadata").
- pgvector supports multiple distance metrics (cosine, euclidean, inner product), which enables the teaching comparison on Pillar 2's frontend.
- Teaching point: "Start with pgvector. Move to a dedicated vector DB when you have millions of vectors and need sub-millisecond search."

## Consequences

- Voyage AI is a paid API — requires an API key and incurs per-token costs
- pgvector requires the extension to be installed in Postgres (handled by using the `pgvector/pgvector` Docker image)
- 1024-dimension vectors at float32 = 4KB per vector. For our dataset (~200 chunks), total vector storage is ~800KB — negligible
- Distance metric comparison is a presentation feature, not a production pattern. In production, you'd pick one metric and optimise for it

## Distance Metrics — Teaching Notes

Three metrics are supported, each answering a slightly different question:

- **Cosine similarity**: "How similar is the direction of these vectors?" Ignores magnitude. Best default for normalised embeddings (which Voyage AI produces). Range: -1 to 1.
- **Euclidean distance**: "How far apart are these points in vector space?" Sensitive to magnitude. Good for clustering. Range: 0 to ∞.
- **Inner product (dot product)**: "How aligned are these vectors, accounting for magnitude?" Equivalent to cosine for normalised vectors. Used when magnitude carries meaning.

For normalised embeddings (like Voyage AI's output), cosine and dot product produce identical rankings. The frontend demonstrates this — users toggle between metrics and see that rankings barely change, reinforcing the concept.
