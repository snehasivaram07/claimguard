from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.claim import (
    ClaimCreateRequest,
    ClaimListResponse,
    ClaimResponse,
    ClaimUpdateRequest,
)
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
