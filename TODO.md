# Oxidian — TODO

> Build order: finish Phase 1 completely before touching Rust. A working Python demo beats a half-finished Rust one every time.

---

## Folder Structure

```
oxidian/
│
├── core/                          # Python core service
│   ├── __init__.py
│   ├── config.py                  # Config loader (config.toml + env vars)
│   ├── models.py                  # Shared Pydantic models
│   │
│   ├── ingest/                    # Ingestion pipeline
│   │   ├── __init__.py
│   │   ├── walker.py              # Vault directory traversal + mtime tracking
│   │   ├── parser.py              # Markdown parsing, frontmatter, wikilinks, tags
│   │   └── chunker.py             # Token-based chunking with heading-aware splits
│   │                              #   ↑ Rust rewrite target (Phase 3)
│   │
│   ├── embed/                     # Embedding layer
│   │   ├── __init__.py
│   │   └── client.py              # OpenAI + Ollama embedding clients
│   │
│   ├── store/                     # Vector storage
│   │   ├── __init__.py
│   │   └── sqlite.py              # sqlite-vec store: upsert, top-k search, mtime diff
│   │                              #   ↑ Rust rewrite target (Phase 3)
│   │
│   ├── query/                     # Query pipeline
│   │   ├── __init__.py
│   │   ├── indexer.py             # Orchestrates walk → parse → chunk → embed → store
│   │   └── llm.py                 # LLM client (Claude + OpenAI), streaming
│   │
│   └── server/                    # HTTP API
│       ├── __init__.py
│       ├── app.py                 # FastAPI app factory + lifespan wiring
│       ├── routes.py              # All route handlers
│       └── watcher.py             # File watcher for auto re-indexing
│
├── tests/
│   ├── __init__.py
│   ├── test_ingest.py             # Walker, parser, chunker unit tests
│   ├── test_store.py              # VectorStore unit tests
│   ├── test_query.py              # Indexer + LLM tests (mocked clients)
│   └── test_api.py                # FastAPI route tests (TestClient)
│
├── oxidian-cli/                   # Rust CLI (Phase 2)
│   ├── Cargo.toml
│   └── src/
│       ├── main.rs
│       ├── client.rs              # HTTP client + SSE reader
│       └── commands/
│           ├── index.rs
│           ├── ask.rs
│           └── status.rs
│
├── oxidian-chunk/                 # Rust chunker binary (Phase 3)
│   ├── Cargo.toml
│   └── src/
│       └── main.rs                # stdin → stdout chunker
│
├── static/
│   └── index.html                 # Minimal web UI (Phase 4)
│
├── main.py                        # Uvicorn entry point
├── cli.py                         # Python CLI (Typer)
├── pyproject.toml
├── config.example.toml
├── README.md
└── TODO.md
```

---

## Phase 1 — Python Core

Everything needed for a working end-to-end system. No Rust yet.

### 1.1 Project setup
- [ ] Create repo and initialise git
- [ ] Set up `pyproject.toml` with all dependencies
- [ ] Create `config.example.toml` with all settings documented
- [ ] Set up `core/` package structure with `__init__.py` files
- [ ] Create `.gitignore` (venv, `*.db`, `config.toml`, `__pycache__`)
- [ ] Create `.env.example` documenting required environment variables

### 1.2 Config
- [ ] `core/config.py` — load and validate `config.toml` with Pydantic
- [ ] Support env var overrides: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `OXIDIAN_VAULT`
- [ ] Fail fast with a clear error if config file is missing or invalid

### 1.3 Models
- [ ] `core/models.py` — define all shared Pydantic models
  - [ ] `Chunk` — text, source path, heading, tags, token count
  - [ ] `StoredChunk` — Chunk + embedding + mtime
  - [ ] `RetrievedChunk` — StoredChunk + similarity score
  - [ ] `QueryRequest` — question, top_k, stream flag
  - [ ] `QueryResponse` — answer, citations, question, chunks_used
  - [ ] `Citation` — filename, path, heading, score
  - [ ] `IndexRequest` / `IndexResponse`
  - [ ] `StatusResponse`

### 1.4 Ingestion pipeline
- [ ] `core/ingest/walker.py`
  - [ ] Recursively walk vault for `.md` files
  - [ ] Skip Obsidian internals: `.obsidian/`, `.trash/`, `.git/`
  - [ ] Return sorted list of file paths
  - [ ] `get_mtime(path)` helper
  - [ ] `files_changed_since(vault_path, known_mtimes)` — diff for incremental indexing
- [ ] `core/ingest/parser.py`
  - [ ] Strip YAML frontmatter cleanly
  - [ ] Extract frontmatter `tags` / `tag` fields
  - [ ] Extract inline `#tags` from body (skip code blocks)
  - [ ] Extract `[[wikilinks]]` including aliased links
  - [ ] Extract all headings in order
  - [ ] Resolve title: frontmatter → first H1 → filename
