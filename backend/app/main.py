from contextlib import asynccontextmanager

# pyrefly: ignore [missing-import]
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.core.config import settings
from app.core.errors import (
    AppException,
    app_exception_handler,
    generic_exception_handler,
    validation_exception_handler,
)
from app.core.logging import logger
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup
    logger.info(
        "Starting ClaimGuard Backend Foundation",
        extra={"environment": settings.ENVIRONMENT, "debug": settings.DEBUG},
    )
    yield
    # Shutdown
    logger.info("Shutting down ClaimGuard Backend")


def create_app() -> FastAPI:
    # Only expose OpenAPI documentation in development environment
    docs_url = "/docs" if settings.ENVIRONMENT == "development" else None
    redoc_url = "/redoc" if settings.ENVIRONMENT == "development" else None
    openapi_url = "/openapi.json" if settings.ENVIRONMENT == "development" else None

    application = FastAPI(
        title="ClaimGuard API",
        description="Multi-Tenant Claim Intelligence Graph Platform - Backend Foundation",
        version="0.1.0",
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
        lifespan=lifespan,
    )

    # 1. Security Headers Middleware
    application.add_middleware(SecurityHeadersMiddleware)

    # 2. CORS Middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # 3. Request-ID Middleware
    application.add_middleware(RequestIDMiddleware)

    # Register Global Exception Handlers
    application.add_exception_handler(AppException, app_exception_handler)
    application.add_exception_handler(RequestValidationError, validation_exception_handler)
    application.add_exception_handler(Exception, generic_exception_handler)

    # Register Routers
    application.include_router(health_router)

    return application


app = create_app()
