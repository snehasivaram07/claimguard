from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.errors import NotFoundError
from app.inference.claim_analysis_schemas import (
    ClaimDiscrepancy,
    ClaimIntelligenceAnalysisV1,
    DiscrepancyCategory,
    DiscrepancySeverity,
    DocumentCitation,
    TimelineEvent,
)
from app.schemas.claim import ClaimResponse
from app.schemas.dossier import DossierExportFormat, ForensicDossierV1
from app.schemas.fraud_ring import (
    ClaimFraudNetworkResponse,
    FraudRingAnalysisV1,
    FraudRingEdge,
    FraudRingNode,
    FraudRingPattern,
    FraudRingSeverity,
    SharedEntitySummary,
)
from app.services.dossier_service import DossierService


@pytest.fixture
def mock_claim_srv():
    srv = MagicMock()
    srv.get_claim = AsyncMock()
    return srv


@pytest.fixture
def mock_document_repo():
    repo = MagicMock()
    repo.list_documents_for_claim = MagicMock()
    return repo


@pytest.fixture
def mock_intelligence_srv():
    srv = MagicMock()
    srv.get_claim_analysis = MagicMock()
    return srv


@pytest.fixture
def mock_fraud_srv():
    srv = MagicMock()
    srv.get_claim_network = AsyncMock()
    return srv


@pytest.fixture
def dossier_service_instance(mock_claim_srv, mock_document_repo, mock_intelligence_srv, mock_fraud_srv):
    return DossierService(
        claim_srv=mock_claim_srv,
        document_repository=mock_document_repo,
        intelligence_srv=mock_intelligence_srv,
        fraud_srv=mock_fraud_srv,
    )


@pytest.mark.asyncio
async def test_generate_dossier_claim_not_found(dossier_service_instance, mock_claim_srv):
    mock_claim_srv.get_claim.side_effect = NotFoundError("Claim not found")

    with pytest.raises(NotFoundError):
        await dossier_service_instance.generate_dossier(owner_id="tenant-1", claim_id="claim-missing")

    mock_claim_srv.get_claim.assert_awaited_once_with(owner_id="tenant-1", claim_id="claim-missing")


@pytest.mark.asyncio
async def test_generate_dossier_baseline_clean_claim(
    dossier_service_instance,
    mock_claim_srv,
    mock_document_repo,
    mock_intelligence_srv,
    mock_fraud_srv,
):
    mock_claim_srv.get_claim.return_value = ClaimResponse(
        id="claim-100",
        owner_id="tenant-1",
        title="Fender Bender Claim",
        claim_type="AUTO",
        claim_number="CLM-100",
        policy_number="POL-555",
        description="Minor scrape in parking lot",
        status="OPEN",
        created_at="2026-10-10T09:00:00Z",
        updated_at="2026-10-10T09:00:00Z",
    )
    mock_document_repo.list_documents_for_claim.return_value = [
        {
            "id": "doc-1",
            "original_filename": "photo_scratch.jpg",
            "document_type": "DAMAGE_PHOTO",
            "status": "COMPLETED",
            "size_bytes": 1048576,
            "uploaded_at": "2026-10-10T09:30:00Z",
        }
    ]
    mock_intelligence_srv.get_claim_analysis.return_value = None
    mock_fraud_srv.get_claim_network.return_value = ClaimFraudNetworkResponse(
        claim_id="claim-100",
        nodes=[],
        edges=[],
        fraud_rings=[],
        node_count=0,
        edge_count=0,
    )

    dossier = await dossier_service_instance.generate_dossier(owner_id="tenant-1", claim_id="claim-100")

    assert isinstance(dossier, ForensicDossierV1)
    assert dossier.claim_id == "claim-100"
    assert dossier.owner_id == "tenant-1"
    assert dossier.overall_risk_score == 0.0
    assert dossier.fraud_classification == "LOW_RISK_STANDARD"
    assert len(dossier.documents_summary) == 1
    assert dossier.documents_summary[0].original_filename == "photo_scratch.jpg"
    assert len(dossier.chronological_timeline) == 1
    assert "photo_scratch.jpg" in dossier.chronological_timeline[0].event_description
    assert len(dossier.contradictions_and_discrepancies) == 0
    assert len(dossier.associated_fraud_rings) == 0
    assert len(dossier.investigator_recommendations) == 1
    assert dossier.investigator_recommendations[0].priority == "LOW"


