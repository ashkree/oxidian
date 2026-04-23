# 🪨 Oxidian

> Your Obsidian vault, sharpened by AI. A personal knowledge assistant with a Python core and a Rust future.

Oxidian is a fast, lightweight RAG (Retrieval-Augmented Generation) pipeline that sits on top of your Obsidian vault. Ask questions in plain English and get answers grounded in your own notes — with source references back to the exact files they came from.

---

## Architecture

Oxidian is built as a **service-oriented system**: a Python core exposes a clean HTTP API, and any client speaks to it over JSON/SSE. This means the CLI, an Obsidian plugin, and a web UI all use exactly the same interface.

```
┌─────────────────────────────────────────┐
│               Clients                   │
│  oxidian-cli (Rust)  │  Obsidian Plugin │  Web UI  │
└──────────────┬──────────────────────────┘
               │  HTTP/REST + SSE (localhost:3000)
┌──────────────▼──────────────────────────┐
│         Python Core (FastAPI)           │
│  POST /index  │  POST /query            │
│  GET /status  │  GET /chunks            │
│  ─────────────────────────────────────  │
│  ingest  │  embed  │  store  │  query   │
└──────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  External APIs          Local Storage   │
│  Anthropic Claude  │   oxidian.db       │
│  OpenAI Embeddings │   config.toml      │
│  (Ollama local)    │   Obsidian Vault   │
└─────────────────────────────────────────┘
```

---

## The Middle Path: Python now, Rust later

The core is written in Python for velocity — the RAG pipeline, embedding, vector storage, and API are all working in v1. The plan is to profile, identify the hot paths, and rewrite them in Rust as a second pass.

| Component | v1 | v2 |
|---|---|---|
| File ingestion + chunking | Python | **Rust binary** (subprocess) |
| Vector similarity search | SQLite + sqlite-vec | **Rust SIMD** (subprocess) |
| HTTP server | FastAPI (Python) | stays Python |
| CLI client | Python script | **Rust** (`oxidian-cli`) |
| Obsidian plugin | — | TypeScript (calls same API) |

This gives a legitimate CV narrative: *"built working RAG pipeline in Python, then profiled and rewrote performance-critical paths in Rust."* The Rust work is grounded in real engineering decisions rather than premature optimisation.

---

## Tech Stack

| Layer | Tech |
|---|---|
| Language | Python 3.11+ |
| API framework | `FastAPI` + `uvicorn` |
| Markdown parsing | `python-frontmatter` |
| Tokenisation | `tiktoken` (cl100k_base) |
| HTTP client | `httpx` |
| Vector storage | `sqlite-vec` (SQLite extension) |
| Embeddings | OpenAI `text-embedding-3-small` or Ollama |
| LLM | Anthropic Claude or OpenAI |
| Streaming | SSE via `sse-starlette` |
| CLI (future) | Rust + `clap` + `reqwest` |

---

## Project Structure

```
oxidian/
├── core/
│   ├── config.py             # Config loader (config.toml + env vars)
│   ├── models.py             # Shared Pydantic models (Chunk, QueryResponse, …)
│   ├── ingest/
│   │   ├── walker.py         # Vault directory traversal + mtime tracking
│   │   ├── parser.py         # Markdown parsing, frontmatter stripping, wikilinks
│   │   └── chunker.py        # Token-based chunking with heading-aware splits ← Rust v2 target
│   ├── embed/
│   │   └── client.py         # Embedding client (OpenAI + Ollama)
│   ├── store/
│   │   └── sqlite.py         # Vector store: upsert, top-k search, mtime diffing ← Rust v2 target
│   ├── query/
│   │   ├── indexer.py        # Orchestrates walk → parse → chunk → embed → store
│   │   └── llm.py            # LLM client (Anthropic + OpenAI), streaming
│   └── server/
│       ├── app.py            # FastAPI app factory + lifespan wiring
│       └── routes.py         # All HTTP route handlers
├── tests/
│   └── test_ingest.py        # Unit tests for walker, parser, chunker
├── main.py                   # Entry point (uvicorn runner)
├── pyproject.toml
├── config.example.toml
└── README.md
```

---

## Setup

