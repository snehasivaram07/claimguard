from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Query,
    Request,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
    PresignedUrlResponse,
)
from app.services.document_service import document_service

router = APIRouter(prefix="/claims/{claim_id}/documents", tags=["Documents"])


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload an untrusted document to a claim",
)
async def upload_document(
    claim_id: str,
    request: Request,
    file: UploadFile = File(..., description="Document file binary"),
    allow_duplicate: bool = Query(
        False, description="Whether to allow uploading duplicate files with matching content hash"
    ),
    document_type: str = Form(
        "GENERAL_ATTACHMENT", description="Document type tag e.g. POLICY, POLICE_REPORT, ESTIMATE"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    client_ip = request.client.host if request.client else None
    request_id = getattr(request.state, "request_id", None)
    return await document_service.upload_document(
        owner_id=current_user.id,
        claim_id=claim_id,
        upload_file=file,
        allow_duplicate=allow_duplicate,
        document_type=document_type,
        db=db,
        ip=client_ip,
        request_id=request_id,
    )


@router.get(
    "",
    response_model=DocumentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all documents attached to a claim",
)
async def list_documents(
    claim_id: str,
    include_archived: bool = Query(False, description="Whether to include soft-deleted documents"),
    current_user: User = Depends(get_current_user),
) -> DocumentListResponse:
    return await document_service.list_documents(
        owner_id=current_user.id,
        claim_id=claim_id,
        include_archived=include_archived,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve document metadata",
)
async def get_document(
    claim_id: str,
    document_id: str,
    current_user: User = Depends(get_current_user),
) -> DocumentResponse:
    return await document_service.get_document(
        owner_id=current_user.id,
        claim_id=claim_id,
        document_id=document_id,
    )


@router.get(
    "/{document_id}/download-url",
    response_model=PresignedUrlResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a short-lived presigned download URL",
)
async def get_download_url(
    claim_id: str,
    document_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PresignedUrlResponse:
    client_ip = request.client.host if request.client else None
    request_id = getattr(request.state, "request_id", None)
    return await document_service.generate_download_url(
        owner_id=current_user.id,
        claim_id=claim_id,
        document_id=document_id,
        db=db,
        ip=client_ip,
        request_id=request_id,
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_200_OK,
    summary="Soft-delete a document (marks status as ARCHIVED)",
)
async def delete_document(
    claim_id: str,
    document_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    client_ip = request.client.host if request.client else None
    request_id = getattr(request.state, "request_id", None)
    await document_service.delete_document(
        owner_id=current_user.id,
        claim_id=claim_id,
        document_id=document_id,
        db=db,
        ip=client_ip,
        request_id=request_id,
    )
    return {"message": "Document successfully archived", "id": document_id}
