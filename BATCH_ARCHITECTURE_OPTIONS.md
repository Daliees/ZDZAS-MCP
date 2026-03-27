# ZAS Batch Processing — Architecture Options

> **Context:** The ZAS agent currently processes requests synchronously. When you ask it to analyze 25 tickets, the entire `/chat` endpoint blocks until all 25 are done. You can't ask questions while the batch runs, and HTTP timeouts become a real risk.
>
> This document outlines 3 implementation options to solve this. Each option enables:
> - Processing tickets 1-by-1 in the background
> - Chatting with the agent while the batch is running
> - Tracking progress ("hoe ver ben je?")
> - Cancelling a running batch

---

## Current Architecture (Problem)

```
Browser Extension → POST /chat → run_zas_chat_turn() → Runner.run(zas, ...) → [blocks for ALL 25 tickets] → response
                                                                                    ↑
                                                                            User cannot interact
                                                                            during this time
```

**Files involved:**
- `chat_api.py` — FastAPI server on port 9000, handles `/chat`
- `zas_agent.py` — OpenAI Agents SDK, `run_zas_chat_turn()` calls `Runner.run()`
- `app.py` — FastMCP server on port 8000, exposes Zendesk/Jira/Confluence tools
- `core.py` — Env config, HTTP helpers
- `ecosystem.config.js` — PM2 runs `ZDZAS-mcp` and `ZDZAS-chat`

---

## Option A — In-Process asyncio Background Tasks (Recommended)

**Complexity:** Low · **New deps:** 0 · **Files changed:** 3 + 1 new · **Time to implement:** ~2 hours

### How It Works

The FastAPI server (`chat_api.py`) spawns a background `asyncio.Task` that loops through tickets one-by-one. The `/chat` endpoint returns immediately with a confirmation. A shared in-memory `dict` tracks job state so the user can ask about progress or get results.

```
POST /chat "analyseer 25 tickets"
    ↓
chat_api detects batch intent
    ↓
Creates BatchJob in memory → asyncio.create_task(run_batch)
    ↓
Returns immediately: "Batch gestart, 25 tickets. Stel vragen terwijl ik werk."
    ↓                                           ↓
User keeps chatting normally          Background task processes ticket 1...2...3...
    ↓                                           ↓
POST /chat "hoe ver ben je?"          Updates job.completed, job.current_ticket
    ↓                                           ↓
Returns: "12/25 klaar"               Appends each result to job.results
    ↓                                           ↓
POST /chat "geef resultaten"          job.status = "done" when finished
```

### New/Changed Files

| File | Action | Description |
|------|--------|-------------|
| `batch_jobs.py` | **NEW** | `BatchJob` dataclass + in-memory store + JSONL persistence |
| `zas_agent.py` | EDIT | Add `run_zas_batch_analysis()` — loops tickets 1-by-1 |
| `chat_api.py` | EDIT | Add `/batch/start`, `GET /batch/{job_id}`, `/batch/{job_id}/cancel` endpoints + auto-detect batch in `/chat` |
| Agent instructions | EDIT | Tell agent about batch capabilities |

### batch_jobs.py (New File)

```python
from __future__ import annotations
import json, os, uuid
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class BatchJob:
    job_id: str
    conversation_id: str
    status: str  # "pending" | "running" | "done" | "failed" | "cancelled"
    ticket_ids: list[int]
    completed: int = 0
    current_ticket: int | None = None
    results: list[dict] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = ""

# In-memory store
batch_store: dict[str, BatchJob] = {}

BATCH_LOG_PATH = os.getenv("ZAS_BATCH_LOG", "zas_batch_log.jsonl")

def create_batch_job(ticket_ids: list[int], conversation_id: str) -> BatchJob:
    job = BatchJob(
        job_id=f"batch_{uuid.uuid4().hex[:12]}",
        conversation_id=conversation_id,
        status="pending",
        ticket_ids=ticket_ids,
    )
    batch_store[job.job_id] = job
    return job

def get_batch_job(job_id: str) -> BatchJob | None:
    return batch_store.get(job_id)

def get_active_batch(conversation_id: str) -> BatchJob | None:
    for job in batch_store.values():
        if job.conversation_id == conversation_id and job.status in ("pending", "running"):
            return job
    return None

def persist_job(job: BatchJob):
    """Append current job state to JSONL for crash recovery."""
    job.updated_at = datetime.utcnow().isoformat()
    record = {
        "job_id": job.job_id,
        "status": job.status,
        "completed": job.completed,
        "total": len(job.ticket_ids),
        "updated_at": job.updated_at,
    }
    with open(BATCH_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
```

