import pytest
from pydantic import ValidationError

from app.inference.claim_analysis_schemas import (
    ClaimDiscrepancy,
    ClaimIntelligenceAnalysisV1,
    DiscrepancyCategory,
    DiscrepancySeverity,
    DocumentCitation,
    TimelineEvent,
)
from app.inference.prompts.claim_intelligence_v1 import (
    CLAIM_INTELLIGENCE_SYSTEM_PROMPT,
    build_claim_intelligence_user_prompt,
)


def test_claim_intelligence_schema_instantiation():
    analysis = ClaimIntelligenceAnalysisV1(
        claim_id="claim-123",
        overall_risk_score=0.45,
        executive_summary="Discrepancy found between police report and repair invoice.",
        timeline=[
            TimelineEvent(
                date="2024-03-10",
                event_description="Vehicle collision on Main St.",
                document_id="doc-1",
            ),
            TimelineEvent(
                date="2024-03-11",
                event_description="Emergency room examination.",
                document_id="doc-2",
            ),
        ],
        discrepancies=[
            ClaimDiscrepancy(
                id="disc-1",
                title="Conflicting Incident Date",
                description="Police report dates collision on March 10 while repair shop lists March 08.",
                category=DiscrepancyCategory.DATE_INCONSISTENCY,
                severity=DiscrepancySeverity.HIGH,
                confidence=0.92,
                citations=[
                    DocumentCitation(
                        document_id="doc-1",
                        document_name="police_report.pdf",
                        quoted_statement="Date of occurrence: 2024-03-10.",
                        page_number=1,
                    ),
                    DocumentCitation(
                        document_id="doc-3",
                        document_name="estimate.pdf",
                        quoted_statement="Vehicle admitted: 2024-03-08.",
                        page_number=1,
                    ),
                ],
                recommended_action="Contact auto body shop to verify admission date.",
            )
        ],
        unresolved_questions=["Why was vehicle admitted before reported incident?"],
        confidence_score=0.95,
    )

    assert analysis.claim_id == "claim-123"
    assert analysis.overall_risk_score == 0.45
    assert len(analysis.timeline) == 2
    assert len(analysis.discrepancies) == 1
    assert analysis.discrepancies[0].severity == "high"
    assert analysis.discrepancies[0].category == "date_inconsistency"


def test_claim_intelligence_risk_score_bounds():
    with pytest.raises(ValidationError):
        ClaimIntelligenceAnalysisV1(
            claim_id="claim-1",
            overall_risk_score=1.5,  # Exceeds max 1.0
            executive_summary="Invalid risk",
        )

    with pytest.raises(ValidationError):
        ClaimIntelligenceAnalysisV1(
            claim_id="claim-1",
            overall_risk_score=-0.1,  # Below min 0.0
            executive_summary="Invalid risk",
        )


def test_build_claim_intelligence_user_prompt():
    claim_meta = {"title": "Rear-end collision", "policy_number": "POL-9876", "status": "OPEN"}
    extractions = [
        {
            "id": "doc-1",
            "original_filename": "police.pdf",
            "document_type": "police_report",
            "summary": "Rear-end impact on highway.",
            "dates": [{"value": "2024-03-10", "context": "crash date"}],
            "parties": [{"name": "Officer Smith", "role": "officer"}],
            "amounts": [],
            "key_facts": ["Clear weather, dry road."],
        },
        {
            "id": "doc-2",
            "original_filename": "repair.pdf",
            "document_type": "repair_estimate",
            "summary": "Front bumper replacement estimate.",
            "dates": [{"value": "2024-03-12", "context": "estimate date"}],
            "parties": [{"name": "Apex Auto", "role": "repairer"}],
            "amounts": [{"amount": 2400.0, "currency": "USD"}],
            "key_facts": ["Front bumper replacement required."],
        },
    ]

    prompt = build_claim_intelligence_user_prompt("claim-123", claim_meta, extractions)
    assert "Claim ID: claim-123" in prompt
    assert "POL-9876" in prompt
    assert "Document #1 (ID: doc-1, Filename: police.pdf)" in prompt
    assert "Document #2 (ID: doc-2, Filename: repair.pdf)" in prompt
    assert "CLAIM_INTELLIGENCE_SYSTEM_PROMPT" in globals()
    assert "Senior Forensic Auditor" in CLAIM_INTELLIGENCE_SYSTEM_PROMPT
