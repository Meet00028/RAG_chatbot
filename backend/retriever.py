from __future__ import annotations

import os
from typing import Any, Dict, List

import chromadb
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential_jitter


def _openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)


@retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(initial=0.5, max=4))
def _embed_query(query: str) -> List[float]:
    """
    Query embedding is a critical online path; retries reduce p95 tail latency
    from transient upstream failures.
    """
    client = _openai_client()
    try:
        resp = client.embeddings.create(model="text-embedding-3-small", input=query)
        return resp.data[0].embedding
    except Exception as e:
        raise RuntimeError(f"OpenAI embeddings request failed: {e}") from e


def _get_chroma_collection():
    persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    host = os.getenv("CHROMA_HOST")
    port = os.getenv("CHROMA_PORT")

    try:
        if host and port:
            client = chromadb.HttpClient(host=host, port=int(port))
        else:
            client = chromadb.PersistentClient(path=persist_dir)
        return client.get_or_create_collection(name="videos")
    except Exception as e:
        raise RuntimeError(f"ChromaDB initialization failed: {e}") from e


def retrieve(query: str, video_ids: List[str], n_results: int = 6) -> List[Dict[str, Any]]:
    """
    Returns nearest transcript chunks filtered by video_id, keeping the result
    shape simple for prompt assembly and front-end citation rendering.
    """
    if not query.strip():
        return []
    if not video_ids:
        return []

    embedding = _embed_query(query)
    collection = _get_chroma_collection()

    try:
        res = collection.query(
            query_embeddings=[embedding],
            n_results=n_results,
            where={"video_id": {"$in": video_ids}},
            include=["documents", "metadatas", "distances"],
        )
    except Exception as e:
        raise RuntimeError(f"ChromaDB query failed: {e}") from e

    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]

    out: List[Dict[str, Any]] = []
    for doc, meta, dist in zip(docs, metas, dists):
        out.append({"content": doc, "metadata": meta or {}, "distance": float(dist)})
    return out


# Commit message suggestion:
#   "Add ChromaDB retriever with video_id filtering"