### zas_agent.py — New Function

```python
async def run_zas_batch_analysis(job: BatchJob) -> None:
    """Process tickets 1-by-1 in the background, updating job state after each."""
    from batch_jobs import persist_job

    job.status = "running"
    for ticket_id in job.ticket_ids:
        if job.status == "cancelled":
            break

        job.current_ticket = ticket_id
        try:
            prompt = (
                f"Analyseer ticket #{ticket_id}: "
                f"haal het op met ticket_get, lees comments met ticket_comments, "
                f"zoek relevante KB artikelen met kb_search_articles, "
                f"en geef een beknopte samenvatting met: probleem, status, prioriteit, advies."
            )
            reply, _ = await run_zas_chat_turn(prompt, history=[])
            job.results.append({"ticket_id": ticket_id, "analysis": reply, "ok": True})
        except Exception as e:
            job.errors.append({"ticket_id": ticket_id, "error": str(e)})

        job.completed += 1
        persist_job(job)

    if job.status != "cancelled":
        job.status = "done"
    job.current_ticket = None
    persist_job(job)
```

### chat_api.py — New Endpoints

```python
import asyncio
from batch_jobs import (
    create_batch_job, get_batch_job, get_active_batch, BatchJob
)
from zas_agent import run_zas_batch_analysis

# --- POST /batch/start ---
class BatchStartRequest(BaseModel):
    ticket_ids: list[int]
    conversationId: Optional[str] = None

@app.post("/batch/start")
async def batch_start(req: BatchStartRequest, x_session_id: Optional[str] = Header(None)):
    conv_id = req.conversationId or x_session_id or str(uuid.uuid4())

    # Only 1 active batch per conversation
    active = get_active_batch(conv_id)
    if active:
        raise HTTPException(400, f"Er loopt al een batch: {active.job_id}")

    job = create_batch_job(req.ticket_ids, conv_id)
    asyncio.create_task(run_zas_batch_analysis(job))

    return {
        "job_id": job.job_id,
        "total": len(job.ticket_ids),
        "status": "running",
        "message": f"Batch gestart: {len(job.ticket_ids)} tickets worden 1-voor-1 geanalyseerd."
    }

# --- GET /batch/{job_id} ---
@app.get("/batch/{job_id}")
async def batch_status(job_id: str):
    job = get_batch_job(job_id)
    if not job:
        raise HTTPException(404, "Batch niet gevonden")
    return {
        "job_id": job.job_id,
        "status": job.status,
        "total": len(job.ticket_ids),
        "completed": job.completed,
        "current_ticket": job.current_ticket,
        "results": job.results,
        "errors": job.errors,
    }

# --- POST /batch/{job_id}/cancel ---
@app.post("/batch/{job_id}/cancel")
async def batch_cancel(job_id: str):
    job = get_batch_job(job_id)
    if not job:
        raise HTTPException(404, "Batch niet gevonden")
    job.status = "cancelled"
    return {"status": "cancelled", "completed": job.completed}
```

### Auto-Detection in `/chat`

```python
import re
BATCH_PATTERN = re.compile(
    r"(?:analyseer|analyze|bekijk)\s+.*?tickets?\s*[:#]?\s*([\d,\s]+)", re.I
)

# Inside the /chat handler, before calling run_zas_chat_turn:
match = BATCH_PATTERN.search(req.message)
if match:
    ids = [int(x.strip()) for x in match.group(1).split(",") if x.strip().isdigit()]
    if len(ids) > 3:
        job = create_batch_job(ids, conv_id)
        asyncio.create_task(run_zas_batch_analysis(job))
        return ChatResponse(
            reply=f"Batch gestart: {len(ids)} tickets worden 1-voor-1 geanalyseerd. "
                  f"Job ID: {job.job_id}. Je kunt gewoon vragen blijven stellen!",
            conversationId=conv_id,
        )
```

### Pros & Cons

| ✅ Pros | ❌ Cons |
|---------|---------|
| Zero new dependencies | Job state lost on process crash (mitigated by JSONL) |
| Works with existing OpenAI Agents SDK | Single uvicorn worker only |
| Simple, fast to implement | No built-in retry for failed tickets |
| Native asyncio — no threading issues | |
| User can chat normally while batch runs | |

---

## Option B — Separate PM2 Worker + SQLite Queue

**Complexity:** Medium · **New deps:** 0 (sqlite3 is stdlib) · **Files changed:** 5 + 1 new · **Time to implement:** ~4 hours

