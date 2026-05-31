from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


class IngestRequest(BaseModel):
    url_a: HttpUrl = Field(..., description="Video A URL (YouTube or Instagram)")
    url_b: HttpUrl = Field(..., description="Video B URL (YouTube or Instagram)")


class VideoMetadata(BaseModel):
    video_id: str = Field(..., description='"A" or "B"')
    source_url: HttpUrl

    title: str
    creator: str
    views: int
    likes: int
    comments: int
    engagement_rate: float

    upload_date: Optional[str] = Field(
        default=None,
        description="Original platform upload date (often YYYYMMDD). Null when unavailable.",
    )
    duration: Optional[int] = Field(
        default=None,
        description="Video duration in seconds. Null when unavailable.",
    )
    thumbnail: Optional[str] = Field(
        default=None,
        description="Thumbnail URL when available.",
    )
    follower_count: Optional[int] = Field(
        default=None,
        description="Channel/page follower count when available; else null.",
    )
    hashtags: List[str] = Field(default_factory=list)


class IngestResponse(BaseModel):
    session_id: str
    video_a: VideoMetadata
    video_b: VideoMetadata


class HealthResponse(BaseModel):
    status: str = "ok"


class RetrievalChunk(BaseModel):
    content: str
    metadata: Dict[str, Any]
    distance: float


# Commit message suggestion:
#   "Add backend request/response Pydantic models"
