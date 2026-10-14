import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.models.audit import AuditEvent
from app.db.models.token import RefreshToken
from app.db.models.user import User


@pytest.fixture
async def test_db_session():
    """Provides an isolated in-memory SQLite async database session for testing models."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_user_creation_and_defaults(test_db_session: AsyncSession):
    user = User(
        email="test@example.com",
        password_hash="argon2_hashed_secret",
    )
    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)

    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.role == "owner"
    assert user.is_active is True
    assert user.created_at is not None
    assert user.updated_at is not None


@pytest.mark.asyncio
async def test_refresh_token_cascade_and_rotation(test_db_session: AsyncSession):
    user = User(
        email="token_user@example.com",
        password_hash="argon2_hashed_secret",
    )
    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)

    token = RefreshToken(
        user_id=user.id,
        token_hash="hashed_refresh_token_123",
        expires_at=datetime.now(UTC),
    )
    test_db_session.add(token)
    await test_db_session.commit()
    await test_db_session.refresh(token)

    assert token.id is not None
    assert token.user_id == user.id
    assert token.revoked is False

    # Mark as revoked (rotation)
    token.revoked = True
    await test_db_session.commit()
    await test_db_session.refresh(token)
    assert token.revoked is True


@pytest.mark.asyncio
async def test_audit_event_logging(test_db_session: AsyncSession):
    event = AuditEvent(
        event_id=str(uuid.uuid4()),
        user_id="user-123",
        action="LOGIN_SUCCESS",
        resource_type="auth",
        resource_id=None,
        ip="127.0.0.1",
        request_id="req-abc-999",
        outcome="SUCCESS",
        event_metadata={"client": "pytest", "scope": "claims"},
    )
    test_db_session.add(event)
    await test_db_session.commit()

    result = await test_db_session.execute(
        select(AuditEvent).where(AuditEvent.event_id == event.event_id)
    )
    persisted = result.scalar_one()

    assert persisted.action == "LOGIN_SUCCESS"
    assert persisted.event_metadata["client"] == "pytest"
    assert persisted.outcome == "SUCCESS"
