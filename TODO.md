# 🪨 Oxidian — TODO

> Phased build plan. Phase 1 is a complete, working Python system. Later phases layer in Rust for performance and additional clients.

---

## Phase 1 — Python Core

**Goal:** A fully working RAG pipeline in pure Python. By the end of this phase, you can index an Obsidian vault and ask questions against it from the command line. No Rust required.

### 1.1 Project Scaffold

- [X] Initialise `pyproject.toml` with dependencies (`fastapi`, `uvicorn`, `httpx`, `tiktoken`, `python-frontmatter`, `sqlite-vec`, `sse-starlette`, `pydantic`)
- [X] Create `config.example.toml` with all required keys (`vault.path`, `embedding`, `llm`, `chunking`)
- [ ] Implement `core/config.py` — load `config.toml`, merge with env vars, expose typed config object
- [X] Implement `core/models.py` — shared Pydantic models: `Chunk`, `QueryRequest`, `QueryResponse`, `CitationRef`, `IndexStatus`
- [ ] Create `main.py` entry point — boots `uvicorn` on `localhost:3000`

### 1.2 Ingestion Pipeline (`core/ingest/`)

- [X] **`walker.py`** — Recursively discover all `.md` files under `vault.path`; record `mtime` per file; return list of `(path, mtime)` pairs
- [ ] **`parser.py`** — For each file: strip YAML frontmatter, extract wikilinks (`[[...]]`), tags (`#tag`), and heading hierarchy; return structured document object
- [ ] **`chunker.py`** — Split document text into token-bounded chunks (configurable `chunk_size` + `overlap` from config); keep chunks heading-aware (annotate each chunk with its nearest parent heading); this file is the **Phase 3 Rust rewrite target** — keep the interface clean

### 1.3 Embedding + Storage (`core/embed/`, `core/store/`)

- [ ] **`embed/client.py`** — Embedding client supporting `openai` (`text-embedding-3-small`) and `ollama` backends; batched requests; exponential backoff on rate-limit errors
- [ ] **`store/sqlite.py`** — Initialise `oxidian.db`; create `chunks` table (id, source\_path, mtime, heading, text, vector); implement `upsert_chunks`, `top_k_search` (cosine via sqlite-vec), `get_file_mtimes`, `delete_by_path`, `wipe`; this file is the **Phase 3 Rust rewrite target** — keep the interface clean

### 1.4 Indexer (`core/query/indexer.py`)

- [ ] Orchestrate the full ingest loop: walk → diff against stored mtimes → parse changed files → chunk → embed → upsert
- [ ] Skip unchanged files (compare stored mtime vs filesystem mtime)
- [ ] Delete chunks for files that have been removed from the vault
- [ ] Expose a `run_index(force: bool)` function usable from both the API and CLI

### 1.5 LLM Client (`core/query/llm.py`)

- [ ] Support `anthropic` (Claude) and `openai` backends, selectable from config
- [ ] Implement streaming response via SSE tokens
- [ ] Implement non-streaming JSON response path
- [ ] Structured citation output: extract `[[source]]` refs from model response and attach file paths

### 1.6 Prompt Builder (`core/query/`)

- [ ] **`prompt_builder.py`** — Assemble system prompt from retrieved chunks; inject chunk text with source labels; format citation instructions for the model; keep token budget configurable

### 1.7 FastAPI Server (`core/server/`)

- [ ] **`app.py`** — FastAPI app factory; lifespan handler (db init on startup); mount routes
- [ ] **`routes.py`** — Implement all five endpoints:

| Endpoint | Behaviour |
|---|---|
| `POST /index` | Run indexer; accept `{"force": false}`; return job status |
| `POST /query` | Embed query → top-k search → build prompt → stream LLM; SSE by default, JSON if `stream: false` |
| `GET /status` | Return index stats (file count, chunk count, last indexed timestamp) |
| `GET /chunks` | Paginated chunk listing for debug (`?page=&limit=`) |
| `DELETE /index` | Wipe the entire index |

### 1.8 SSE Streaming

- [ ] Query endpoint streams `event: token` lines as LLM responds
- [ ] Emit `event: citations` with full citation list once generation completes
- [ ] Emit `event: done` to close the stream
- [ ] CLI and web clients can consume this without any changes to the API contract

### 1.9 Tests (`tests/`)

- [ ] **`test_ingest.py`** — Unit tests for `walker`, `parser`, `chunker` using fixture `.md` files
- [ ] **`test_store.py`** — Unit tests for `sqlite.py`: upsert, mtime diff, top-k search with known vectors
- [ ] **`test_routes.py`** — Integration tests with mock embedding client (no real API calls); test all five endpoints

### 1.10 Python CLI (quick, pre-Rust)

- [ ] **`oxidian/cli.py`** — Thin Python CLI using `argparse` or `typer`
- [ ] `oxidian index` — POST `/index`, print progress
- [ ] `oxidian ask "<question>"` — POST `/query`, print streamed SSE tokens to stdout
- [ ] `oxidian status` — GET `/status`, pretty-print stats

### 1.11 File Watcher

- [ ] Add optional `watchdog`-based file watcher that calls `run_index(force=False)` on vault changes
- [ ] Enable/disable via config flag (`[watcher] enabled = true`)

