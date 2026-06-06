import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class TestApiCors:
    """Tests for CORS headers."""

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_cors_headers(self, async_client):
        """Test OPTIONS /ingest returns CORS headers."""
        response = await async_client.options(
            "/ingest",
            headers={"Origin": "http://localhost:5173"}
        )
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
