import sys
import os
from unittest.mock import patch
import pytest
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class TestApiIngest:
    """Tests for the /ingest endpoint."""

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_ingest_valid_urls(self, async_client, mock_youtube_transcript, mock_yt_dlp_json, mock_openai_embeddings):
        """Test POST /ingest with valid URLs returns 200 and valid session_id."""
        with patch("main.ingest") as mock_ingest:
            mock_meta = {
                "video_a": {
                    "video_id": "A",
                    "source_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                    "title": "Test A",
                    "creator": "Creator A",
                    "views": 1000,
                    "likes": 100,
                    "comments": 50,
                    "engagement_rate": 15.0,
                    "hashtags": []
                },
                "video_b": {
                    "video_id": "B",
                    "source_url": "https://www.youtube.com/watch?v=9bZkp7q19f0",
                    "title": "Test B",
                    "creator": "Creator B",
                    "views": 2000,
                    "likes": 200,
                    "comments": 100,
                    "engagement_rate": 15.0,
                    "hashtags": []
                }
            }
            mock_ingest.ingest_videos.return_value = mock_meta

            response = await async_client.post(
                "/ingest",
                json={
                    "url_a": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                    "url_b": "https://www.youtube.com/watch?v=9bZkp7q19f0"
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert "session_id" in data
            # Check session_id is UUID format
            try:
                uuid.UUID(data["session_id"])
                valid_uuid = True
            except ValueError:
                valid_uuid = False
            assert valid_uuid is True
            assert "video_a" in data
            assert "video_b" in data

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_ingest_missing_url_a(self, async_client):
        """Test POST /ingest missing url_a returns 422."""
        response = await async_client.post(
            "/ingest",
            json={"url_b": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        )
        assert response.status_code == 422

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_ingest_missing_url_b(self, async_client):
        """Test POST /ingest missing url_b returns 422."""
        response = await async_client.post(
            "/ingest",
            json={"url_a": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        )
        assert response.status_code == 422

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_ingest_invalid_url(self, async_client):
        """Test POST /ingest with invalid URL returns 422, not 500."""
        response = await async_client.post(
            "/ingest",
            json={"url_a": "not-a-url", "url_b": "not-a-url"}
        )
        assert response.status_code == 422
