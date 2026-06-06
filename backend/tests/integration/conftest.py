import os
from unittest.mock import patch

import pytest

# Add backend to path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import ingest


@pytest.fixture(scope="function")
def temp_chroma_collection(temp_chroma_dir, mock_openai_api_key):
    """Fixture providing a temporary, isolated ChromaDB collection."""
    # Override CHROMA_PERSIST_DIR for test
    with patch.dict(os.environ, {"CHROMA_PERSIST_DIR": temp_chroma_dir}):
        # Get or create test collection
        collection = ingest._get_chroma_collection()
        # Clear any existing data
        try:
            existing_ids = collection.get()["ids"]
            if existing_ids:
                collection.delete(ids=existing_ids)
        except Exception:
            pass
        yield collection


@pytest.fixture
def mock_youtube_transcript():
    """Fixture that mocks YouTube transcript retrieval."""
    with patch("ingest._youtube_transcript_text") as mock:
        mock.return_value = "Hey everyone! Welcome back! Let's talk about how to make great videos. First, you need a great hook in the first 5 seconds. Then, keep your content engaging. Finally, end with a strong call to action!"
        yield mock


@pytest.fixture
def mock_yt_dlp_json():
    """Fixture that mocks yt-dlp metadata retrieval."""
    with patch("ingest._run_yt_dlp_json") as mock:
        mock.return_value = {
            "title": "Test Video Title",
            "uploader": "Test Creator Name",
            "view_count": 10000,
            "like_count": 800,
            "comment_count": 200,
            "upload_date": "20240101",
            "duration": 120,
            "thumbnail": "https://example.com/thumb.jpg",
            "channel_follower_count": 50000,
            "tags": ["test", "video"],
        }
        yield mock


@pytest.fixture
def mock_whisper_transcript():
    """Fixture that mocks Whisper transcription for Instagram."""
    with patch("ingest._instagram_transcript_text") as mock:
        mock.return_value = "Hey guys! Welcome to my channel! Today we're trying something new. Let's get started!"
        yield mock


@pytest.fixture
def mock_openai_embeddings():
    """Fixture that mocks OpenAI embeddings API calls."""
    with patch("ingest._embed_texts") as mock:
        def mock_embed(texts):
            # Return dummy 1536-dimensional embeddings
            return [[0.1] * 1536 for _ in texts]
        mock.side_effect = mock_embed
        yield mock


@pytest.fixture
def mock_retriever_embeddings():
    """Fixture that mocks retriever embeddings."""
    with patch("retriever._embed_query") as mock:
        mock.return_value = [0.1] * 1536
        yield mock


@pytest.fixture
def sample_ingested_videos(temp_chroma_collection, mock_youtube_transcript, mock_yt_dlp_json, mock_openai_embeddings):
    """Fixture that ingests two mock videos for testing."""
    # Ingest videos using mock functions
    metadata = ingest.ingest_videos(
        "https://www.youtube.com/watch?v=test1",
        "https://www.youtube.com/watch?v=test2"
    )
    yield metadata
