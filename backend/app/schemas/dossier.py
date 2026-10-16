from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class DossierExportFormat(StrEnum):
    """Supported export serialization formats for Special Investigation Unit (SIU) dossiers."""

    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"


class DossierClaimMetadata(BaseModel):
    """Core insurance claim metadata embedded into the forensic dossier."""

    claim_id: str
    title: str
    claim_type: str = "GENERAL"
    claim_number: str | None = None
    policy_number: str | None = None
    description: str = ""
    status: str = "OPEN"
    created_at: str | None = None
    updated_at: str | None = None


class DossierDocumentSummary(BaseModel):
    """Summary of an evidentiary document attached to the claim."""

    document_id: str
    original_filename: str
    document_type: str = "GENERAL_ATTACHMENT"
    status: str
    size_bytes: int = 0
    uploaded_at: str | None = None
    extracted_entities_count: int = 0
    extracted_dates_count: int = 0


class DossierTimelineEvent(BaseModel):
    """Chronologically sorted incident or claim event with source attribution."""

    date: str
    event_description: str
    document_id: str | None = None
    document_name: str | None = None
    source_context: str | None = None


class DossierDiscrepancyItem(BaseModel):
    """Contradiction or factual inconsistency identified across claim evidence."""

    id: str
    title: str
    description: str
    category: str
    severity: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    citations: list[dict[str, Any]] = Field(default_factory=list)
    recommended_action: str | None = None


class DossierFraudRingItem(BaseModel):
    """Collusion network or fraud ring associated with the investigated claim."""

    ring_id: str
    pattern: str
    severity: str
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0)
    title: str
    summary: str
    claim_ids: list[str] = Field(default_factory=list)
    shared_entities: list[dict[str, Any]] = Field(default_factory=list)
    suspicious_indicators: list[str] = Field(default_factory=list)
    recommended_siu_actions: list[str] = Field(default_factory=list)


class DossierRecommendationItem(BaseModel):
    """Actionable recommendation for SIU field investigators or claims adjusters."""

    priority: str  # "HIGH", "MEDIUM", "LOW"
    category: str  # "INTERVIEW", "EVIDENCE_COLLECTION", "FORENSIC_AUDIT", "LEGAL"
    action: str
    rationale: str


class ForensicDossierV1(BaseModel):
    """Comprehensive forensic Special Investigation Unit (SIU) claim dossier."""

    dossier_id: str
    claim_id: str
    owner_id: str
    generated_at: str
    overall_risk_score: float = Field(default=0.0, ge=0.0, le=1.0)
    fraud_classification: str = "LOW_RISK"
    executive_summary: str
    claim_metadata: DossierClaimMetadata
    documents_summary: list[DossierDocumentSummary] = Field(default_factory=list)
    chronological_timeline: list[DossierTimelineEvent] = Field(default_factory=list)
    contradictions_and_discrepancies: list[DossierDiscrepancyItem] = Field(default_factory=list)
    associated_fraud_rings: list[DossierFraudRingItem] = Field(default_factory=list)
    network_subgraph: dict[str, Any] | None = None
    investigator_recommendations: list[DossierRecommendationItem] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    evidentiary_citations: list[dict[str, Any]] = Field(default_factory=list)


class DossierExportResponse(BaseModel):
    """Container for serialized dossier export payloads ready for download or client delivery."""

    claim_id: str
    format: DossierExportFormat
    content_type: str
    filename: str
    content: str