@pytest.mark.asyncio
async def test_generate_dossier_high_risk_collusion_and_discrepancies(
    dossier_service_instance,
    mock_claim_srv,
    mock_document_repo,
    mock_intelligence_srv,
    mock_fraud_srv,
):
    mock_claim_srv.get_claim.return_value = ClaimResponse(
        id="claim-200",
        owner_id="tenant-1",
        title="Multi-Vehicle Collision",
        claim_type="AUTO",
        claim_number="CLM-200",
        policy_number="POL-777",
        description="High speed intersection crash",
        status="OPEN",
        created_at="2026-10-12T12:00:00Z",
        updated_at="2026-10-12T12:00:00Z",
    )
    mock_document_repo.list_documents_for_claim.return_value = [
        {
            "id": "doc-a",
            "original_filename": "police_report.pdf",
            "document_type": "POLICE_REPORT",
            "status": "COMPLETED",
            "size_bytes": 20480,
            "uploaded_at": "2026-10-12T13:00:00Z",
        },
        {
            "id": "doc-b",
            "original_filename": "medical_bill.pdf",
            "document_type": "MEDICAL_BILL",
            "status": "COMPLETED",
            "size_bytes": 15360,
            "uploaded_at": "2026-10-12T14:00:00Z",
        },
    ]

    mock_intelligence_srv.get_claim_analysis.return_value = ClaimIntelligenceAnalysisV1(
        claim_id="claim-200",
        overall_risk_score=0.82,
        executive_summary="Critical contradictions found between police report and clinic billing dates.",
        timeline=[
            TimelineEvent(
                date="2026-09-01",
                event_description="Accident reported on Highway 101",
                document_id="doc-a",
            ),
            TimelineEvent(
                date="2026-09-05",
                event_description="Physiotherapy billed retroactively",
                document_id="doc-b",
            ),
        ],
        discrepancies=[
            ClaimDiscrepancy(
                id="disc-99",
                title="Service date precedes collision",
                description="Clinic invoice bills treatment prior to accident date.",
                category=DiscrepancyCategory.DATE_INCONSISTENCY,
                severity=DiscrepancySeverity.CRITICAL,
                confidence=0.98,
                citations=[
                    DocumentCitation(
                        document_id="doc-b",
                        quoted_statement="Date of Service: 2026-08-28",
                    )
                ],
                recommended_action="Contact medical provider for original ledger",
            )
        ],
        unresolved_questions=["Why does treatment predate the collision?"],
    )

    mock_fraud_srv.get_claim_network.return_value = ClaimFraudNetworkResponse(
        claim_id="claim-200",
        nodes=[
            FraudRingNode(id="claim-200", label="Claim 200", type="claim"),
            FraudRingNode(id="prov-1", label="Dr. Scam Clinic", type="organization"),
        ],
        edges=[
            FraudRingEdge(source="claim-200", target="prov-1", type="INVOLVES_ORGANIZATION"),
        ],
        fraud_rings=[
            FraudRingAnalysisV1(
                ring_id="ring-888",
                pattern=FraudRingPattern.PROVIDER_FRAUD_COLLUSION,
                severity=FraudRingSeverity.CRITICAL,
                risk_score=0.92,
                title="Metro Clinic Collusion Ring",
                summary="Clinic systematically submits fraudulent invoices across 4 claims.",
                claim_ids=["claim-200", "claim-101", "claim-102"],
                shared_entities=[
                    SharedEntitySummary(
                        name="Dr. Scam Clinic",
                        entity_type="organization",
                        claim_count=3,
                    )
                ],
                suspicious_indicators=["Recurring billing codes for non-existent injuries"],
                recommended_siu_actions=["Issue immediate SIU subpoena for clinic records"],
            )
        ],
        node_count=2,
        edge_count=1,
    )

    dossier = await dossier_service_instance.generate_dossier(owner_id="tenant-1", claim_id="claim-200")

    assert dossier.overall_risk_score == 0.92
    assert dossier.fraud_classification == "CRITICAL_COLLUSION_RING"
    assert len(dossier.documents_summary) == 2
    assert len(dossier.chronological_timeline) == 2
    assert len(dossier.contradictions_and_discrepancies) == 1
    assert len(dossier.associated_fraud_rings) == 1
    assert dossier.network_subgraph["node_count"] == 2

    # Check recommendations prioritized
    actions = [r.action for r in dossier.investigator_recommendations]
    assert "Issue immediate SIU subpoena for clinic records" in actions
    assert "Contact medical provider for original ledger" in actions