### How It Works

A dedicated PM2-managed worker process polls a SQLite database for pending batch jobs. The chat server writes jobs to SQLite; the worker reads and processes them. Both sides read/write the same database for status tracking.

```
┌─────────────────────────────────────────────────────┐
│                    PM2 Managed                       │
│                                                      │
│  ZDZAS-mcp       ZDZAS-chat        ZDZAS-worker     │
│  (app.py :8000)  (chat_api.py :9000) (batch_worker.py) │
│                       │                    │          │
│                       │   INSERT job       │          │
│                       ├──────────────►     │          │
│                       │              ┌─────┴─────┐   │
│                       │              │  SQLite    │   │
│                       │              │  batch.db  │   │
│                       │              └─────┬─────┘   │
│                       │   SELECT status    │          │
│                       ├───────────────────►│          │
│                       │                    │          │
│                       │    SELECT pending  │          │
│                       │    ◄───────────────┤          │
│                       │    UPDATE progress │          │
│                       │    ◄───────────────┤          │
└─────────────────────────────────────────────────────┘
```

### New/Changed Files

| File | Action | Description |
|------|--------|-------------|
| `batch_store.py` | **NEW** | SQLite wrapper: `create_job()`, `get_job()`, `update_progress()`, `mark_done()` |
| `batch_worker.py` | **NEW** | Standalone process: polls SQLite, processes tickets via `Runner.run()` |
| `chat_api.py` | EDIT | New endpoints that write/read SQLite |
| `zas_agent.py` | EDIT | Batch analysis function (shared with worker) |
| `ecosystem.config.js` | EDIT | Add `ZDZAS-worker` app |
| `run_worker.sh` | **NEW** | Shell wrapper for PM2 |

### batch_store.py (New File)

```python
import sqlite3, json, uuid, os
from datetime import datetime

DB_PATH = os.getenv("ZAS_BATCH_DB", "batch_jobs.db")

def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # safe for concurrent reads
    return conn

def init_db():
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                conversation_id TEXT,
                status TEXT DEFAULT 'pending',
                ticket_ids TEXT,         -- JSON array
                completed INTEGER DEFAULT 0,
                current_ticket INTEGER,
                results TEXT DEFAULT '[]', -- JSON array
                errors TEXT DEFAULT '[]',  -- JSON array
                created_at TEXT,
                updated_at TEXT
            )
        """)

def create_job(ticket_ids: list[int], conversation_id: str) -> dict:
    job_id = f"batch_{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow().isoformat()
    with _conn() as c:
        c.execute(
            "INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?)",
            (job_id, conversation_id, "pending", json.dumps(ticket_ids),
             0, None, "[]", "[]", now, now)
        )
    return {"job_id": job_id, "total": len(ticket_ids)}

def get_job(job_id: str) -> dict | None:
    with _conn() as c:
        row = c.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
    if not row:
        return None
    return {**dict(row), "ticket_ids": json.loads(row["ticket_ids"]),
            "results": json.loads(row["results"]), "errors": json.loads(row["errors"])}

def next_pending() -> dict | None:
    with _conn() as c:
        row = c.execute("SELECT * FROM jobs WHERE status='pending' ORDER BY created_at LIMIT 1").fetchone()
    if not row:
        return None
    return {**dict(row), "ticket_ids": json.loads(row["ticket_ids"])}

def update_progress(job_id: str, completed: int, current_ticket: int | None,
                    results: list, errors: list, status: str = "running"):
    now = datetime.utcnow().isoformat()
    with _conn() as c:
        c.execute("""
            UPDATE jobs SET status=?, completed=?, current_ticket=?,
                           results=?, errors=?, updated_at=?
            WHERE job_id=?
        """, (status, completed, current_ticket, json.dumps(results),
              json.dumps(errors), now, job_id))

init_db()
```

### batch_worker.py (New File)

