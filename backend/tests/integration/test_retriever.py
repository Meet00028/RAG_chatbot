import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
import retriever


class TestRetriever:
    """Tests for the retriever module."""

    @pytest.mark.integration
    def test_retrieve_results(self, sample_ingested_videos, temp_chroma_collection, mock_retriever_embeddings):
        """Test retrieve returns non-empty results for a valid query."""
        results = retriever.retrieve("test query about video content", video_ids=["A", "B"], n_results=4)
        assert len(results) > 0

    @pytest.mark.integration
    def test_retrieve_filter_a_only(self, sample_ingested_videos, temp_chroma_collection, mock_retriever_embeddings):
        """Test retrieve with filter ['A'] returns only A chunks."""
        results = retriever.retrieve("test", video_ids=["A"], n_results=4)
        for result in results:
            assert result["metadata"]["video_id"] == "A"

    @pytest.mark.integration
    def test_retrieve_filter_b_only(self, sample_ingested_videos, temp_chroma_collection, mock_retriever_embeddings):
        """Test retrieve with filter ['B'] returns only B chunks."""
        results = retriever.retrieve("test", video_ids=["B"], n_results=4)
        for result in results:
            assert result["metadata"]["video_id"] == "B"

    @pytest.mark.integration
    def test_retrieve_n_results(self, sample_ingested_videos, temp_chroma_collection, mock_retriever_embeddings):
        """Test n_results=4 returns at most 4 chunks."""
        results = retriever.retrieve("test", video_ids=["A", "B"], n_results=4)
        assert len(results) <= 4

    @pytest.mark.integration
    def test_retrieve_empty_query(self, sample_ingested_videos, temp_chroma_collection):
        """Test retrieve with empty query returns nothing and doesn't crash."""
        results = retriever.retrieve("", video_ids=["A", "B"])
        assert len(results) == 0

    @pytest.mark.integration
    def test_retrieve_special_chars(self, sample_ingested_videos, temp_chroma_collection, mock_retriever_embeddings):
        """Test retrieve with special characters in query doesn't crash."""
        retriever.retrieve("test! @#$%^&*()", video_ids=["A", "B"])
        # Just verify no crash
        assert True

    @pytest.mark.integration
    def test_retrieve_result_keys(self, sample_ingested_videos, temp_chroma_collection, mock_retriever_embeddings):
        """Test each result has content, metadata, and distance keys."""
        results = retriever.retrieve("test query", video_ids=["A", "B"], n_results=2)
        for result in results:
            assert "content" in result
            assert "metadata" in result
            assert "distance" in result

    @pytest.mark.integration
    def test_retrieve_metadata_keys(self, sample_ingested_videos, temp_chroma_collection, mock_retriever_embeddings):
        """Test metadata includes required keys."""
        results = retriever.retrieve("test query", video_ids=["A", "B"], n_results=2)
        for result in results:
            meta = result["metadata"]
            assert "video_id" in meta
            assert "chunk_index" in meta
            assert "title" in meta
            assert "creator" in meta
            assert "engagement_rate" in meta
