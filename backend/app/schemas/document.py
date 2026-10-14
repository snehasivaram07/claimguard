from enum import StrEnum

from pydantic import BaseModel, Field


class IngestionStatus(StrEnum):
    """Complete document ingestion lifecycle status enum across all ClaimGuard phases."""
    RECEIVED = "RECEIVED"
    VALIDATING = "VALIDATING"
    STORED = "STORED"  # Phase 1 terminal status
    EXTRACTING = "EXTRACTING"
    INDEXING = "INDEXING"
    MATCHING_CLAIM = "MATCHING_CLAIM"
    ANALYZING = "ANALYZING"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    COMPLETED = "COMPLETED"
    FAILED_RETRYABLE = "FAILED_RETRYABLE"
    RETRYING = "RETRYING"
    FAILED_FINAL = "FAILED_FINAL"
    ARCHIVED = "ARCHIVED"


class DocumentResponse(BaseModel):
    id: str
    claim_id: str
    owner_id: str
    object_key: str
    content_hash: str
    document_type: str = "GENERAL_ATTACHMENT"
    original_filename: str
    size_bytes: int
    mime_type: str
    uploaded_at: str
    version: int = 1
    status: str = Field(default=IngestionStatus.STORED.value)
    schema_version: int = 1


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int


class PresignedUrlResponse(BaseModel):
    document_id: str
    download_url: str
    expires_in_seconds: int = 300