@pytest.mark.asyncio
async def test_render_markdown_and_html(dossier_service_instance, mock_claim_srv, mock_document_repo, mock_intelligence_srv, mock_fraud_srv):
    mock_claim_srv.get_claim.return_value = ClaimResponse(
        id="claim-300",
        owner_id="tenant-1",
        title="Comprehensive Claim",
        claim_type="AUTO",
        claim_number="CLM-300",
        policy_number="POL-300",
        description="Comprehensive vehicle loss",
        status="OPEN",
        created_at="2026-10-15T08:00:00Z",
        updated_at="2026-10-15T08:00:00Z",
    )
    mock_document_repo.list_documents_for_claim.return_value = []
    mock_intelligence_srv.get_claim_analysis.return_value = None
    mock_fraud_srv.get_claim_network.return_value = ClaimFraudNetworkResponse(
        claim_id="claim-300",
        nodes=[],
        edges=[],
        fraud_rings=[],
        node_count=0,
        edge_count=0,
    )

    dossier = await dossier_service_instance.generate_dossier(owner_id="tenant-1", claim_id="claim-300")

    # Render Markdown
    md = dossier_service_instance.render_markdown(dossier)
    assert "# FORENSIC SIU INVESTIGATION DOSSIER" in md
    assert "claim-300" in md
    assert "Executive Summary" in md
    assert "Claim & Policy Metadata" in md
    assert "Evidentiary Documents Summary" in md
    assert "Chronological Incident & Claim Timeline" in md

    # Render HTML
    html_doc = dossier_service_instance.render_html(dossier)
    assert "<!DOCTYPE html>" in html_doc
    assert "SIU Forensic Dossier - claim-300" in html_doc
    assert "Executive Summary" in html_doc
    assert "@media print" in html_doc


@pytest.mark.asyncio
async def test_export_dossier_formats(dossier_service_instance, mock_claim_srv, mock_document_repo, mock_intelligence_srv, mock_fraud_srv):
    mock_claim_srv.get_claim.return_value = ClaimResponse(
        id="claim-400",
        owner_id="tenant-1",
        title="Export Test Claim",
        claim_type="AUTO",
        description="Export test claim description",
        status="OPEN",
        created_at="2026-10-15T08:00:00Z",
        updated_at="2026-10-15T08:00:00Z",
    )
    mock_document_repo.list_documents_for_claim.return_value = []
    mock_intelligence_srv.get_claim_analysis.return_value = None
    mock_fraud_srv.get_claim_network.return_value = ClaimFraudNetworkResponse(
        claim_id="claim-400",
        nodes=[],
        edges=[],
        fraud_rings=[],
        node_count=0,
        edge_count=0,
    )

    # 1. JSON Export
    json_resp = await dossier_service_instance.export_dossier(
        owner_id="tenant-1", claim_id="claim-400", format=DossierExportFormat.JSON
    )
    assert json_resp.format == DossierExportFormat.JSON
    assert json_resp.content_type == "application/json"
    assert json_resp.filename == "dossier_claim-400.json"
    assert '"claim_id": "claim-400"' in json_resp.content

    # 2. Markdown Export
    md_resp = await dossier_service_instance.export_dossier(
        owner_id="tenant-1", claim_id="claim-400", format=DossierExportFormat.MARKDOWN
    )
    assert md_resp.format == DossierExportFormat.MARKDOWN
    assert md_resp.content_type == "text/markdown; charset=utf-8"
    assert md_resp.filename == "dossier_claim-400.md"
    assert "# FORENSIC SIU INVESTIGATION DOSSIER" in md_resp.content

    # 3. HTML Export
    html_resp = await dossier_service_instance.export_dossier(
        owner_id="tenant-1", claim_id="claim-400", format=DossierExportFormat.HTML
    )
    assert html_resp.format == DossierExportFormat.HTML
    assert html_resp.content_type == "text/html; charset=utf-8"
    assert html_resp.filename == "dossier_claim-400.html"
    assert "<!DOCTYPE html>" in html_resp.content
