from typing import Any

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.logging import logger
from app.db.session import AsyncSessionLocal
from app.graph.client import graph_manager
from app.storage.s3_client import s3_manager

router = APIRouter(prefix="/health", tags=["Health"])


async def check_postgres() -> bool:
    """Probes PostgreSQL database connectivity via raw SQL SELECT 1."""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.warning("Postgres readiness check failed: %s", e)
        return False


def check_falkordb() -> bool:
    """Probes FalkorDB graph connectivity via ping Cypher query."""
    try:
        return graph_manager.check_health(max_retries=1, retry_delay=0.1)
    except Exception as e:
        logger.warning("FalkorDB readiness check failed: %s", e)
        return False


def check_storage() -> bool:
    """Probes S3 / MinIO object storage connectivity via bucket verification."""
    try:
        return s3_manager.check_health()
    except Exception as e:
        logger.warning("S3 readiness check failed: %s", e)
        return False


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness() -> dict[str, str]:
    """Basic liveness probe confirming the process is executing."""
    return {"status": "alive"}


@router.get("/ready")
async def readiness() -> JSONResponse:
    """Readiness probe checking availability of core backing services (PostgreSQL, FalkorDB, S3)."""
    pg_ok = await check_postgres()
    graph_ok = check_falkordb()
    storage_ok = check_storage()

    all_healthy = pg_ok and graph_ok and storage_ok

    content: dict[str, Any] = {
        "status": "ready" if all_healthy else "unhealthy",
        "services": {
            "postgres": "healthy" if pg_ok else "unhealthy",
            "falkordb": "healthy" if graph_ok else "unhealthy",
            "s3": "healthy" if storage_ok else "unhealthy",
        },
    }

    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=status_code, content=content)
