import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from pydantic import ValidationError
from models import IngestRequest, VideoMetadata, HealthResponse, RetrievalChunk


class TestIngestRequest:
    """Tests for the IngestRequest Pydantic model."""

    def test_valid_ingest_request(self):
        """Test valid input with two URLs passes validation."""
        req = IngestRequest(
            url_a="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            url_b="https://www.youtube.com/watch?v=9bZkp7q19f0",
        )
        assert req is not None
        assert str(req.url_a) == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert str(req.url_b) == "https://www.youtube.com/watch?v=9bZkp7q19f0"

    def test_missing_url_a(self):
        """Test missing url_a raises ValidationError."""
        with pytest.raises(ValidationError):
            IngestRequest(url_b="https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_missing_url_b(self):
        """Test missing url_b raises ValidationError."""
        with pytest.raises(ValidationError):
            IngestRequest(url_a="https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_non_string_url_fails(self):
        """Test non-HTTP URL fails validation."""
        with pytest.raises(ValidationError):
            IngestRequest(url_a=123, url_b=456)


class TestVideoMetadata:
    """Tests for the VideoMetadata Pydantic model."""

    def test_complete_video_metadata(self):
        """Test all fields present passes validation."""
        meta = VideoMetadata(
            video_id="A",
            source_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            title="Never Gonna Give You Up",
            creator="Rick Astley",
            views=1500000000,
            likes=15000000,
            comments=500000,
            engagement_rate=1.0333,
        )
        assert meta is not None

    def test_follower_count_none_allowed(self):
        """Test follower_count=None is allowed."""
        meta = VideoMetadata(
            video_id="B",
            source_url="https://www.youtube.com/watch?v=9bZkp7q19f0",
            title="GANGNAM STYLE",
            creator="PSY",
            views=5000000000,
            likes=25000000,
            comments=1000000,
            engagement_rate=0.52,
            follower_count=None,
        )
        assert meta.follower_count is None

    def test_engagement_rate_float(self):
        """Test engagement_rate must be a float."""
        with pytest.raises(ValidationError):
            VideoMetadata(
                video_id="A",
                source_url="https://example.com",
                title="Test",
                creator="Test",
                views=1000,
                likes=100,
                comments=50,
                engagement_rate="not-a-float",
            )


class TestHealthResponse:
    """Tests for HealthResponse model."""

    def test_health_response_ok(self):
        res = HealthResponse(status="ok")
        assert res.status == "ok"

    def test_health_response_default_ok(self):
        res = HealthResponse()
        assert res.status == "ok"


class TestRetrievalChunk:
    """Tests for RetrievalChunk model."""

    def test_retrieval_chunk_valid(self):
        chunk = RetrievalChunk(
            content="Test content",
            metadata={"video_id": "A", "chunk_index": 0},
            distance=0.5,
        )
        assert chunk is not None