- [ ] `core/ingest/chunker.py`
  - [ ] Token-based sliding window using `tiktoken` (cl100k_base)
  - [ ] Split at heading boundaries first, then slide window within sections
  - [ ] Configurable `chunk_size`, `overlap`, `min_chunk_size`
  - [ ] Attach nearest heading to each chunk for context
  - [ ] Return sequential chunk indices per file

### 1.5 Embedding client
- [ ] `core/embed/client.py`
  - [ ] Abstract `EmbedClient` base class
  - [ ] `OpenAIEmbedClient` — batch up to 100 texts per request
  - [ ] `OllamaEmbedClient` — local embeddings via HTTP
  - [ ] `make_embed_client(config)` factory function
  - [ ] Retry logic on transient API errors
  - [ ] Rate limit handling with exponential backoff

### 1.6 Vector store
- [ ] `core/store/sqlite.py`
  - [ ] Create `chunks` table (id, source_path, filename, text, heading, tags, mtime, …)
  - [ ] Create `chunk_vectors` virtual table via `sqlite-vec`
  - [ ] `upsert_chunk(chunk, embedding, mtime)` — insert or replace
  - [ ] `delete_by_source(path)` — remove all chunks for a file
  - [ ] `top_k(query_embedding, k)` — cosine similarity search, return `RetrievedChunk` list
  - [ ] `get_known_mtimes()` — return `{source_path: mtime}` dict
  - [ ] `stats()` — total chunks and total files
  - [ ] WAL mode + NORMAL synchronous pragma for performance

### 1.7 Indexer
- [ ] `core/query/indexer.py`
  - [ ] Full pipeline: walk → parse → chunk → embed → store
  - [ ] Incremental mode: compare mtimes, only process changed files
  - [ ] Delete chunks for files that no longer exist
  - [ ] Batched parallel embedding with concurrency limit
  - [ ] Return `IndexResponse` with counts and duration

### 1.8 LLM client
- [ ] `core/query/llm.py`
  - [ ] Abstract `LLMClient` base class
  - [ ] System prompt that enforces citation-grounded answers
  - [ ] `_build_user_prompt(question, chunks)` — inject retrieved chunks as context
  - [ ] `AnthropicClient` — streaming via `messages.stream()`
  - [ ] `OpenAILLMClient` — streaming via `chat.completions.create(stream=True)`
  - [ ] Both: non-streaming `query()` and async generator `stream()`
  - [ ] `make_llm_client(config)` factory function

### 1.9 FastAPI server
- [ ] `core/server/app.py`
  - [ ] FastAPI app factory
  - [ ] Lifespan: initialise store, embed client, LLM client, indexer on startup
  - [ ] Attach everything to `app.state`
  - [ ] CORS middleware
  - [ ] Graceful shutdown: close DB connection
- [ ] `core/server/routes.py`
  - [ ] `POST /index` — run indexer, return `IndexResponse`
  - [ ] `POST /query` — embed query, retrieve, stream or return answer + citations
  - [ ] `GET /status` — health check + index stats
  - [ ] `GET /chunks` — paginated chunk list for debugging
  - [ ] `DELETE /index` — wipe all chunks from store
  - [ ] SSE streaming: emit `token`, `citations`, `done`, `error` events

### 1.10 Python CLI
- [ ] `cli.py` — Typer app, four commands
  - [ ] `oxidian serve [--port] [--host]` — start the FastAPI server via uvicorn
  - [ ] `oxidian index [--force]` — call `POST /index`, print Rich summary
  - [ ] `oxidian ask "<question>" [--top-k]` — stream tokens to terminal, print citations
  - [ ] `oxidian status` — call `GET /status`, pretty-print with Rich
- [ ] Wire `pyproject.toml` entry point: `oxidian = "cli:app"`

### 1.11 File watcher
- [ ] `core/server/watcher.py`
  - [ ] Background task using `watchfiles`
  - [ ] Watch vault directory for `.md` changes
  - [ ] Debounce: wait 2s after last change before triggering re-index
  - [ ] Run incremental index on change, log changed files
- [ ] Optional watcher startup in `app.py` lifespan (config flag: `[server] watch = true`)

### 1.12 Tests
- [ ] `tests/test_ingest.py`
  - [ ] Walker finds markdown, excludes `.obsidian/`, handles nested dirs
  - [ ] Parser strips frontmatter, extracts tags/wikilinks/headings, title fallback chain
  - [ ] Chunker: single chunk for short notes, multiple for long, heading attribution, sequential indices
- [ ] `tests/test_store.py`
  - [ ] Upsert chunk then retrieve it with `top_k`
  - [ ] `delete_by_source` removes from both tables
  - [ ] `get_known_mtimes` reflects inserted data
  - [ ] More similar vector ranks higher in results
- [ ] `tests/test_query.py`
  - [ ] Full indexer run with mocked embed client and real SQLite
  - [ ] Incremental: second run with unchanged files skips embedding
  - [ ] Deleted files removed from store on next index
  - [ ] Prompt builder injects chunk text and filenames correctly
