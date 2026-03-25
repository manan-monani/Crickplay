"""
Pytest Configuration for Crickplay Backend Tests
"""

import pytest
from httpx import AsyncClient

from app.main import app


@pytest.fixture
async def client():
    """Async test client fixture."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