```python
#!/usr/bin/env python
"""Standalone batch worker — runs as separate PM2 process."""
import asyncio, time
from batch_store import next_pending, update_progress, get_job
from zas_agent import run_zas_chat_turn

POLL_INTERVAL = 5  # seconds

async def process_job(job: dict):
    job_id = job["job_id"]
    ticket_ids = job["ticket_ids"]
    results, errors = [], []

    for i, ticket_id in enumerate(ticket_ids):
        # Check if cancelled
        current = get_job(job_id)
        if current and current["status"] == "cancelled":
            break

        try:
            prompt = f"Analyseer ticket #{ticket_id}: haal op, lees comments, zoek KB, geef samenvatting."
            reply, _ = await run_zas_chat_turn(prompt, history=[])
            results.append({"ticket_id": ticket_id, "analysis": reply, "ok": True})
        except Exception as e:
            errors.append({"ticket_id": ticket_id, "error": str(e)})

        update_progress(job_id, i + 1, ticket_id, results, errors)

    final_status = "done" if (not current or current["status"] != "cancelled") else "cancelled"
    update_progress(job_id, len(results) + len(errors), None, results, errors, status=final_status)

async def main():
    print("[BATCH WORKER] Started, polling for jobs...")
    while True:
        job = next_pending()
        if job:
            print(f"[BATCH WORKER] Processing {job['job_id']} ({len(job['ticket_ids'])} tickets)")
            update_progress(job["job_id"], 0, None, [], [], status="running")
            await process_job(job)
        else:
            await asyncio.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())
```

### ecosystem.config.js Change

```javascript
module.exports = {
  apps: [
    { name: "ZDZAS-mcp",    script: "run_mcp.sh",    /* ... */ },
    { name: "ZDZAS-chat",   script: "run_chat.sh",   /* ... */ },
    { name: "ZDZAS-worker", script: "run_worker.sh", /* ... */ },  // NEW
  ],
};
```

### Pros & Cons

| ✅ Pros | ❌ Cons |
|---------|---------|
| Jobs survive PM2 restarts (SQLite) | More files to maintain |
| Worker is isolated — can't crash chat server | SQLite locking under high concurrent writes |
| Clean separation of concerns | 5s polling delay before job starts |
| Can scale to multiple workers later | Need to share `zas_agent.py` imports in worker |
| Zero new external dependencies | |

---

## Option C — Redis Queue + Background Worker (Production-Grade)

**Complexity:** High · **New deps:** `redis`, `aioredis` · **Files changed:** 5+ · **Time to implement:** ~8 hours

### How It Works

Redis acts as both the job queue and pub/sub bus. A dedicated worker process consumes jobs from a Redis list. Progress updates are published via Redis pub/sub and can be streamed to the extension via SSE (Server-Sent Events).

```
┌─────────────────────────────────────────────────────────────┐
│                       PM2 Managed                            │
│                                                              │
│  ZDZAS-mcp        ZDZAS-chat           ZDZAS-worker          │
│  (app.py :8000)   (chat_api.py :9000)  (batch_worker.py)    │
│                       │                      │               │
│                       │  LPUSH job           │               │
│                       ├──────────┐           │               │
│                       │          ▼           │               │
│                       │   ┌───────────┐     │               │
│                       │   │   Redis    │◄────┤ BRPOP job    │
│                       │   │           │     │               │
│                       │   │  pub/sub  │────►│ progress      │
│                       │   └───────────┘     │               │
│                       │          │           │               │
│                       │  GET status          │               │
│                       ├──────────┘           │               │
│                       │                      │               │
│                       │  SSE /batch/stream   │               │
│                       ├──────────────────────►Extension      │
└─────────────────────────────────────────────────────────────┘
```

### New/Changed Files

| File | Action | Description |
|------|--------|-------------|
| `batch_queue.py` | **NEW** | Redis wrapper: `enqueue_job()`, `get_status()`, `publish_progress()` |
| `batch_worker.py` | **NEW** | `BRPOP` loop, processes tickets, publishes progress |
| `chat_api.py` | EDIT | New endpoints + SSE streaming endpoint |
| `zas_agent.py` | EDIT | Batch analysis function |
| `ecosystem.config.js` | EDIT | Add worker + Redis service |
| `requirements.txt` | EDIT | Add `redis>=5.0` |

### batch_queue.py (New File)

```python
import redis, json, uuid, os
from datetime import datetime

r = redis.Redis(
    host=os.getenv("REDIS_HOST", "127.0.0.1"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True,
)

QUEUE_KEY = "zas:batch:queue"
JOB_PREFIX = "zas:batch:job:"
CHANNEL_PREFIX = "zas:batch:progress:"

def enqueue_job(ticket_ids: list[int], conversation_id: str) -> str:
    job_id = f"batch_{uuid.uuid4().hex[:12]}"
    job_data = {
        "job_id": job_id,
        "conversation_id": conversation_id,
        "ticket_ids": ticket_ids,
        "status": "pending",
        "completed": 0,
        "total": len(ticket_ids),
        "results": [],
        "errors": [],
        "created_at": datetime.utcnow().isoformat(),
    }
    r.set(f"{JOB_PREFIX}{job_id}", json.dumps(job_data))
    r.lpush(QUEUE_KEY, job_id)
    return job_id

def get_status(job_id: str) -> dict | None:
    data = r.get(f"{JOB_PREFIX}{job_id}")
    return json.loads(data) if data else None

def update_job(job_id: str, **fields):
    data = get_status(job_id)
    if data:
        data.update(fields)
        r.set(f"{JOB_PREFIX}{job_id}", json.dumps(data))
        # Publish progress event
        r.publish(f"{CHANNEL_PREFIX}{job_id}", json.dumps({
            "completed": data.get("completed", 0),
            "total": data.get("total", 0),
            "current_ticket": fields.get("current_ticket"),
            "status": data.get("status"),
        }))
```

