import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.config import settings
from app.graph.claim_repo import ClaimRepository
from app.graph.document_repo import DocumentRepository
from app.graph.entity_repo import EntityRepository
from app.inference.claim_analysis_schemas import ClaimIntelligenceAnalysisV1
from app.inference.client import NebiusTokenFactoryClient
from app.services.claim_intelligence_service import ClaimIntelligenceService, ClaimNotFoundError
from app.services.extraction_service import DocumentExtractionService


@pytest.fixture
def mock_claim_repo():
    repo = MagicMock(spec=ClaimRepository)
    repo.get_claim.return_value = {
        "id": "claim-1",
        "owner_id": "owner-1",
        "title": "Intersection Crash",
        "policy_number": "POL-1001",
        "status": "OPEN",
    }
    repo.update_claim_analysis.return_value = True
    return repo


@pytest.fixture
def mock_doc_repo():
    repo = MagicMock(spec=DocumentRepository)
    repo.list_documents_for_claim.return_value = [
        {
            "id": "doc-1",
            "original_filename": "police_report.pdf",
            "document_type": "police_report",
            "status": "COMPLETED",
            "extraction_json": json.dumps({
                "summary": "Vehicle accident on 2024-04-10.",
                "dates": [{"value": "2024-04-10", "context": "incident date"}],
                "parties": [{"name": "Officer Miller", "role": "officer"}],
                "amounts": [],
                "key_facts": ["Rear-end collision."],
            }),
        },
        {
            "id": "doc-2",
            "original_filename": "repair_bill.pdf",
            "document_type": "repair_estimate",
            "status": "COMPLETED",
            "extraction_json": json.dumps({
                "summary": "Auto repair invoice.",
                "dates": [{"value": "2024-04-09", "context": "repair start date"}],
                "parties": [{"name": "Metro Body Shop", "role": "repairer"}],
                "amounts": [{"amount": 3200.0, "currency": "USD"}],
                "key_facts": ["Front bumper damage."],
            }),
        },
    ]
    return repo


@pytest.fixture
def mock_entity_repo():
    repo = MagicMock(spec=EntityRepository)
    repo.upsert_person.return_value = {"id": "p-1"}
    repo.upsert_organization.return_value = {"id": "org-1"}
    return repo


@pytest.fixture
def mock_llm_client():
    client = MagicMock(spec=NebiusTokenFactoryClient)
    return client


@pytest.mark.asyncio
async def test_analyze_claim_success(
    monkeypatch: pytest.MonkeyPatch,
    mock_claim_repo,
    mock_doc_repo,
    mock_entity_repo,
    mock_llm_client,
):
    monkeypatch.setattr(settings, "INFERENCE_ENABLED", True)

    llm_output = json.dumps({
        "claim_id": "claim-1",
        "overall_risk_score": 0.65,
        "executive_summary": "Discrepancy detected: Repair bill predates incident date.",
        "timeline": [
            {
                "date": "2024-04-09",
                "event_description": "Vehicle admitted to repair shop.",
                "document_id": "doc-2",
            },
            {
                "date": "2024-04-10",
                "event_description": "Accident occurred.",
                "document_id": "doc-1",
            },
        ],
        "discrepancies": [
            {
                "id": "disc-1",
                "title": "Repair Predates Collision",
                "description": "Repair started on 2024-04-09 before incident on 2024-04-10.",
                "category": "date_inconsistency",
                "severity": "high",
                "confidence": 0.95,
                "citations": [
                    {
                        "document_id": "doc-1",
                        "document_name": "police_report.pdf",
                        "quoted_statement": "Date of incident: 2024-04-10",
                    },
                    {
                        "document_id": "doc-2",
                        "document_name": "repair_bill.pdf",
                        "quoted_statement": "Vehicle admitted: 2024-04-09",
                    },
                ],
                "recommended_action": "Verify invoice date with body shop.",
            }
        ],
        "unresolved_questions": ["Why was repair started before crash?"],
        "confidence_score": 0.92,
    })

    mock_llm_client.chat_completion = AsyncMock(
        return_value={"choices": [{"message": {"content": llm_output}}]}
    )

    mock_extraction_service = MagicMock(spec=DocumentExtractionService)

    service = ClaimIntelligenceService(
        claim_repo=mock_claim_repo,
        document_repo=mock_doc_repo,
        entity_repository=mock_entity_repo,
        extraction_srv=mock_extraction_service,
        client=mock_llm_client,
    )

    result = await service.analyze_claim(owner_id="owner-1", claim_id="claim-1")

    assert isinstance(result, ClaimIntelligenceAnalysisV1)
    assert result.claim_id == "claim-1"
    assert result.overall_risk_score == 0.65
    assert len(result.discrepancies) == 1
    assert result.discrepancies[0].severity == "high"

    # Verify entity linking was triggered
    mock_entity_repo.upsert_person.assert_called_once_with(
        owner_id="owner-1",
        claim_id="claim-1",
        name="Officer Miller",
        role="officer",
        document_id="doc-1",
    )
    mock_entity_repo.upsert_organization.assert_called_once_with(
        owner_id="owner-1",
        claim_id="claim-1",
        name="Metro Body Shop",
        org_type="repairer",
        document_id="doc-2",
    )

    # Verify claim node updated
    mock_claim_repo.update_claim_analysis.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_claim_not_found(mock_claim_repo, mock_doc_repo, mock_entity_repo, mock_llm_client):
    mock_claim_repo.get_claim.return_value = None

    service = ClaimIntelligenceService(
        claim_repo=mock_claim_repo,
        document_repo=mock_doc_repo,
        entity_repository=mock_entity_repo,
        client=mock_llm_client,
    )

    with pytest.raises(ClaimNotFoundError):
        await service.analyze_claim(owner_id="foreign-owner", claim_id="claim-1")


@pytest.mark.asyncio
async def test_analyze_claim_zero_documents(mock_claim_repo, mock_doc_repo, mock_entity_repo, mock_llm_client):
    mock_doc_repo.list_documents_for_claim.return_value = []

    service = ClaimIntelligenceService(
        claim_repo=mock_claim_repo,
        document_repo=mock_doc_repo,
        entity_repository=mock_entity_repo,
        client=mock_llm_client,
    )

    result = await service.analyze_claim(owner_id="owner-1", claim_id="claim-1")

    assert result.overall_risk_score == 0.0
    assert "No active documents" in result.executive_summary
    # Zero LLM inference calls made
    mock_llm_client.chat_completion.assert_not_called()
    mock_claim_repo.update_claim_analysis.assert_called_once()


def test_get_claim_analysis_cached(mock_claim_repo, mock_doc_repo, mock_entity_repo, mock_llm_client):
    cached_data = {
        "claim_id": "claim-1",
        "overall_risk_score": 0.2,
        "executive_summary": "Cached report.",
        "timeline": [],
        "discrepancies": [],
        "unresolved_questions": [],
        "confidence_score": 1.0,
    }
    mock_claim_repo.get_claim.return_value = {
        "id": "claim-1",
        "owner_id": "owner-1",
        "analysis_json": json.dumps(cached_data),
    }

    service = ClaimIntelligenceService(
        claim_repo=mock_claim_repo,
        document_repo=mock_doc_repo,
        entity_repository=mock_entity_repo,
        client=mock_llm_client,
    )

    cached = service.get_claim_analysis(owner_id="owner-1", claim_id="claim-1")
    assert cached is not None
    assert cached.executive_summary == "Cached report."
