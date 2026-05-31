import sys
import os
from unittest.mock import patch, AsyncMock
import pytest
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class TestApiStream:
    """Tests for the /stream endpoint."""

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_stream_valid_session(self, async_client, sample_video_metadata):
        """Test GET /stream with valid session_id and query returns 200 and text/event-stream."""
        # First, set up session metadata in main's SESSION_METADATA
        session_id = str(uuid.uuid4())
        import main
        main.SESSION_METADATA[session_id] = sample_video_metadata

        with patch("main.graph.run_graph_streaming") as mock_stream:
            async def mock_gen():
                yield "This is a test "
                yield "response "
                yield "with [Video A | Chunk 0]."
                yield "[DONE]"
            mock_stream.return_value = mock_gen()

            response = await async_client.get(
                "/stream",
                params={"session_id": session_id, "query": "test query"}
            )
            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]
            assert "This is a test" in response.text

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_stream_missing_session_id(self, async_client):
        """Test GET /stream with missing session_id returns 422."""
        response = await async_client.get(
            "/stream",
            params={"query": "test"}
        )
        assert response.status_code == 422

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_stream_missing_query(self, async_client):
        """Test GET /stream with missing query returns 422."""
        session_id = str(uuid.uuid4())
        response = await async_client.get(
            "/stream",
            params={"session_id": session_id}
        )
        assert response.status_code == 422

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_stream_unknown_session_id(self, async_client):
        """Test GET /stream with unknown session_id returns 404."""
        unknown_session = str(uuid.uuid4())
        response = await async_client.get(
            "/stream",
            params={"session_id": unknown_session, "query": "test"}
        )
        assert response.status_code == 404
