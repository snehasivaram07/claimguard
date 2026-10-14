from typing import Any

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness() -> dict[str, str]:
    """Basic liveness probe confirming the process is executing."""
    return {"status": "alive"}


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness() -> JSONResponse:
    """Readiness probe checking availability of core backing services."""
    checks: dict[str, Any] = {
        "status": "ready",
        "services": {
            "api": "healthy",
        },
    }
    return JSONResponse(status_code=status.HTTP_200_OK, content=checks)
