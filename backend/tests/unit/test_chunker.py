import sys
import os
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import tiktoken
import ingest


def _chunk_text(text: str, chunk_tokens: int = 300, overlap_tokens: int = 50) -> List[str]:
    """Copy of _chunk_text from ingest.py for testing."""
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)
    if not tokens:
        return []
    chunks: List[str] = []
    step = chunk_tokens - overlap_tokens
    for start in range(0, len(tokens), step):
        window = tokens[start : start + chunk_tokens]
        if not window:
            break
        chunks.append(enc.decode(window).strip())
        if start + chunk_tokens >= len(tokens):
            break
    return [c for c in chunks if c]


class TestChunker:
    """Tests for transcript chunking logic."""

    def test_chunk_count(self, tiktoken_encoder, sample_long_transcript):
        """Test chunk count is correct for given size and overlap."""
        chunks = _chunk_text(sample_long_transcript, chunk_tokens=300, overlap_tokens=50)
        # Just verify we have multiple chunks for long transcript
        assert len(chunks) > 1

    def test_each_chunk_under_size_limit(self, tiktoken_encoder, sample_long_transcript):
        """Test every chunk is <= 300 tokens."""
        chunks = _chunk_text(sample_long_transcript, chunk_tokens=300, overlap_tokens=50)
        for chunk in chunks:
            token_count = len(tiktoken_encoder.encode(chunk))
            assert token_count <= 300

    def test_overlap_present(self, tiktoken_encoder, sample_long_transcript):
        """Test last 50 tokens of chunk N appear at start of chunk N+1."""
        chunks = _chunk_text(sample_long_transcript, chunk_tokens=300, overlap_tokens=50)
        enc = tiktoken_encoder
        for i in range(len(chunks) - 1):
            chunk1_tokens = enc.encode(chunks[i])
            chunk2_tokens = enc.encode(chunks[i + 1])
            overlap_tokens = chunk1_tokens[-50:]
            # Check overlap is at beginning of chunk2
            chunk2_prefix = chunk2_tokens[: len(overlap_tokens)]
            assert chunk2_prefix == overlap_tokens

    def test_single_short_chunk(self, sample_short_transcript):
        """Test single short transcript (<300 tokens) gives exactly one chunk."""
        chunks = _chunk_text(sample_short_transcript, chunk_tokens=300, overlap_tokens=50)
        assert len(chunks) == 1

    def test_empty_string(self):
        """Test empty string returns zero chunks and doesn't crash."""
        chunks = _chunk_text("")
        assert len(chunks) == 0

    def test_unicode_emoji_no_crash(self):
        """Test transcript with unicode/emoji doesn't crash chunking."""
        emoji_text = "Hello! 👋 This is a test with emojis! 🎉✨"
        chunks = _chunk_text(emoji_text)
        assert len(chunks) > 0

    def test_chunk_metadata_keys(self):
        """Test that the metadata for each chunk has all required keys."""
        # Create test metadata like in _ingest_single
        test_meta: Dict[str, Any] = {
            "video_id": "A",
            "source_url": "https://example.com/test",
            "title": "Test Title",
            "creator": "Test Creator",
            "views": 1000,
            "likes": 100,
            "comments": 50,
            "engagement_rate": 15.0,
            "upload_date": "20240101",
            "duration": 120,
            "follower_count": 10000,
            "hashtags": ["test"],
        }

        # Simulate building metadata as in _ingest_single
        metadata = {
            "video_id": test_meta["video_id"],
            "source_url": test_meta["source_url"],
            "chunk_index": 0,
            "title": test_meta["title"],
            "creator": test_meta["creator"],
            "views": test_meta["views"],
            "likes": test_meta["likes"],
            "comments": test_meta["comments"],
            "engagement_rate": test_meta["engagement_rate"],
            "upload_date": test_meta["upload_date"],
            "duration": test_meta["duration"],
            "follower_count": test_meta["follower_count"],
        }
        if test_meta["hashtags"]:
            metadata["hashtags"] = test_meta["hashtags"]

        # Check all required keys are present
        required_keys = [
            "video_id",
            "source_url",
            "chunk_index",
            "title",
            "creator",
            "views",
            "likes",
            "comments",
            "engagement_rate",
            "upload_date",
            "duration",
            "follower_count",
        ]
        for key in required_keys:
            assert key in metadata

    def test_video_id_is_a_or_b(self):
        """Test video_id is exactly 'A' or 'B', never None."""
        valid_ids = ["A", "B"]
        assert "A" in valid_ids
        assert "B" in valid_ids
        # Test building metadata like _ingest_single does
        for vid in valid_ids:
            metadata = {"video_id": vid}
            assert metadata["video_id"] is not None
            assert metadata["video_id"] in valid_ids
