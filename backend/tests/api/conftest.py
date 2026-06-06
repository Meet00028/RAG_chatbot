import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.fixture
async def async_client(temp_chroma_dir, mock_openai_api_key):
    """Fixture providing an httpx AsyncClient for testing the FastAPI app."""
    with patch.dict(os.environ, {"CHROMA_PERSIST_DIR": temp_chroma_dir}):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            yield client


