from enum import StrEnum

from pydantic import BaseModel, Field


class DocumentTypeEnum(StrEnum):
    """Supported document types for insurance claim extraction."""

    POLICE_REPORT = "police_report"
    MEDICAL_RECORD = "medical_record"
    REPAIR_ESTIMATE = "repair_estimate"
    PROOF_OF_LOSS = "proof_of_loss"
    CORRESPONDENCE = "correspondence"
    OTHER = "other"


class PartyRoleEnum(StrEnum):
    """Categorization of entities involved in an insurance claim document."""

    CLAIMANT = "claimant"
    INSURED = "insured"
    WITNESS = "witness"
    OFFICER = "officer"
    PHYSICIAN = "physician"
    REPAIRER = "repairer"
    OTHER = "other"


class AmountTypeEnum(StrEnum):
    """Categorization of monetary sums found in insurance claim documents."""

    TOTAL_LOSS = "total_loss"
    ESTIMATED_REPAIR = "estimated_repair"
    MEDICAL_EXPENSE = "medical_expense"
    DEDUCTIBLE = "deductible"
    SETTLEMENT = "settlement"
    OTHER = "other"


class ExtractedDate(BaseModel):
    """A date mentioned in the document with context and source grounding info."""

    value: str
    context: str = Field(..., description="Context of date, e.g. date of loss, date of filing, incident date")
    grounded: bool = False
    page_number: int | None = None
    char_start: int | None = None
    char_end: int | None = None


class ExtractedParty(BaseModel):
    """An individual or organization mentioned in the document."""

    name: str
    role: PartyRoleEnum = PartyRoleEnum.OTHER
    role_description: str | None = None
    grounded: bool = False
    page_number: int | None = None
    char_start: int | None = None
    char_end: int | None = None


class ExtractedAmount(BaseModel):
    """A monetary amount mentioned in the document."""

    amount: float
    currency: str = "USD"
    amount_type: AmountTypeEnum = AmountTypeEnum.OTHER
    context: str | None = None
    grounded: bool = False
    page_number: int | None = None
    char_start: int | None = None
    char_end: int | None = None


class DocumentExtractionV1(BaseModel):
    """Structured extraction output schema for insurance claim documents (version 1)."""

    document_type: DocumentTypeEnum
    summary: str = Field(..., max_length=1000, description="Concise summary of the document contents")
    dates: list[ExtractedDate] = Field(default_factory=list)
    parties: list[ExtractedParty] = Field(default_factory=list)
    amounts: list[ExtractedAmount] = Field(default_factory=list)
    key_facts: list[str] = Field(default_factory=list, description="List of notable factual observations")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    all_entities_grounded: bool = False
