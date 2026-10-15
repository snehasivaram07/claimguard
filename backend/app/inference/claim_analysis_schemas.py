from enum import StrEnum

from pydantic import BaseModel, Field


class DiscrepancySeverity(StrEnum):
    """Severity classification for factual contradictions between documents in a claim."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DiscrepancyCategory(StrEnum):
    """Categorization of cross-document discrepancies discovered during claim intelligence."""

    DATE_INCONSISTENCY = "date_inconsistency"
    AMOUNT_MISMATCH = "amount_mismatch"
    DAMAGE_LOCATION_CONFLICT = "damage_location_conflict"
    PARTY_INVOLVEMENT_CONFLICT = "party_involvement_conflict"
    FACTUAL_CONTRADICTION = "factual_contradiction"
    OTHER = "other"


class DocumentCitation(BaseModel):
    """Specific textual quote and document reference supporting a flagged discrepancy."""

    document_id: str
    document_name: str | None = None
    quoted_statement: str
    page_number: int | None = None


class ClaimDiscrepancy(BaseModel):
    """A factual contradiction or timeline mismatch between two or more documents."""

    id: str
    title: str
    description: str
    category: DiscrepancyCategory
    severity: DiscrepancySeverity
    confidence: float = Field(..., ge=0.0, le=1.0)
    citations: list[DocumentCitation] = Field(default_factory=list)
    recommended_action: str | None = None


class TimelineEvent(BaseModel):
    """Chronologically sorted event extracted from claim documents."""

    date: str
    event_description: str
    document_id: str
    source_context: str | None = None


class ClaimIntelligenceAnalysisV1(BaseModel):
    """Structured forensic intelligence output comparing all evidence attached to a claim."""

    claim_id: str
    overall_risk_score: float = Field(default=0.0, ge=0.0, le=1.0)
    executive_summary: str = Field(..., max_length=2000)
    timeline: list[TimelineEvent] = Field(default_factory=list)
    discrepancies: list[ClaimDiscrepancy] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    analyzed_at: str | None = None
