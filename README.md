# Agentic AI Workshop

A teaching-focused demonstration platform for **agentic AI**, **RAG systems**, and **production AI engineering**. Built as both a portfolio piece and a team training tool.

## What This Is

An interactive platform organised into 10 pillars, each covering a core AI engineering concept with working backend code and a frontend that lets you experiment, visualise, and understand the trade-offs behind every decision.

## The 10 Pillars

| # | Pillar | What You'll Learn |
|---|--------|-------------------|
| 1 | **Document Processing & Chunking** | Semantic vs naive chunking, token-aware splitting |
| 2 | **Embeddings & Retrieval** | Voyage AI embeddings, pgvector search, distance metrics |
| 3 | **RAG Pipeline** | End-to-end retrieval-augmented generation with reranking |
| 4 | **Agentic Workflow** | LangGraph state machines, conditional routing, tool use |
| 5 | **Observability & Cost** | Langfuse tracing, per-request cost tracking, latency analysis |
| 6 | **Evaluation Pipeline** | Golden datasets, precision/recall/MRR, LLM-as-judge |
| 7 | **Guardrails & Safety** | Layered guardrails, PII detection, faithfulness scoring |
| 8 | **Prompt Engineering** | Versioned templates, A/B comparison, prompt design patterns |
| 9 | **Structured Outputs** | Pydantic LLM schemas, parse-validate-retry pipelines |
| 10 | **Error Handling & Fallbacks** | Retry strategies, fallback chains, circuit breakers |

## Tech Stack

**Backend**: Python 3.12+ · FastAPI · SQLAlchemy · PostgreSQL + pgvector · Claude (Anthropic) · Voyage AI · LangGraph · Langfuse

**Frontend**: Next.js · TypeScript · Tailwind CSS · React Flow · Recharts

**Infrastructure**: Docker Compose · GitHub Actions

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+
- Python 3.12+
- API keys: Anthropic, Voyage AI, Langfuse

### Setup

```bash
# Clone and configure
git clone <repo-url>
cd agentic-ai-workshop
cp .env.example .env
# Edit .env with your API keys

# Start all services
docker compose up

# Or run individually:
docker compose up -d db          # PostgreSQL + pgvector
cd src && uvicorn main:app --reload --port 8000   # API
cd web && npm install && npm run dev               # Frontend
```

### Seed Sample Data

```bash
python -m scripts.seed_data
```

## Project Structure

```
├── docs/           # Architecture (C4), ADRs, roadmap
├── src/            # Python backend (FastAPI, one package per pillar)
├── tests/          # Unit, integration, and evaluation tests
├── web/            # Next.js frontend (interactive documentation)
├── scripts/        # Seed data, eval runner, demo
└── docker-compose.yml
```

See [docs/architecture.md](docs/architecture.md) for the full C4 architecture documentation.

See [docs/ROADMAP.md](docs/ROADMAP.md) for the build roadmap and progress.

## Architecture Decisions

All significant decisions are documented as ADRs in [docs/adrs/](docs/adrs/).

## License

MIT
