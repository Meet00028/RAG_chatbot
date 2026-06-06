from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

import chromadb
import tiktoken
import whisper
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential_jitter
from youtube_transcript_api import YouTubeTranscriptApi

from utils import engagement_rate, normalize_yt_dlp_metadata, safe_int, safe_str


_ENCODING = tiktoken.get_encoding("cl100k_base")
_WHISPER_MODEL: Optional[Any] = None


def _is_youtube(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return "youtube.com" in host or "youtu.be" in host


def _is_instagram(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return "instagram.com" in host


def _extract_youtube_video_id(url: str) -> str:
    """
    We extract IDs using URL parsing rather than regexes to avoid subtly broken
    behavior across shorts/watch/playlist formats.
    """
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()

    if "youtu.be" in host:
        vid = parsed.path.strip("/").split("/")[0]
        if vid:
            return vid

    qs = parse_qs(parsed.query)
    if "v" in qs and qs["v"]:
        return qs["v"][0]

    # Fallback for /shorts/<id> or other path-based URLs
    parts = [p for p in parsed.path.split("/") if p]
    for i, p in enumerate(parts):
        if p in {"shorts", "embed"} and i + 1 < len(parts) and parts[i + 1]:
            return parts[i + 1]

    raise ValueError("Could not extract YouTube video ID from URL")


def _run_yt_dlp_json(url: str) -> Dict[str, Any]:
    """
    yt-dlp is a non-Python dependency boundary; we treat it as an untrusted
    process and capture stdout/stderr for good operator debugging.
    """
    cmd = ["yt-dlp", "-J", "--no-warnings", "--no-playlist", "--skip-download", url]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except Exception as e:
        raise RuntimeError(f"yt-dlp failed to execute: {e}") from e

    if proc.returncode != 0:
        raise RuntimeError(f"yt-dlp error ({proc.returncode}): {proc.stderr.strip()}")

    try:
        return json.loads(proc.stdout)
    except Exception as e:
        raise RuntimeError("yt-dlp returned invalid JSON") from e


def _ensure_whisper_model() -> Any:
    """
    Whisper model load is slow; caching it at module-level prevents per-request
    reloads that would destroy latency under concurrent creators.
    Use "tiny" model for free tiers with limited RAM!
    """
    global _WHISPER_MODEL
    if _WHISPER_MODEL is None:
        _WHISPER_MODEL = whisper.load_model("tiny")
    return _WHISPER_MODEL


def _youtube_transcript_text(url: str) -> str:
    video_id = _extract_youtube_video_id(url)
    try:
        # youtube-transcript-api v1+ moved away from static/class methods and
        # intentionally requires an instance (it owns a requests.Session and is
        # not thread-safe). Creating it per call avoids cross-request leakage.
        fetched = YouTubeTranscriptApi().fetch(video_id)
    except Exception as e:
        raise RuntimeError(f"Failed to fetch YouTube transcript: {e}") from e

    text_parts: List[str] = []
    for snippet in fetched:
        t = safe_str(getattr(snippet, "text", ""), default="").strip()
        if t:
            text_parts.append(t)
    transcript_text = " ".join(text_parts).strip()
    if not transcript_text:
        raise RuntimeError("YouTube transcript returned empty text")
    return transcript_text


def _instagram_transcript_text(url: str) -> str:
    """
    Instagram has no reliable public transcript API. We download audio with yt-dlp
    then transcribe with Whisper to keep the pipeline deterministic.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        outtmpl = str(Path(tmpdir) / "audio.%(ext)s")
        cmd = [
            "yt-dlp",
            "--no-warnings",
            "--no-playlist",
            "-f",
            "bestaudio/best",
            "-x",
            "--audio-format",
            "mp3",
            "-o",
            outtmpl,
            url,
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        except Exception as e:
            raise RuntimeError(f"yt-dlp audio download failed to execute: {e}") from e

        if proc.returncode != 0:
            raise RuntimeError(
                f"yt-dlp audio download error ({proc.returncode}): {proc.stderr.strip()}"
            )

        audio_files = list(Path(tmpdir).glob("audio.*"))
        if not audio_files:
            raise RuntimeError("yt-dlp audio download produced no file")

        audio_path = str(audio_files[0])
        try:
            model = _ensure_whisper_model()
            result = model.transcribe(audio_path)
        except Exception as e:
            raise RuntimeError(f"Whisper transcription failed: {e}") from e

        transcript_text = safe_str(result.get("text"), default="").strip()
        if not transcript_text:
            raise RuntimeError("Whisper returned empty transcript")
        return transcript_text


def _chunk_text(text: str, chunk_tokens: int = 300, overlap_tokens: int = 50) -> List[str]:
    """
    Token-based chunking avoids hidden regressions when different scripts or
    emoji-heavy content shifts byte lengths significantly.
    """
    if chunk_tokens <= 0:
        raise ValueError("chunk_tokens must be positive")
    if overlap_tokens < 0 or overlap_tokens >= chunk_tokens:
        raise ValueError("overlap_tokens must be in [0, chunk_tokens)")

    tokens = _ENCODING.encode(text)
    if not tokens:
        return []

    chunks: List[str] = []
    step = chunk_tokens - overlap_tokens
    for start in range(0, len(tokens), step):
        window = tokens[start : start + chunk_tokens]
        if not window:
            break
        chunks.append(_ENCODING.decode(window).strip())
        if start + chunk_tokens >= len(tokens):
            break
    return [c for c in chunks if c]


def _openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)


@retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(initial=0.5, max=4))
def _embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Embeddings are a paid external dependency; retries help absorb short-lived
    networking blips without forcing creators to restart ingestion.
    """
    client = _openai_client()
    try:
        resp = client.embeddings.create(model="text-embedding-3-small", input=texts)
        return [d.embedding for d in resp.data]
    except Exception as e:
        raise RuntimeError(f"OpenAI embeddings request failed: {e}") from e


def _get_chroma_collection():
    """
    Supports both embedded (PersistentClient) and server (HttpClient) modes so
    local dev and docker-compose can share the same application code.
    """
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


def _ingest_single(video_id: str, url: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    if _is_youtube(url):
        transcript = _youtube_transcript_text(url)
        ytdlp = _run_yt_dlp_json(url)
    elif _is_instagram(url):
        transcript = _instagram_transcript_text(url)
        ytdlp = _run_yt_dlp_json(url)
    else:
        raise ValueError("Only YouTube and Instagram URLs are supported")

    normalized = normalize_yt_dlp_metadata(ytdlp)
    views = safe_int(normalized.get("views"), default=0)
    likes = safe_int(normalized.get("likes"), default=0)
    comments = safe_int(normalized.get("comments"), default=0)

    meta_out: Dict[str, Any] = {
        "video_id": video_id,
        "source_url": url,
        "title": safe_str(normalized.get("title"), default="Untitled"),
        "creator": safe_str(normalized.get("creator"), default="Unknown"),
        "views": views,
        "likes": likes,
        "comments": comments,
        "engagement_rate": engagement_rate(views, likes, comments),
        "upload_date": normalized.get("upload_date"),
        "duration": normalized.get("duration"),
        "thumbnail": normalized.get("thumbnail"),
        "follower_count": normalized.get("follower_count"),
        "hashtags": normalized.get("hashtags") or [],
    }

    chunks = _chunk_text(transcript, chunk_tokens=300, overlap_tokens=50)
    chunk_docs: List[Dict[str, Any]] = []
    for idx, content in enumerate(chunks):
        # Build metadata, only add hashtags if not empty
        metadata = {
            "video_id": video_id,
            "source_url": url,
            "chunk_index": idx,
            "title": meta_out["title"],
            "creator": meta_out["creator"],
            "views": meta_out["views"],
            "likes": meta_out["likes"],
            "comments": meta_out["comments"],
            "engagement_rate": meta_out["engagement_rate"],
            "upload_date": meta_out["upload_date"],
            "duration": meta_out["duration"],
            "follower_count": meta_out["follower_count"],
        }
        if meta_out["hashtags"]:
            metadata["hashtags"] = meta_out["hashtags"]
        chunk_docs.append(
            {
                "id": f"{video_id}_chunk_{idx}",
                "content": content,
                "metadata": metadata,
            }
        )
    return meta_out, chunk_docs


def ingest_videos(url_a: str, url_b: str) -> Dict[str, Any]:
    """
    Ingests exactly two videos (A and B), embeds transcript chunks, and stores them
    into a persistent ChromaDB collection.
    """
    video_a_meta, video_a_docs = _ingest_single("A", url_a)
    video_b_meta, video_b_docs = _ingest_single("B", url_b)

    all_docs = video_a_docs + video_b_docs
    if not all_docs:
        raise RuntimeError("No transcript chunks were produced; ingestion aborted")

    try:
        embeddings = _embed_texts([d["content"] for d in all_docs])
    except Exception:
        # Let the higher layer return 5xx with the real error message.
        raise

    collection = _get_chroma_collection()

    try:
        collection.upsert(
            ids=[d["id"] for d in all_docs],
            embeddings=embeddings,
            documents=[d["content"] for d in all_docs],
            metadatas=[d["metadata"] for d in all_docs],
        )
    except Exception as e:
        raise RuntimeError(f"ChromaDB upsert failed: {e}") from e

    return {"video_a": video_a_meta, "video_b": video_b_meta}


# Commit message suggestion:
#   "Implement video ingestion (YouTube transcript + Instagram whisper) and store embeddings in ChromaDB"