---

## Phase 2 — Rust CLI (`oxidian-cli`)

**Goal:** Replace the Python CLI shim with a proper Rust binary. The Python core is unchanged — the Rust client just speaks the same HTTP API. This phase produces a distributable binary and establishes the Rust toolchain in the repo.

### 2.1 Project Setup

- [ ] Create `oxidian-cli/` as a Cargo workspace member
- [ ] Add dependencies: `clap` (arg parsing), `reqwest` (HTTP + SSE), `tokio` (async runtime), `serde`/`serde_json`, `indicatif` (progress bars), `colored` (terminal output)
- [ ] Wire up `Cargo.toml` at repo root as a workspace

### 2.2 Commands

- [ ] **`oxidian index`** — POST `/index`; stream progress events; display spinner + file count on completion
- [ ] **`oxidian ask "<question>"`** — POST `/query` with `stream: true`; consume SSE `token` events and print to stdout in real time; print citations block after `done` event
- [ ] **`oxidian status`** — GET `/status`; render formatted table of index stats
- [ ] **`oxidian chunks`** — GET `/chunks`; paginated debug view

### 2.3 Config

- [ ] Read `config.toml` for `server.url` (default `http://localhost:3000`)
- [ ] Allow `--url` flag to override per-command

---

## Phase 3 — Rust Hot Path Rewrites

**Goal:** Profile the Python core under real vault load and rewrite the two identified bottlenecks as Rust binaries called via subprocess. The Python server stays — only the hot paths move to Rust.

### 3.1 Profiling

- [ ] Add timing instrumentation to `indexer.py` (log time per stage: walk, parse, chunk, embed, store)
- [ ] Run against a large vault (500+ notes) and record baseline numbers
- [ ] Confirm `chunker.py` and `top_k_search` in `sqlite.py` are the bottlenecks before rewriting

### 3.2 Rust Chunker (`oxidian-chunk`)

- [ ] Create `oxidian-chunk/` Cargo crate
- [ ] Accept input via stdin as JSON array of `{path, text, headings[]}`
- [ ] Output chunked result as JSON array of `Chunk` objects to stdout
- [ ] Implement same heading-aware, token-bounded chunking logic as `chunker.py` (use `tiktoken-rs`)
- [ ] Update `core/ingest/chunker.py` to detect `oxidian-chunk` binary and delegate via subprocess if present, else fall back to Python implementation
- [ ] Benchmark: compare throughput (notes/sec) Python vs Rust chunker

### 3.3 Rust Vector Search (`oxidian-search`)

- [ ] Create `oxidian-search/` Cargo crate
- [ ] Load all vectors from `oxidian.db` into memory at startup
- [ ] Implement cosine similarity with SIMD (`packed_simd` or `std::simd`)
- [ ] Accept query vector via stdin, return top-k results as JSON to stdout
- [ ] Update `core/store/sqlite.py` to call `oxidian-search` via subprocess if binary present
- [ ] Benchmark: compare latency (ms/query) sqlite-vec vs Rust SIMD

---

## Phase 4 — Web UI

**Goal:** A minimal single-file web frontend served directly by FastAPI. No build step, no framework — just HTML, CSS, and vanilla JS.

- [ ] Create `core/server/static/index.html` — single-file UI
- [ ] Input box for question, submit button
- [ ] Consume SSE stream and render tokens progressively
- [ ] Display citations list after `done` event with links to source files
- [ ] Mount static files in `app.py` at `/`
- [ ] Add `GET /` route that serves `index.html`

---

## Phase 5 — Obsidian Plugin

**Goal:** A TypeScript Obsidian plugin that adds a sidebar panel and calls the local Oxidian API. Requires the Python core to be running locally.

- [ ] Create `obsidian-plugin/` directory with standard Obsidian plugin scaffold (`manifest.json`, `main.ts`, `styles.css`)
- [ ] Add dependencies: `obsidian` types, `esbuild` for bundling
- [ ] Implement sidebar leaf panel with question input and answer view
- [ ] Call `POST /query` with `stream: true`, render SSE tokens progressively in the panel
- [ ] Render citations as clickable links that open the source note in Obsidian
- [ ] Settings tab: configurable `server_url` (default `http://localhost:3000`)
- [ ] Use FastAPI's auto-generated OpenAPI spec for type-safe client generation

---

## Phase 6 — Fully Local Mode

**Goal:** Allow Oxidian to run with zero cloud API calls using Ollama for both embeddings and generation.

- [ ] Verify `embed/client.py` Ollama path works end-to-end with `nomic-embed-text`
- [ ] Add Ollama LLM backend to `core/query/llm.py` (streaming via Ollama's API)
- [ ] Update `config.example.toml` with fully-local example configuration
- [ ] Document local-only setup in README (no API keys required)
- [ ] Test full pipeline: index + query with no network egress

---

## Ongoing

- [ ] Keep `config.example.toml` in sync with any new config keys
- [ ] Update `README.md` API reference if routes change
- [ ] Add `CHANGELOG.md` entries at each phase completion
- [ ] Ensure all Rust binaries are optional — Python core must work without them
