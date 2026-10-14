import pytest
from httpx import ASGITransport, AsyncClient

from app.api import health
from app.main import app


@pytest.mark.asyncio
async def test_health_live():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health/live")
        assert response.status_code == 200
        assert response.json() == {"status": "alive"}
        assert "x-request-id" in response.headers
        assert response.headers["x-content-type-options"] == "nosniff"


@pytest.mark.asyncio
async def test_health_ready_all_healthy(monkeypatch):
    async def mock_pg():
        return True

    monkeypatch.setattr(health, "check_postgres", mock_pg)
    monkeypatch.setattr(health, "check_falkordb", lambda: True)
    monkeypatch.setattr(health, "check_storage", lambda: True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["services"] == {
            "postgres": "healthy",
            "falkordb": "healthy",
            "s3": "healthy",
        }


@pytest.mark.asyncio
async def test_health_ready_postgres_down(monkeypatch):
    async def mock_pg_fail():
        return False

    monkeypatch.setattr(health, "check_postgres", mock_pg_fail)
    monkeypatch.setattr(health, "check_falkordb", lambda: True)
    monkeypatch.setattr(health, "check_storage", lambda: True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["services"]["postgres"] == "unhealthy"
        assert data["services"]["falkordb"] == "healthy"
        assert data["services"]["s3"] == "healthy"


@pytest.mark.asyncio
async def test_health_ready_falkordb_down(monkeypatch):
    async def mock_pg():
        return True

    monkeypatch.setattr(health, "check_postgres", mock_pg)
    monkeypatch.setattr(health, "check_falkordb", lambda: False)
    monkeypatch.setattr(health, "check_storage", lambda: True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["services"]["falkordb"] == "unhealthy"


@pytest.mark.asyncio
async def test_health_ready_storage_down(monkeypatch):
    async def mock_pg():
        return True

    monkeypatch.setattr(health, "check_postgres", mock_pg)
    monkeypatch.setattr(health, "check_falkordb", lambda: True)
    monkeypatch.setattr(health, "check_storage", lambda: False)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["services"]["s3"] == "unhealthy"
