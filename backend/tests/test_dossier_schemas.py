import pytest
from pydantic import ValidationError

from app.schemas.dossier import (
    DossierClaimMetadata,
    DossierDiscrepancyItem,
    DossierDocumentSummary,
    DossierExportFormat,
    DossierExportResponse,
    DossierFraudRingItem,
    DossierRecommendationItem,
    DossierTimelineEvent,
    ForensicDossierV1,
)


def test_dossier_export_formats():
    assert DossierExportFormat.JSON == "json"
    assert DossierExportFormat.MARKDOWN == "markdown"
    assert DossierExportFormat.HTML == "html"
    assert list(DossierExportFormat) == ["json", "markdown", "html"]


def test_dossier_claim_metadata_defaults():
    meta = DossierClaimMetadata(
        claim_id="claim-123",
        title="Collision Claim",
    )
    assert meta.claim_id == "claim-123"
    assert meta.title == "Collision Claim"
    assert meta.claim_type == "GENERAL"
    assert meta.claim_number is None
    assert meta.policy_number is None
    assert meta.status == "OPEN"
    assert meta.description == ""


def test_dossier_document_summary():
    doc = DossierDocumentSummary(
        document_id="doc-999",
        original_filename="police_report.pdf",
        status="COMPLETED",
        size_bytes=10240,
        extracted_entities_count=5,
        extracted_dates_count=3,
    )
    assert doc.document_id == "doc-999"
    assert doc.original_filename == "police_report.pdf"
    assert doc.document_type == "GENERAL_ATTACHMENT"
    assert doc.extracted_entities_count == 5
    assert doc.extracted_dates_count == 3


def test_dossier_timeline_event():
    event = DossierTimelineEvent(
        date="2026-03-15",
        event_description="Vehicle accident occurred on Interstate 95",
        document_id="doc-1",
        document_name="police_report.pdf",
        source_context="Page 1 narrative",
    )
    assert event.date == "2026-03-15"
    assert event.event_description == "Vehicle accident occurred on Interstate 95"
    assert event.document_id == "doc-1"
    assert event.document_name == "police_report.pdf"


def test_dossier_discrepancy_item():
    discrepancy = DossierDiscrepancyItem(
        id="disc-1",
        title="Incident date mismatch",
        description="Police report says March 15 but repair estimate says March 18",
        category="date_inconsistency",
        severity="high",
        confidence=0.95,
        citations=[
            {"document_id": "doc-1", "quoted_statement": "Accident occurred March 15"},
            {"document_id": "doc-2", "quoted_statement": "Repairs initiated following accident on March 18"},
        ],
        recommended_action="Contact insured to verify exact loss date",
    )
    assert discrepancy.id == "disc-1"
    assert discrepancy.severity == "high"
    assert len(discrepancy.citations) == 2


def test_dossier_fraud_ring_item_and_validation():
    ring = DossierFraudRingItem(
        ring_id="ring-101",
        pattern="staged_collision_ring",
        severity="critical",
        risk_score=0.88,
        title="Interstate 95 Staged Collisions",
        summary="Multiple claims sharing same body shop and legal counsel",
        claim_ids=["claim-1", "claim-2", "claim-3"],
        shared_entities=[{"name": "Metro Auto Body", "type": "organization", "claim_count": 3}],
        suspicious_indicators=["Recurring provider across unconnected claimants"],
        recommended_siu_actions=["Issue subpoena for body shop repair invoices"],
    )
    assert ring.ring_id == "ring-101"
    assert ring.risk_score == 0.88
    assert len(ring.claim_ids) == 3

    # Risk score > 1.0 must fail
    with pytest.raises(ValidationError):
        DossierFraudRingItem(
            ring_id="ring-bad",
            pattern="other",
            severity="low",
            risk_score=1.5,
            title="Invalid Score",
            summary="Bad",
        )


def test_dossier_recommendation_item():
    rec = DossierRecommendationItem(
        priority="HIGH",
        category="INTERVIEW",
        action="Conduct recorded examination under oath (EUO) with claimant",
        rationale="Discrepancies in medical billing timeline",
    )
    assert rec.priority == "HIGH"
    assert rec.category == "INTERVIEW"
    assert "EUO" in rec.action


def test_forensic_dossier_v1_serialization_and_roundtrip():
    dossier = ForensicDossierV1(
        dossier_id="dossier-claim-1",
        claim_id="claim-1",
        owner_id="tenant-alpha",
        generated_at="2026-10-16T10:00:00Z",
        overall_risk_score=0.85,
        fraud_classification="HIGH_RISK_COLLUSION",
        executive_summary="Claim exhibits multi-document contradictions and participation in a detected fraud ring.",
        claim_metadata=DossierClaimMetadata(
            claim_id="claim-1",
            title="Auto Collision Claim",
            claim_number="CLM-001",
            policy_number="POL-999",
            status="OPEN",
        ),
        documents_summary=[
            DossierDocumentSummary(
                document_id="doc-1",
                original_filename="police_report.pdf",
                status="COMPLETED",
                size_bytes=5120,
            )
        ],
        chronological_timeline=[
            DossierTimelineEvent(
                date="2026-03-15",
                event_description="Accident reported",
                document_id="doc-1",
            )
        ],
        contradictions_and_discrepancies=[
            DossierDiscrepancyItem(
                id="disc-1",
                title="Date conflict",
                description="Dates differ",
                category="date_inconsistency",
                severity="medium",
                confidence=0.9,
            )
        ],
        associated_fraud_rings=[
            DossierFraudRingItem(
                ring_id="ring-1",
                pattern="provider_fraud_collusion",
                severity="high",
                risk_score=0.75,
                title="Provider Ring",
                summary="Shared clinic",
            )
        ],
        investigator_recommendations=[
            DossierRecommendationItem(
                priority="HIGH",
                category="FORENSIC_AUDIT",
                action="Subpoena clinic records",
                rationale="Excessive treatments billed",
            )
        ],
        unresolved_questions=["Why was initial police report filed 14 days post incident?"],
    )

    data = dossier.model_dump()
    assert data["dossier_id"] == "dossier-claim-1"
    assert data["overall_risk_score"] == 0.85
    assert data["fraud_classification"] == "HIGH_RISK_COLLUSION"
    assert len(data["contradictions_and_discrepancies"]) == 1

    json_str = dossier.model_dump_json()
    reconstituted = ForensicDossierV1.model_validate_json(json_str)
    assert reconstituted.claim_id == dossier.claim_id
    assert reconstituted.claim_metadata.policy_number == "POL-999"
    assert len(reconstituted.investigator_recommendations) == 1
    assert reconstituted.investigator_recommendations[0].priority == "HIGH"


def test_dossier_export_response():
    resp = DossierExportResponse(
        claim_id="claim-123",
        format=DossierExportFormat.HTML,
        content_type="text/html; charset=utf-8",
        filename="claim_123_siu_dossier.html",
        content="<html><body><h1>Dossier</h1></body></html>",
    )
    assert resp.claim_id == "claim-123"
    assert resp.format == DossierExportFormat.HTML
    assert resp.content_type == "text/html; charset=utf-8"
    assert resp.filename == "claim_123_siu_dossier.html"
    assert "<html>" in resp.content
