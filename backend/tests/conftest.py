import os

import pytest
from httpx import ASGITransport, AsyncClient

# Enforce test environment settings before importing app
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "true"

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
