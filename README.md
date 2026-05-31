# RAG Video Comparator (YouTube vs Instagram)

This is a production-style, full-stack RAG chatbot that ingests **two social video URLs** (one YouTube, one Instagram Reel), stores transcript chunks + metadata in **ChromaDB**, and exposes a **streaming** chat UI where creators can ask comparative questions with **citations** back to transcript chunks.

It’s built for the “creator analytics” workflow: *what worked, why it worked, and how to replicate it—without hallucinating numbers.*

---

## Architecture (high level)

```
           ┌──────────────────────────┐
           │        Frontend          │
           │  React + Vite            │
           │  EventSource (SSE)       │
           └───────────┬──────────────┘
                       │ /ingest (POST)
                       │ /stream (GET, SSE)
                       ▼
           ┌──────────────────────────┐
           │        Backend           │
           │ FastAPI                  │
           │                          │
           │ ingest.py                │
           │  - YouTube transcript API│
           │  - yt-dlp metadata       │
           │  - Instagram audio dl    │
           │  - Whisper (base)        │
           │  - Chunk + embed         │
           │                          │
           │ LangGraph (graph.py)     │
           │  START → retrieve → LLM  │
           │  MemorySaver per session │
           └───────────┬──────────────┘
                       │ vector ops
                       ▼
           ┌──────────────────────────┐
           │        ChromaDB          │
           │  collection: "videos"   │
           │  filter: video_id in A,B │
           └──────────────────────────┘
```

---

## Setup (step-by-step)

### 0) Prereqs

- Python 3.11+
- Node 18+
- `yt-dlp` will be installed via pip requirements (used as a CLI under the hood)

### 1) Configure env vars

1. Copy the example env file:

   ```bash
   cp .env.example .env
   ```

2. Set your OpenAI key in `.env`:

   ```bash
   OPENAI_API_KEY=...
   ```

### 2) Run ChromaDB + backend (Docker Compose)

From the repo root:

```bash
docker compose up --build
```

The backend will be available at:

- http://localhost:8000/health

ChromaDB (server) will be on:

- http://localhost:8001

### 3) Run the frontend (local dev)

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the printed dev URL (typically http://localhost:5173).

### 4) Use it

1. Paste a **YouTube** URL into Video A.
2. Paste an **Instagram Reel** URL into Video B.
3. Click **Analyze Videos** (this can take time if Whisper has to transcribe).
4. Ask comparative questions, e.g.:
   - “Which video has a stronger hook and what exactly do they do in the first 10 seconds?”
   - “How do their CTAs differ, and what’s the likely effect on engagement?”

---

## Why these tech choices

### Why LangGraph over LangChain?

LangGraph forces you to define a graph with explicit state + edges. That matters for “shipping to prod” because:

- You can make retrieval and generation distinct nodes with clear inputs/outputs.
- Streaming becomes a first-class concern (message chunk reducers + streamed node output).
- Memory is handled via checkpointers (here: `MemorySaver`), so you can swap to Redis/Postgres later without rewriting your agent logic.

### Why ChromaDB for this scale?

For “two videos per session” workloads, ChromaDB is perfect:

- Local persistence for dev (`PersistentClient`)
- Easy server mode in docker-compose (`HttpClient`)
- Simple metadata filtering (`where={"video_id": {"$in": ["A","B"]}}`)

### Why GPT-4o-mini (not GPT-4o)?

Because this app’s core value is *analysis grounded in retrieval + metadata*, not raw reasoning depth. GPT-4o-mini is:

- Fast enough to stream well in a UX people will actually use
- Cheap enough to run at creator-scale without surprise bills

According to OpenAI’s model card pricing, **GPT-4o-mini** is **$0.15 / 1M input tokens** and **$0.60 / 1M output tokens**.  
Source: https://platform.openai.com/docs/models/gpt-4o-mini

### Why 300-token chunks with 50 overlap?

It’s a pragmatic “production default”:

- 300 tokens keeps chunks semantically focused (good for pinpoint citations like hooks/CTAs)
- 50-token overlap reduces boundary loss when a key idea spans the split
- Token-based chunking is stable across emojis/URLs/hashtags vs character chunking

---

## Cost analysis (example @ 1,000 creators/day)

Assumptions (you should replace these with your real analytics):

- Each creator ingests 2 videos/day (A + B).
- Average transcript length: ~2,000 tokens per video (YouTube is usually larger; IG varies a lot).
- Each creator asks 5 chat questions.
- Each chat question uses ~2,500 input tokens (system prompt + metadata + retrieved context + short history) and ~400 output tokens.

### Embeddings

- 1,000 creators/day × 2 videos × 2,000 tokens ≈ **4,000,000 tokens/day**
- text-embedding-3-small costs **$0.02 / 1M tokens**

Estimated embeddings cost/day:

```
4.0M / 1M * $0.02 ≈ $0.08/day
```

Source (text-embedding-3-small): https://platform.openai.com/docs/models/text-embedding-3-small

### Chat

Calls/day: 1,000 × 5 = **5,000**

Input tokens/day: 5,000 × 2,500 = **12,500,000**

Output tokens/day: 5,000 × 400 = **2,000,000**

Estimated chat cost/day:

```
Input: 12.5M / 1M * $0.15 ≈ $1.875/day
Output: 2.0M / 1M * $0.60 ≈ $1.20/day
Total ≈ $3.08/day
```

Ballpark total/day (chat + embeddings): **~$3.16/day**, or **~$95/month** (30-day month).

---

## What breaks at 10,000 users (and how to fix it)

At 10k daily creators, the core issues are not “LLM prompts” — they’re *throughput, durability, and multi-tenant isolation*:

1. **Whisper transcription throughput**
   - Problem: CPU transcription becomes a hard bottleneck and spikes ingest latency.
   - Fix: move ingest to a background job queue (Celery/RQ/Temporal), add GPU workers, and return an async job status to the UI.

2. **In-memory session metadata**
   - Problem: backend restarts drop sessions; horizontal scaling makes sessions inconsistent.
   - Fix: store session metadata in Redis/Postgres keyed by session_id; also persist LangGraph checkpoints there.

3. **ChromaDB single-node limits**
   - Problem: local Chroma works great for small deployments, but one node will bottleneck on I/O and memory.
   - Fix: move to a managed/distributed vector DB (or shard by creator/org), add eviction/TTL policies, and implement index lifecycle management.

4. **No per-creator auth / tenancy**
   - Problem: production needs access control and rate limiting.
   - Fix: add auth (JWT), rate limiting, per-org namespaces in vector storage, and request logging/metrics.

---

## Known limitations

- **Instagram ingestion is brittle**: scraping metadata depends on yt-dlp extractors, which can break when IG changes. This build follows the constraint to use yt-dlp + Whisper, but you should expect operational maintenance.
- **Whisper latency**: even with the “base” model, transcription can take seconds to minutes depending on hardware and audio length.
- **Metadata completeness varies**: follower count and comment count are often missing for IG; the backend normalizes missing fields to `null` instead of failing.

---

## Commit message suggestion

`"Add README with architecture, setup, cost analysis, and scaling notes"`
