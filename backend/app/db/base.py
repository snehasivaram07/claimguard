from datetime import UTC, datetime

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy relational models."""
    pass


def utc_now() -> datetime:
    """Helper to return current UTC timezone-aware datetime."""
    return datetime.now(UTC)
