from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditEventResponse(BaseModel):
    """Schema representing an individual append-only audit event record."""

    model_config = ConfigDict(from_attributes=True)

    event_id: str
    timestamp: datetime
    user_id: str | None = None
    action: str
    resource_type: str
    resource_id: str | None = None
    ip: str | None = None
    request_id: str | None = None
    outcome: str
    metadata: dict[str, Any] = Field(default_factory=dict, alias="event_metadata")


class AuditTrailResponse(BaseModel):
    """Paginated collection of audit event records."""

    total: int
    items: list[AuditEventResponse]
