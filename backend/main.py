from __future__ import annotations

import asyncio
import uuid
from typing import Any, AsyncGenerator, Dict

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

import graph
import ingest
from models import HealthResponse, IngestRequest, IngestResponse, VideoMetadata


load_dotenv()

app = FastAPI(title="Video RAG Chatbot", version="1.0.0")

# Local dev: creators will run the React dev server on a different origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# In-memory session store is intentionally simple for this build. In production
# you'd persist in Redis/Postgres to survive restarts and allow horizontal scale.
SESSION_METADATA: Dict[str, Dict[str, Any]] = {}


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/ingest", response_model=IngestResponse)
def ingest_route(payload: IngestRequest) -> IngestResponse:
    try:
        meta = ingest.ingest_videos(str(payload.url_a), str(payload.url_b))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        # Keep error details for local dev; in production you'd log and return a generic message.
        raise HTTPException(status_code=500, detail=str(e)) from e

    session_id = str(uuid.uuid4())
    SESSION_METADATA[session_id] = meta

    return IngestResponse(
        session_id=session_id,
        video_a=VideoMetadata(**meta["video_a"]),
        video_b=VideoMetadata(**meta["video_b"]),
    )


def _sse(data: str) -> str:
    return f"data: {data}\n\n"


@app.get("/stream")
async def stream_route(
    session_id: str = Query(...),
    query: str = Query(...),
):
    if session_id not in SESSION_METADATA:
        raise HTTPException(status_code=404, detail="Unknown session_id; ingest first")

    video_metadata = SESSION_METADATA[session_id]

    async def event_gen() -> AsyncGenerator[str, None]:
        try:
            async for token in graph.run_graph_streaming(
                query=query, session_id=session_id, video_metadata=video_metadata
            ):
                # SSE expects UTF-8 strings; we stream token-by-token for minimal latency.
                yield _sse(token)

            yield _sse("[DONE]")
        except Exception as e:
            # Client-side can render this like a normal assistant message.
            yield _sse(f"[ERROR] {str(e)}")
            yield _sse("[DONE]")
        finally:
            # Give the network loop a moment to flush the last chunk before teardown.
            await asyncio.sleep(0)

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
    }
    return StreamingResponse(event_gen(), media_type="text/event-stream", headers=headers)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_, exc: Exception):
    # One last guardrail so unexpected crashes still return JSON.
    return JSONResponse(status_code=500, content={"detail": str(exc)})


# Commit message suggestion:
#   "Add FastAPI app with ingest endpoint and SSE streaming chat route"
