import os
import tempfile
from unittest.mock import patch, AsyncMock

import pytest
from httpx import AsyncClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from main import app


@pytest.fixture
async def async_client(temp_chroma_dir, mock_openai_api_key):
    """Fixture providing an httpx AsyncClient for testing the FastAPI app."""
    with patch.dict(os.environ, {"CHROMA_PERSIST_DIR": temp_chroma_dir}):
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client


import sys
