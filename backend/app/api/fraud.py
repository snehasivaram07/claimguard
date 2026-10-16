from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.limiter import limiter
from app.db.models.audit import AuditEvent
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.fraud_ring import FraudRingListResponse
from app.services.fraud_ring_service import fraud_ring_service

router = APIRouter(prefix="/fraud-rings", tags=["Fraud Rings"])


@router.get(
    "",
    response_model=FraudRingListResponse,
    status_code=status.HTTP_200_OK,
    summary="Detect and list all multi-claim fraud rings and collusion syndicates",
)
@limiter.limit(f"{settings.RATE_LIMIT_FRAUD_NETWORK_PER_MINUTE}/minute")
async def list_fraud_rings(
    request: Request,
    min_shared: int = Query(
        2, ge=1, le=10, description="Minimum shared entities required to form a ring"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FraudRingListResponse:
    client_ip = request.client.host if request.client else None
    request_id = getattr(request.state, "request_id", None)

    rings = await fraud_ring_service.detect_fraud_rings(
        owner_id=current_user.id,
        min_shared=min_shared,
    )

    audit_detected = AuditEvent(
        user_id=current_user.id,
        action="FRAUD_RINGS_DETECTED",
        resource_type="fraud_ring",
        resource_id="all",
        ip=client_ip,
        request_id=request_id,
        outcome="SUCCESS",
        event_metadata={
            "min_shared": min_shared,
            "rings_count": len(rings),
        },
    )
    db.add(audit_detected)
    await db.commit()

    return FraudRingListResponse(rings=rings, total=len(rings))
