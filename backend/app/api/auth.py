from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.limiter import limiter
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.audit import AuditTrailResponse
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.audit_service import audit_service
from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
@limiter.limit(f"{settings.RATE_LIMIT_REGISTER_PER_MINUTE}/minute")
async def register(
    request: Request,
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    client_ip = request.client.host if request.client else None
    request_id = getattr(request.state, "request_id", None)
    return await auth_service.register_user(
        db=db,
        request=payload,
        ip=client_ip,
        request_id=request_id,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate and receive access and rotating refresh tokens",
)
@limiter.limit(f"{settings.RATE_LIMIT_LOGIN_PER_MINUTE}/minute")
async def login(
    request: Request,
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    client_ip = request.client.host if request.client else None
    request_id = getattr(request.state, "request_id", None)
    return await auth_service.login_user(
        db=db,
        request=payload,
        ip=client_ip,
        request_id=request_id,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Rotate refresh token and issue new access token",
)
async def refresh(
    request: Request,
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    client_ip = request.client.host if request.client else None
    request_id = getattr(request.state, "request_id", None)
    return await auth_service.refresh_access_token(
        db=db,
        raw_refresh_token=payload.refresh_token,
        ip=client_ip,
        request_id=request_id,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Revoke refresh token and log out",
)
async def logout(
    request: Request,
    payload: LogoutRequest,
    db: AsyncSession = Depends(get_db),
):
    client_ip = request.client.host if request.client else None
    request_id = getattr(request.state, "request_id", None)
    await auth_service.logout_user(
        db=db,
        raw_refresh_token=payload.refresh_token,
        ip=client_ip,
        request_id=request_id,
    )
    return {"message": "Logged out successfully"}


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve current user profile",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.get(
    "/me/audit",
    response_model=AuditTrailResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve personal security audit events",
)
async def get_my_audit(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AuditTrailResponse:
    items, total = await audit_service.get_user_audit_events(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )
    return AuditTrailResponse(total=total, items=items)