### SSE Streaming Endpoint (chat_api.py)

```python
from fastapi.responses import StreamingResponse

@app.get("/batch/{job_id}/stream")
async def batch_stream(job_id: str):
    """Server-Sent Events: real-time batch progress."""
    import aioredis

    async def event_generator():
        redis = aioredis.from_url("redis://127.0.0.1:6379")
        pubsub = redis.pubsub()
        await pubsub.subscribe(f"zas:batch:progress:{job_id}")

        async for message in pubsub.listen():
            if message["type"] == "message":
                yield f"data: {message['data']}\n\n"
                data = json.loads(message["data"])
                if data.get("status") in ("done", "failed", "cancelled"):
                    break

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

### Extension Integration (popup.js)

```javascript
const evtSource = new EventSource(`${API_URL}/batch/${jobId}/stream`);
evtSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    updateProgressBar(data.completed, data.total);
    if (data.status === "done") evtSource.close();
};
```

### Pros & Cons

| ✅ Pros | ❌ Cons |
|---------|---------|
| Real-time progress via SSE/pub-sub | Requires Redis server running |
| Battle-tested at scale | Most complex to implement and maintain |
| Jobs persist in Redis (survives all crashes) | New dependency: `redis` / `aioredis` |
| Multiple workers possible | Overkill for single-user setup |
| Production-grade architecture | Extension needs SSE support changes |

---

## Side-by-Side Comparison

| Aspect | **A: asyncio Task** | **B: PM2 Worker + SQLite** | **C: Redis Queue** |
|--------|---------------------|---------------------------|-------------------|
| New dependencies | **0** | **0** | redis, aioredis |
| New files | 1 | 3 | 4+ |
| Survives PM2 restart | JSONL (partial) | **Yes (SQLite)** | **Yes (Redis)** |
| Crash isolation | No (same process) | **Yes (separate worker)** | **Yes** |
| Real-time progress | Poll via `/chat` | Poll via endpoint | **SSE streaming** |
| Concurrency | Single process | Multi-process capable | **Multi-worker** |
| Implementation time | **~2 hours** | ~4 hours | ~8 hours |
| Best for | **This project now** | Growing to production | Multi-user scale |
| Extension changes | None | None | SSE support needed |

---

## Investigation: LangChain / LangGraph

I also researched whether LangChain or LangGraph has a built-in solution:

| LangChain/LangGraph Feature | Background? | Progress? | Chat While Running? | Verdict |
|------------------------------|-------------|-----------|---------------------|---------|
| `Runnable.batch()` / `.abatch()` | ❌ Blocking | ❌ | ❌ | **No fit** |
| LangGraph Orchestrator-Worker + `Send` | ❌ Blocking graph call | Via streaming | ❌ | **Partial** |
| LangGraph Persistence + Checkpointing | Survives crashes | State per step | ❌ Still blocks | **Partial** |
| LangGraph Streaming (`custom` mode) | ❌ | ✅ Real-time | ❌ | **Partial** |
| LangSmith Cloud Background Runs | ✅ | ✅ | ✅ | **Yes, but paid hosted service** |

**Conclusion:** LangChain/LangGraph OSS doesn't solve the "run batch in background while chat stays responsive" problem. Their open-source `batch()` and orchestrator-worker patterns still block the calling code. Only LangSmith Cloud (paid) has true background runs, and it would require rewriting the agent from OpenAI Agents SDK to LangGraph — a major refactor with no clear benefit for this project's scale.

**All three options (A/B/C) work with the existing OpenAI Agents SDK — no rewrite needed.**

---

## My Recommendation

**Start with Option A.** Zero deps, minimal changes, solves the problem immediately. If you later need crash recovery or multi-process isolation, swap the in-memory store for SQLite (upgrade to Option B) — the API surface stays the same.
