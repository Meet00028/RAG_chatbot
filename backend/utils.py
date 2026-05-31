from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


def safe_int(value: Any, default: int = 0) -> int:
    """
    External scrapers frequently return null/strings; we normalize aggressively so
    downstream math/storage never fails at runtime.
    """
    try:
        if value is None:
            return default
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            return int(value)
        value_str = str(value).strip()
        if value_str == "":
            return default
        return int(float(value_str))
    except Exception:
        return default


def safe_str(value: Any, default: str = "") -> str:
    try:
        if value is None:
            return default
        v = str(value).strip()
        return v if v else default
    except Exception:
        return default


def safe_list_str(value: Any) -> List[str]:
    """
    Normalizes tags/hashtags from different platforms into a list[str].
    """
    if value is None:
        return []
    if isinstance(value, list):
        out: List[str] = []
        for item in value:
            s = safe_str(item, default="").strip()
            if s:
                out.append(s)
        return out
    if isinstance(value, str):
        return [t for t in re.split(r"[\s,]+", value) if t]
    return []


def engagement_rate(views: int, likes: int, comments: int) -> float:
    """
    Engagement rate is a product-facing metric; clamping views==0 to 0 prevents
    noisy crashes and avoids misleading 'inf%' outputs.
    """
    if views <= 0:
        return 0.0
    return round(((likes + comments) / views) * 100.0, 4)


def normalize_yt_dlp_metadata(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    yt-dlp is the one tool we rely on across platforms; we normalize field names
    here so ingest.py stays focused on orchestration and error boundaries.
    """
    title = safe_str(raw.get("title"), default="Untitled")
    uploader = safe_str(raw.get("uploader") or raw.get("channel"), default="Unknown")

    views = safe_int(raw.get("view_count"), default=0)
    likes = safe_int(raw.get("like_count"), default=0)
    comments = safe_int(raw.get("comment_count"), default=0)

    upload_date = raw.get("upload_date")
    if upload_date is not None:
        upload_date = safe_str(upload_date, default=None)  # type: ignore[assignment]

    duration = raw.get("duration")
    duration_int: Optional[int] = None
    try:
        duration_int = None if duration is None else int(duration)
    except Exception:
        duration_int = None

    thumbnail = raw.get("thumbnail")
    thumbnail = safe_str(thumbnail, default=None) if thumbnail is not None else None

    follower_count = raw.get("channel_follower_count")
    follower_count_int: Optional[int] = None
    try:
        follower_count_int = None if follower_count is None else int(follower_count)
    except Exception:
        follower_count_int = None

    hashtags = safe_list_str(raw.get("tags") or raw.get("hashtags"))

    return {
        "title": title,
        "creator": uploader,
        "views": views,
        "likes": likes,
        "comments": comments,
        "upload_date": upload_date,
        "duration": duration_int,
        "thumbnail": thumbnail,
        "follower_count": follower_count_int,
        "hashtags": hashtags,
    }


# Commit message suggestion:
#   "Add ingestion helpers (metadata normalization + engagement rate)"
