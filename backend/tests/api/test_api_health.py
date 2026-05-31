import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class TestApiHealth:
    """Tests for the /health endpoint."""

    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_health_endpoint_ok(self, async_client):
        """Test GET /health returns 200 and correct JSON body."""
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
