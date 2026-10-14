import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, utc_now


class AuditEvent(Base):
    """Append-only audit log table capturing security-relevant events."""

    __tablename__ = "audit_events"

    event_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
    )
    user_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    resource_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    resource_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    ip: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )
    request_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )
    outcome: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    event_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSON,
        default=dict,
        nullable=False,
    )
