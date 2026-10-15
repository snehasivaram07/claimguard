from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.errors import NotFoundError
from app.core.limiter import limiter
from app.db.models.audit import AuditEvent
from app.db.models.user import User
from app.db.session import get_db
from app.inference.claim_analysis_schemas import ClaimIntelligenceAnalysisV1
from app.schemas.audit import AuditTrailResponse
from app.schemas.claim import (
    ClaimCreateRequest,
    ClaimListResponse,
    ClaimResponse,
    ClaimUpdateRequest,
)
from app.services.audit_service import audit_service
from app.services.claim_intelligence_service import claim_intelligence_service
from app.services.claim_service import claim_service

router = APIRouter(prefix="/claims", tags=["Claims"])


@router.post(
    "",
    response_model=ClaimResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new insurance claim",
)
async def create_claim(
    request: Request,
    payload: ClaimCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ClaimResponse:
    client_ip = request.client.host if request.client else None
    request_id = getattr(request.state, "request_id", None)
    return await claim_service.create_claim(
        owner_id=current_user.id,
        request=payload,
        db=db,
        ip=client_ip,
        request_id=request_id,
    )


@router.get(
    "",
    response_model=ClaimListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all claims owned by the authenticated user",
)
async def list_claims(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    include_archived: bool = Query(False, description="Whether to include archived claims"),
    current_user: User = Depends(get_current_user),
) -> ClaimListResponse:
    return await claim_service.list_claims(
        owner_id=current_user.id,
        skip=skip,
        limit=limit,
        include_archived=include_archived,
    )


@router.get(
    "/{claim_id}",
    response_model=ClaimResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve details of a specific claim",
)
async def get_claim(
    claim_id: str,
    current_user: User = Depends(get_current_user),
) -> ClaimResponse:
    return await claim_service.get_claim(
        owner_id=current_user.id,
        claim_id=claim_id,
    )


@router.patch(
    "/{claim_id}",
    response_model=ClaimResponse,
    status_code=status.HTTP_200_OK,
    summary="Update details of an existing claim",
)
async def update_claim(
    claim_id: str,
    request: Request,
    payload: ClaimUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ClaimResponse:
    client_ip = request.client.host if request.client else None
    request_id = getattr(request.state, "request_id", None)
    return await claim_service.update_claim(
        owner_id=current_user.id,
        claim_id=claim_id,
        request=payload,
        db=db,
        ip=client_ip,
        request_id=request_id,
    )


@router.delete(
    "/{claim_id}",
    status_code=status.HTTP_200_OK,
    summary="Soft-delete a claim (marks status as ARCHIVED)",
)
async def delete_claim(
    claim_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    client_ip = request.client.host if request.client else None
    request_id = getattr(request.state, "request_id", None)
    await claim_service.delete_claim(
        owner_id=current_user.id,
        claim_id=claim_id,
        db=db,
        ip=client_ip,
        request_id=request_id,
    )
    return {"message": "Claim successfully archived", "id": claim_id}


@router.get(
    "/{claim_id}/audit",
    response_model=AuditTrailResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve audit trail for a specific claim",
)
async def get_claim_audit(
    claim_id: str,
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AuditTrailResponse:
    # Strict multi-tenant verification: raises 404 Not Found if claim does not exist or belongs to another user
    await claim_service.get_claim(owner_id=current_user.id, claim_id=claim_id)
    items, total = await audit_service.get_claim_audit_events(
        db=db,
        claim_id=claim_id,
        skip=skip,
        limit=limit,
    )
    return AuditTrailResponse(total=total, items=items)


@router.post(
    "/{claim_id}/analyze",
    response_model=ClaimIntelligenceAnalysisV1,
    status_code=status.HTTP_200_OK,
    summary="Trigger cross-document intelligence analysis, timeline reconstruction, and discrepancy detection",
)
@limiter.limit(f"{settings.RATE_LIMIT_ANALYZE_PER_MINUTE}/minute")
async def analyze_claim(
    claim_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ClaimIntelligenceAnalysisV1:
    client_ip = request.client.host if request.client else None
    request_id = getattr(request.state, "request_id", None)

    # 1. Audit analysis requested
    audit_requested = AuditEvent(
        user_id=current_user.id,
        action="CLAIM_ANALYSIS_REQUESTED",
        resource_type="claim",
        resource_id=claim_id,
        ip=client_ip,
        request_id=request_id,
        outcome="SUCCESS",
        event_metadata={"claim_id": claim_id},
    )
    db.add(audit_requested)
    await db.commit()

    try:
        # 2. Run claim intelligence service
        analysis = await claim_intelligence_service.analyze_claim(
            owner_id=current_user.id,
            claim_id=claim_id,
        )

        # 3. Audit analysis completed (metadata contains counts only, never raw text)
        audit_completed = AuditEvent(
            user_id=current_user.id,
            action="CLAIM_ANALYSIS_COMPLETED",
            resource_type="claim",
            resource_id=claim_id,
            ip=client_ip,
            request_id=request_id,
            outcome="SUCCESS",
            event_metadata={
                "claim_id": claim_id,
                "overall_risk_score": analysis.overall_risk_score,
                "confidence_score": analysis.confidence_score,
                "timeline_events_count": len(analysis.timeline),
                "discrepancies_count": len(analysis.discrepancies),
                "unresolved_questions_count": len(analysis.unresolved_questions),
            },
        )
        db.add(audit_completed)
        await db.commit()
        return analysis

    except Exception as exc:
        error_code = getattr(exc, "code", "ANALYSIS_FAILED")
        audit_failed = AuditEvent(
            user_id=current_user.id,
            action="CLAIM_ANALYSIS_FAILED",
            resource_type="claim",
            resource_id=claim_id,
            ip=client_ip,
            request_id=request_id,
            outcome="FAILURE",
            event_metadata={
                "claim_id": claim_id,
                "error_code": error_code,
            },
        )
        db.add(audit_failed)
        await db.commit()
        raise


@router.get(
    "/{claim_id}/intelligence",
    response_model=ClaimIntelligenceAnalysisV1,
    status_code=status.HTTP_200_OK,
    summary="Retrieve cached claim intelligence analysis, timeline, and discrepancy report",
)
async def get_claim_intelligence(
    claim_id: str,
    current_user: User = Depends(get_current_user),
) -> ClaimIntelligenceAnalysisV1:
    analysis = claim_intelligence_service.get_claim_analysis(
        owner_id=current_user.id,
        claim_id=claim_id,
    )
    if not analysis:
        raise NotFoundError(f"Intelligence analysis not found for claim {claim_id}")
    return analysis