- [ ] `tests/test_api.py`
  - [ ] `GET /status` returns 200 with correct shape
  - [ ] `POST /index` with mocked indexer returns `IndexResponse`
  - [ ] `POST /query` (non-streaming) returns `QueryResponse`
  - [ ] `POST /query` (streaming) emits correct SSE event sequence
  - [ ] `DELETE /index` wipes chunks, confirmed by `/status`
  - [ ] `POST /query` before indexing returns 404 with clear message

### 1.13 End-to-end smoke test
- [ ] Run against a real Obsidian vault
- [ ] `oxidian index` completes and prints file + chunk counts
- [ ] `oxidian ask` returns a cited answer
- [ ] Second `oxidian index` skips unchanged files
- [ ] Modify a note, re-index — only that file is re-embedded

---

## Phase 2 — Rust CLI (`oxidian-cli`)

The primary CV Rust story: a typed, async Rust HTTP client as the main interface to the Python core.

### 2.1 Project setup
- [ ] `oxidian-cli/Cargo.toml` — dependencies: `clap`, `reqwest`, `tokio`, `serde`, `serde_json`, `eventsource-client`, `colored`, `indicatif`
- [ ] `oxidian-cli/src/main.rs` — clap CLI entry point with subcommands

### 2.2 API client
- [ ] `oxidian-cli/src/client.rs` — typed HTTP client
  - [ ] `post_index(base_url, force) -> Result<IndexResponse>`
  - [ ] `get_status(base_url) -> Result<StatusResponse>`
  - [ ] `stream_query(base_url, question, top_k) -> Result<impl Stream<Item = SseEvent>>`
  - [ ] Configurable base URL (default `http://localhost:3000`)
  - [ ] Clear error type if core service is unreachable

### 2.3 Commands
- [ ] `oxidian-cli/src/commands/index.rs`
  - [ ] Spinner while indexing runs
  - [ ] Summary table: files found, indexed, skipped, chunks created, duration
- [ ] `oxidian-cli/src/commands/ask.rs`
  - [ ] Print streamed tokens to stdout without newline buffering
  - [ ] On `citations` event: print source list below answer
  - [ ] Handle `error` SSE event gracefully
- [ ] `oxidian-cli/src/commands/status.rs`
  - [ ] Formatted table: vault path, chunk count, file count, providers

### 2.4 Polish
- [ ] Cross-platform build test (macOS + Linux)
- [ ] `--url` flag to point at a non-default server address
- [ ] Update README with CLI install and usage

---

## Phase 3 — Rust Hot Path Rewrites

Profile before rewriting. Only worth doing if benchmarks show a real bottleneck.

### 3.1 Profiling
- [ ] Benchmarking script: index a vault of 500+ notes, measure time per stage
- [ ] Identify whether chunker or vector search is the bottleneck
- [ ] Record baseline numbers — document them so the improvement is provable

### 3.2 Chunker rewrite (`oxidian-chunk`)
- [ ] Design stdin/stdout protocol: newline-delimited JSON in, newline-delimited JSON out
- [ ] `oxidian-chunk/src/main.rs` — reads `ParsedNote` JSON, writes `Chunk` JSON
- [ ] Port tokenisation: byte-pair heuristic or `tiktoken-rs`
- [ ] Update `core/ingest/chunker.py` — subprocess call with Python fallback
- [ ] Benchmark: Python vs Rust chunker throughput on real vault
- [ ] Document the interface contract (good interview talking point)

### 3.3 Vector search rewrite
- [ ] Evaluate integration: PyO3 extension vs subprocess vs sidecar service
- [ ] Implement cosine similarity with SIMD (`std::simd` or `packed_simd`)
- [ ] Benchmark against `sqlite-vec` at 10k and 100k vectors
- [ ] Integrate: replace `store.top_k()` with Rust implementation
- [ ] Document before/after latency numbers

---

## Phase 4 — Clients and Polish

### 4.1 Web UI
- [ ] `static/index.html` — single file, no build step, served by FastAPI
  - [ ] Query input + streaming response display
  - [ ] Citation list below answer
  - [ ] Index status indicator + re-index button

### 4.2 Obsidian plugin
- [ ] TypeScript plugin project setup
- [ ] Sidebar panel with query input
- [ ] Stream response using `EventSource`
- [ ] Open cited note in Obsidian on citation click

### 4.3 Local-only mode
- [ ] Ollama embedding support (`nomic-embed-text`)
- [ ] Ollama LLM support (e.g. `llama3`)
- [ ] Document fully local setup in README (no API keys required)

### 4.4 Remaining features
- [ ] Configurable chunking strategies: by heading, by paragraph, fixed-size
- [ ] `GET /chunks?source=<filename>` — filter chunks by source file
- [ ] Relevance score display in query responses
- [ ] `oxidian export` — dump all chunks as JSON

---

## Backlog

- [ ] Docker Compose setup (core + optional Ollama)
- [ ] Multi-vault support (array of vault paths in config)
- [ ] Query history stored in SQLite
- [ ] Hybrid search: BM25 + vector combined scoring
- [ ] Re-rank retrieved chunks with a cross-encoder model
- [ ] OpenAPI spec + auto-generated TypeScript client for Obsidian plugin