### Prerequisites

- Python 3.11+
- An Obsidian vault
- API key from [Anthropic](https://console.anthropic.com/) and/or [OpenAI](https://platform.openai.com/)

### Installation

```bash
git clone https://github.com/yourusername/oxidian
cd oxidian

python -m venv .venv
source .venv/bin/activate

pip install -e .
```

### Configuration

```bash
cp config.example.toml config.toml
# Edit config.toml with your vault path and API keys
```

```toml
[vault]
path = "/path/to/your/obsidian/vault"

[embedding]
provider = "openai"
model = "text-embedding-3-small"
api_key = "sk-..."          # or set OPENAI_API_KEY env var

[llm]
provider = "anthropic"
model = "claude-sonnet-4-20250514"
api_key = "sk-ant-..."      # or set ANTHROPIC_API_KEY env var

[chunking]
chunk_size = 512
overlap = 64
```

### Running

```bash
# Start the core service
python main.py
# → listening on http://localhost:3000

# Index your vault
curl -X POST http://localhost:3000/index

# Ask a question
curl -X POST http://localhost:3000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What did I write about deep work?", "stream": false}'

# Check status
curl http://localhost:3000/status
```

---

## API Reference

| Method | Route | Description |
|---|---|---|
| `POST` | `/index` | Index or re-index the vault. `{"force": false}` for incremental. |
| `POST` | `/query` | Ask a question. Returns SSE stream (default) or JSON. |
| `GET` | `/status` | Health check + index stats. |
| `GET` | `/chunks` | Paginated view of indexed chunks (debug). |
| `DELETE` | `/index` | Wipe the index. |

### Query request

```json
{
  "question": "What are my notes on Zettelkasten?",
  "top_k": 5,
  "stream": true
}
```

### Query SSE stream events

```
event: token      data: "Based on your notes..."
event: token      data: " the Zettelkasten method..."
event: citations  data: [{"filename": "zettelkasten.md", "heading": "Core Principles", ...}]
event: done       data: ""
```

---

## Milestones

### Phase 1 — Python Core ✦ current
- [x] Vault walker with mtime tracking and incremental diffing
- [x] Markdown parser: frontmatter stripping, wikilinks, tags, headings
- [x] Token-based chunker with heading-aware splits and overlap
- [x] Embedding client: OpenAI + Ollama
- [x] SQLite vector store with sqlite-vec
- [x] Incremental indexer (only re-embeds changed files)
- [x] LLM client: Anthropic + OpenAI, streaming
- [x] FastAPI server: `/index`, `/query`, `/status`, `/chunks`, `DELETE /index`
- [x] SSE streaming for query responses
- [x] Unit tests for ingestion pipeline
- [ ] Integration tests (mock embeddings)
- [ ] `oxidian index` CLI command (Python, quick)
- [ ] `oxidian ask` CLI command (Python, quick)
- [ ] File watcher for automatic re-indexing

### Phase 2 — Rust CLI
- [ ] `oxidian-cli` Rust project setup (`clap`, `reqwest`, `tokio`)
- [ ] `oxidian index` — calls `POST /index`, shows progress
- [ ] `oxidian ask` — calls `POST /query`, streams SSE to terminal
- [ ] `oxidian status` — calls `GET /status`, pretty-prints stats

### Phase 3 — Rust Hot Path Rewrites
- [ ] Profile the Python core under real vault load
- [ ] Rewrite chunker as a Rust binary (`oxidian-chunk`)
- [ ] Call chunker via subprocess from Python indexer
- [ ] Benchmark: Python vs Rust chunker throughput
- [ ] Rewrite vector similarity search in Rust with SIMD
- [ ] Benchmark: sqlite-vec vs Rust SIMD search latency

### Phase 4 — Polish
- [ ] Minimal web UI (single HTML file, served by FastAPI)
- [ ] Obsidian plugin (TypeScript) calling the local API
- [ ] Ollama support for fully local operation (no cloud APIs)
- [ ] Relevance score display and chunk preview in responses
- [ ] Configurable chunking strategies (by heading, by paragraph)
- [ ] OpenAPI spec + auto-generated client for Obsidian plugin

---

## License

MIT
