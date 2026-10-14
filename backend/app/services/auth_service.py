from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.db.models.audit import AuditEvent
from app.db.models.token import RefreshToken
from app.db.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse


class AuthService:
    """Handles user identity, credential verification, and token rotation."""

    async def register_user(
        self,
        db: AsyncSession,
        request: RegisterRequest,
        ip: str | None = None,
        request_id: str | None = None,
    ) -> UserResponse:
        # Check if email is already registered
        query = select(User).where(User.email == request.email.lower().strip())
        result = await db.execute(query)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            # Audit registration failure
            audit = AuditEvent(
                user_id=None,
                action="REGISTER",
                resource_type="user",
                resource_id=None,
                ip=ip,
                request_id=request_id,
                outcome="FAILURE",
                event_metadata={"reason": "email_already_exists"},
            )
            db.add(audit)
            await db.commit()
            raise ConflictError("An account with this email address already exists")

        # Create user
        hashed_pw = hash_password(request.password)
        new_user = User(
            email=request.email.lower().strip(),
            password_hash=hashed_pw,
            role="owner",
            is_active=True,
        )
        db.add(new_user)
        await db.flush()

        # Audit successful registration
        audit = AuditEvent(
            user_id=new_user.id,
            action="REGISTER",
            resource_type="user",
            resource_id=new_user.id,
            ip=ip,
            request_id=request_id,
            outcome="SUCCESS",
            event_metadata={"email": new_user.email, "role": new_user.role},
        )
        db.add(audit)
        await db.commit()
        await db.refresh(new_user)

        return UserResponse.model_validate(new_user)

    async def login_user(
        self,
        db: AsyncSession,
        request: LoginRequest,
        ip: str | None = None,
        request_id: str | None = None,
    ) -> TokenResponse:
        # Find user
        query = select(User).where(User.email == request.email.lower().strip())
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user or not user.is_active or not verify_password(request.password, user.password_hash):
            audit = AuditEvent(
                user_id=user.id if user else None,
                action="LOGIN",
                resource_type="auth",
                resource_id=None,
                ip=ip,
                request_id=request_id,
                outcome="FAILURE",
                event_metadata={"attempted_email": request.email.lower().strip()},
            )
            db.add(audit)
            await db.commit()
            raise UnauthorizedError("Invalid email or password")

        # Generate access token
        access_token = create_access_token(
            subject=user.id,
            role=user.role,
        )

        # Generate and store rotating refresh token
        raw_refresh_token = generate_refresh_token()
        token_digest = hash_token(raw_refresh_token)
        expires_at = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        refresh_record = RefreshToken(
            user_id=user.id,
            token_hash=token_digest,
            revoked=False,
            expires_at=expires_at,
        )
        db.add(refresh_record)

        # Audit login success
        audit = AuditEvent(
            user_id=user.id,
            action="LOGIN",
            resource_type="auth",
            resource_id=user.id,
            ip=ip,
            request_id=request_id,
            outcome="SUCCESS",
            event_metadata={"role": user.role},
        )
        db.add(audit)
        await db.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def refresh_access_token(
        self,
        db: AsyncSession,
        raw_refresh_token: str,
        ip: str | None = None,
        request_id: str | None = None,
    ) -> TokenResponse:
        token_digest = hash_token(raw_refresh_token)
        now = datetime.now(UTC)

        # Look up valid unrevoked, unexpired refresh token
        query = select(RefreshToken).where(
            RefreshToken.token_hash == token_digest,
            RefreshToken.revoked.is_(False),
            RefreshToken.expires_at > now,
        )
        result = await db.execute(query)
        token_record = result.scalar_one_or_none()

        if not token_record:
            audit = AuditEvent(
                user_id=None,
                action="TOKEN_REFRESH",
                resource_type="auth",
                resource_id=None,
                ip=ip,
                request_id=request_id,
                outcome="FAILURE",
                event_metadata={"reason": "invalid_or_revoked_token"},
            )
            db.add(audit)
            await db.commit()
            raise UnauthorizedError("Invalid or expired refresh token")

        # Invalidate old token (Rotation)
        token_record.revoked = True

        # Fetch associated user
        user = await db.get(User, token_record.user_id)
        if not user or not user.is_active:
            raise UnauthorizedError("Associated user account is deactivated or deleted")

        # Generate new access token
        new_access_token = create_access_token(
            subject=user.id,
            role=user.role,
        )

        # Generate and store new refresh token
        new_raw_refresh = generate_refresh_token()
        new_digest = hash_token(new_raw_refresh)
        new_expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        new_refresh_record = RefreshToken(
            user_id=user.id,
            token_hash=new_digest,
            revoked=False,
            expires_at=new_expires_at,
        )
        db.add(new_refresh_record)

        # Audit token rotation
        audit = AuditEvent(
            user_id=user.id,
            action="TOKEN_REFRESH",
            resource_type="auth",
            resource_id=user.id,
            ip=ip,
            request_id=request_id,
            outcome="SUCCESS",
            event_metadata={},
        )
        db.add(audit)
        await db.commit()

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_raw_refresh,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def logout_user(
        self,
        db: AsyncSession,
        raw_refresh_token: str,
        user_id: str | None = None,
        ip: str | None = None,
        request_id: str | None = None,
    ) -> bool:
        token_digest = hash_token(raw_refresh_token)

        # Revoke token
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_digest)
            .values(revoked=True)
        )
        await db.execute(stmt)

        audit = AuditEvent(
            user_id=user_id,
            action="LOGOUT",
            resource_type="auth",
            resource_id=user_id,
            ip=ip,
            request_id=request_id,
            outcome="SUCCESS",
            event_metadata={},
        )
        db.add(audit)
        await db.commit()
        return True


auth_service = AuthService()
