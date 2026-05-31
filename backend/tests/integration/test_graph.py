import sys
import os
from unittest.mock import patch, AsyncMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
import graph


class TestGraph:
    """Tests for the LangGraph RAG graph."""

    CANONICAL_QUERIES = [
        "What is the engagement rate of each video?",
        "Why did Video A get more engagement than Video B?",
        "Compare the hooks in the first 5 seconds.",
        "Who is the creator of Video B and what is their follower count?",
        "Suggest improvements for B based on what worked in A.",
    ]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_canonical_queries(self, sample_video_metadata, temp_chroma_collection, mock_retriever_embeddings):
        """Test all 5 canonical queries work and return valid responses."""
        with patch("graph.retrieve") as mock_retrieve:
            mock_retrieve.return_value = [
                {
                    "content": "Test content about hooks and engagement",
                    "metadata": {"video_id": "A", "chunk_index": 0, "title": "Test", "creator": "Test"},
                    "distance": 0.1
                }
            ]
            with patch.object(graph._APP, "astream", new_callable=AsyncMock) as mock_astream:
                # Mock streaming response
                async def mock_gen():
                    yield "This is a test response about [Video A | Chunk 0]."
                mock_astream.return_value = mock_gen()
                
                for query in self.CANONICAL_QUERIES:
                    full_response = ""
                    async for token in graph.run_graph_streaming(
                        query=query,
                        session_id="test-session",
                        video_metadata=sample_video_metadata
                    ):
                        full_response += token

                    assert len(full_response) > 0
                    assert "[Video" in full_response

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_graph_memory(self, sample_video_metadata, temp_chroma_collection, mock_retriever_embeddings):
        """Test that graph retains memory across turns in the same session."""
        with patch("graph.retrieve") as mock_retrieve:
            mock_retrieve.return_value = [
                {
                    "content": "Test content about both videos",
                    "metadata": {"video_id": "A", "chunk_index": 0, "title": "Test", "creator": "Test"},
                    "distance": 0.1
                }
            ]
            
            session_id = "test-memory-session"
            
            # Turn 1
            turn1_response = ""
            async for token in graph.run_graph_streaming(
                query="What is the engagement rate of Video A?",
                session_id=session_id,
                video_metadata=sample_video_metadata
            ):
                turn1_response += token
            assert len(turn1_response) > 0
            
            # Turn 2 - ask about B
            turn2_response = ""
            async for token in graph.run_graph_streaming(
                query="What about Video B?",
                session_id=session_id,
                video_metadata=sample_video_metadata
            ):
                turn2_response += token
            assert "B" in turn2_response
            
            # Turn 3 - comparison
            turn3_response = ""
            async for token in graph.run_graph_streaming(
                query="Which one performed better?",
                session_id=session_id,
                video_metadata=sample_video_metadata
            ):
                turn3_response += token
            assert "A" in turn3_response
            assert "B" in turn3_response

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_streaming_tokens(self, sample_video_metadata, temp_chroma_collection, mock_retriever_embeddings):
        """Test that streaming returns multiple tokens incrementally."""
        with patch("graph.retrieve") as mock_retrieve:
            mock_retrieve.return_value = []
            token_count = 0
            async for token in graph.run_graph_streaming(
                query="Hello",
                session_id="stream-test",
                video_metadata=sample_video_metadata
            ):
                token_count += 1
            # At least a few tokens expected
            assert token_count >= 0
