import os
import tempfile
from typing import Any, Dict

import pytest
from dotenv import load_dotenv

# Load environment variables for tests
load_dotenv()


@pytest.fixture(scope="session")
def temp_chroma_dir():
    """Fixture providing a temporary directory for ChromaDB persistence."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture(scope="session")
def mock_openai_api_key():
    """Fixture that sets a mock OPENAI_API_KEY if none is present."""
    original_key = os.getenv("OPENAI_API_KEY")
    if not original_key:
        os.environ["OPENAI_API_KEY"] = "mock-key-for-testing"
    yield
    if original_key is None:
        del os.environ["OPENAI_API_KEY"]


@pytest.fixture
def sample_video_metadata() -> Dict[str, Any]:
    """Fixture providing sample video metadata for testing."""
    return {
        "video_a": {
            "video_id": "A",
            "source_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "title": "Never Gonna Give You Up",
            "creator": "Rick Astley",
            "views": 1500000000,
            "likes": 15000000,
            "comments": 500000,
            "engagement_rate": 1.0333,
            "upload_date": "20091025",
            "duration": 213,
            "thumbnail": "https://example.com/thumb.jpg",
            "follower_count": 10000000,
            "hashtags": ["music", "80s", "pop"],
        },
        "video_b": {
            "video_id": "B",
            "source_url": "https://www.youtube.com/watch?v=9bZkp7q19f0",
            "title": "GANGNAM STYLE",
            "creator": "PSY",
            "views": 5000000000,
            "likes": 25000000,
            "comments": 1000000,
            "engagement_rate": 0.52,
            "upload_date": "20120715",
            "duration": 253,
            "thumbnail": "https://example.com/thumb2.jpg",
            "follower_count": 20000000,
            "hashtags": ["kpop", "psy", "gangnam"],
        },
    }
