import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
import ingest


class TestIngestYouTube:
    """Tests for YouTube video ingestion."""

    @pytest.mark.integration
    def test_ingest_metadata(self, temp_chroma_collection, mock_youtube_transcript, mock_yt_dlp_json, mock_openai_embeddings):
        """Test ingest returns valid metadata for YouTube videos."""
        metadata = ingest.ingest_videos(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=9bZkp7q19f0"
        )

        assert "video_a" in metadata
        assert "video_b" in metadata
        video_a = metadata["video_a"]
        assert isinstance(video_a["title"], str)
        assert len(video_a["title"]) > 0
        assert isinstance(video_a["creator"], str)
        assert len(video_a["creator"]) > 0
        assert isinstance(video_a["views"], int)
        assert video_a["views"] >= 0
        assert isinstance(video_a["likes"], int)
        assert video_a["likes"] >= 0
        assert isinstance(video_a["comments"], int)
        assert video_a["comments"] >= 0
        assert isinstance(video_a["engagement_rate"], float)

    @pytest.mark.integration
    def test_ingest_chunks_in_chroma(self, temp_chroma_collection, mock_youtube_transcript, mock_yt_dlp_json, mock_openai_embeddings):
        """Test chunks are stored in ChromaDB after ingestion."""
        ingest.ingest_videos(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=9bZkp7q19f0"
        )

        # Check collection has chunks
        collection = ingest._get_chroma_collection()
        all_ids = collection.get()["ids"]
        assert len(all_ids) > 0

        # Check video A chunks exist
        video_a_chunks = collection.get(where={"video_id": "A"})
        assert len(video_a_chunks["ids"]) > 0
