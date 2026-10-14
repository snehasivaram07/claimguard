from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.models.audit import AuditEvent


class AuditService:
    """Service providing append-only persistence and query capabilities for security audit events."""

    async def record_event(
        self,
        db: AsyncSession,
        *,
        action: str,
        resource_type: str,
        outcome: str = "SUCCESS",
        resource_id: str | None = None,
        user_id: str | None = None,
        ip: str | None = None,
        request_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Persists a new structured audit event into PostgreSQL."""
        event = AuditEvent(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip=ip,
            request_id=request_id,
            outcome=outcome,
            event_metadata=metadata or {},
        )
        db.add(event)
        await db.flush()
        logger.info(
            "Audit event recorded: action=%s, resource_type=%s, outcome=%s, user=%s",
            action,
            resource_type,
            outcome,
            user_id,
            extra={
                "audit_action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "outcome": outcome,
                "request_id": request_id,
            },
        )
        return event

    async def get_user_audit_events(
        self,
        db: AsyncSession,
        user_id: str,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[AuditEvent], int]:
        """Retrieves paginated audit events associated with a specific user account."""
        stmt = (
            select(AuditEvent)
            .where(AuditEvent.user_id == user_id)
            .order_by(AuditEvent.timestamp.desc())
            .offset(skip)
            .limit(min(limit, 100))
        )
        result = await db.execute(stmt)
        items = list(result.scalars().all())

        count_stmt = (
            select(func.count())
            .select_from(AuditEvent)
            .where(AuditEvent.user_id == user_id)
        )
        count_res = await db.execute(count_stmt)
        total = count_res.scalar() or 0

        return items, total

    async def get_claim_audit_events(
        self,
        db: AsyncSession,
        claim_id: str,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[AuditEvent], int]:
        """Retrieves paginated audit events for actions executed on a specific claim."""
        stmt = (
            select(AuditEvent)
            .where(
                AuditEvent.resource_type == "claim",
                AuditEvent.resource_id == claim_id,
            )
            .order_by(AuditEvent.timestamp.desc())
            .offset(skip)
            .limit(min(limit, 100))
        )
        result = await db.execute(stmt)
        items = list(result.scalars().all())

        count_stmt = (
            select(func.count())
            .select_from(AuditEvent)
            .where(
                AuditEvent.resource_type == "claim",
                AuditEvent.resource_id == claim_id,
            )
        )
        count_res = await db.execute(count_stmt)
        total = count_res.scalar() or 0

        return items, total

    async def query_events(
        self,
        db: AsyncSession,
        *,
        user_id: str | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        outcome: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[AuditEvent], int]:
        """General multi-filter search across audit logs with total count."""
        filters = []
        if user_id is not None:
            filters.append(AuditEvent.user_id == user_id)
        if action is not None:
            filters.append(AuditEvent.action == action)
        if resource_type is not None:
            filters.append(AuditEvent.resource_type == resource_type)
        if resource_id is not None:
            filters.append(AuditEvent.resource_id == resource_id)
        if outcome is not None:
            filters.append(AuditEvent.outcome == outcome)

        stmt = select(AuditEvent)
        count_stmt = select(func.count()).select_from(AuditEvent)

        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        stmt = stmt.order_by(AuditEvent.timestamp.desc()).offset(skip).limit(min(limit, 100))

        result = await db.execute(stmt)
        items = list(result.scalars().all())

        count_res = await db.execute(count_stmt)
        total = count_res.scalar() or 0

        return items, total


audit_service = AuditService()
