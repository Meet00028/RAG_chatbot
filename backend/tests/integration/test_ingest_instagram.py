import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
import ingest


class TestIngestInstagram:
    """Tests for Instagram video ingestion."""

    @pytest.mark.integration
    def test_ingest_instagram_metadata(self, temp_chroma_collection, mock_whisper_transcript, mock_yt_dlp_json, mock_openai_embeddings):
        """Test ingest works with Instagram mock data."""
        metadata = ingest.ingest_videos(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.instagram.com/reel/test/"
        )

        video_b = metadata["video_b"]
        assert isinstance(video_b["title"], str)
        # Follower count can be None
        assert "follower_count" in video_b

    @pytest.mark.integration
    def test_ingest_instagram_chunks(self, temp_chroma_collection, mock_whisper_transcript, mock_yt_dlp_json, mock_openai_embeddings):
        """Test Instagram chunks stored in ChromaDB."""
        ingest.ingest_videos(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.instagram.com/reel/test/"
        )

        collection = ingest._get_chroma_collection()
        video_b_chunks = collection.get(where={"video_id": "B"})
        assert len(video_b_chunks["ids"]) > 0
