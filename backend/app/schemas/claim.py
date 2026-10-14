from enum import StrEnum

from pydantic import BaseModel, Field


class ClaimStatus(StrEnum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"


class ClaimCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Descriptive title of the insurance claim")
    claim_type: str = Field(default="GENERAL", max_length=64, description="Category of claim e.g. AUTO, PROPERTY, HEALTH")
    claim_number: str | None = Field(default=None, max_length=64, description="Optional insurer internal claim identifier")
    policy_number: str | None = Field(default=None, max_length=64, description="Optional policy reference number")
    description: str | None = Field(default="", max_length=4000, description="Detailed description of the claim circumstances")


class ClaimUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    claim_type: str | None = Field(default=None, max_length=64)
    claim_number: str | None = Field(default=None, max_length=64)
    policy_number: str | None = Field(default=None, max_length=64)
    description: str | None = Field(default=None, max_length=4000)
    status: ClaimStatus | None = None


class ClaimResponse(BaseModel):
    id: str
    owner_id: str
    title: str
    claim_type: str
    claim_number: str | None = None
    policy_number: str | None = None
    description: str
    status: str
    created_at: str
    updated_at: str
    schema_version: int = 1


class ClaimListResponse(BaseModel):
    items: list[ClaimResponse]
    total: int
    skip: int
    limit: int
