import pytest
from httpx import AsyncClient

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
from app.services.claim_service import claim_service
from app.services.dossier_service import dossier_service
from tests.test_claims import InMemoryClaimRepo, get_auth_token


@pytest.fixture(autouse=True)
def setup_claim_repo(monkeypatch):
    test_repo = InMemoryClaimRepo()
    monkeypatch.setattr(claim_service, "_claim_repo", test_repo)
    return test_repo


def _make_mock_dossier(claim_id: str, owner_id: str) -> ForensicDossierV1:
    return ForensicDossierV1(
        dossier_id=f"dossier-{claim_id}",
        claim_id=claim_id,
        owner_id=owner_id,
        generated_at="2026-10-16T12:00:00Z",
        overall_risk_score=0.85,
        fraud_classification="HIGH_RISK_COLLUSION",
        executive_summary="Forensic evaluation indicates high risk of staged collision network involvement.",
        claim_metadata=DossierClaimMetadata(
            claim_id=claim_id,
            title="Highway Collision Claim",
            claim_number="CLM-700",
            policy_number="POL-700",
            status="OPEN",
            description="Vehicle accident",
        ),
        documents_summary=[
            DossierDocumentSummary(
                document_id="doc-1",
                original_filename="police_report.pdf",
                document_type="POLICE_REPORT",
                status="COMPLETED",
                size_bytes=10240,
            )
        ],
        chronological_timeline=[
            DossierTimelineEvent(
                date="2026-09-10",
                event_description="Accident reported to highway patrol",
                document_id="doc-1",
            )
        ],
        contradictions_and_discrepancies=[
            DossierDiscrepancyItem(
                id="disc-1",
                title="Date conflict",
                description="Loss date mismatch",
                category="date_inconsistency",
                severity="high",
                confidence=0.92,
            )
        ],
        associated_fraud_rings=[
            DossierFraudRingItem(
                ring_id="ring-1",
                pattern="staged_collision_ring",
                severity="critical",
                risk_score=0.89,
                title="Staged Crash Ring",
                summary="Shared clinic and tow service across 3 claims",
            )
        ],
        investigator_recommendations=[
            DossierRecommendationItem(
                priority="HIGH",
                category="COLLUSION_INVESTIGATION",
                action="Subpoena clinic records",
                rationale="Excessive physical therapy invoices",
            )
        ],
        unresolved_questions=["Why was loss reported 10 days post accident?"],
    )


@pytest.mark.asyncio
async def test_get_claim_dossier_happy_path(async_client: AsyncClient, monkeypatch):
    token = await get_auth_token(async_client, "siu_officer@claimguard.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a claim
    create_resp = await async_client.post(
        "/claims",
        headers=headers,
        json={"title": "Highway Collision Claim", "policy_number": "POL-700"},
    )
    assert create_resp.status_code == 201
    claim_id = create_resp.json()["id"]

    # 2. Mock dossier_service.generate_dossier
    async def mock_generate(owner_id: str, claim_id: str):
        assert owner_id is not None
        assert claim_id is not None
        return _make_mock_dossier(claim_id=claim_id, owner_id=owner_id)

    monkeypatch.setattr(dossier_service, "generate_dossier", mock_generate)

    # 3. Retrieve dossier
    resp = await async_client.get(f"/claims/{claim_id}/dossier", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["claim_id"] == claim_id
    assert data["dossier_id"] == f"dossier-{claim_id}"
    assert data["overall_risk_score"] == 0.85
    assert data["fraud_classification"] == "HIGH_RISK_COLLUSION"
    assert len(data["documents_summary"]) == 1
    assert len(data["contradictions_and_discrepancies"]) == 1
    assert len(data["associated_fraud_rings"]) == 1
    assert len(data["investigator_recommendations"]) == 1

    # 4. Verify audit trail event DOSSIER_GENERATED
    audit_resp = await async_client.get(f"/claims/{claim_id}/audit", headers=headers)
    assert audit_resp.status_code == 200
    events = audit_resp.json()["items"]
    actions = [e["action"] for e in events]
    assert "DOSSIER_GENERATED" in actions

    event = next(e for e in events if e["action"] == "DOSSIER_GENERATED")
    meta = event["event_metadata"]
    assert meta["claim_id"] == claim_id
    assert meta["overall_risk_score"] == 0.85
    assert meta["fraud_classification"] == "HIGH_RISK_COLLUSION"
    assert meta["documents_count"] == 1
    assert meta["discrepancies_count"] == 1
    assert meta["fraud_rings_count"] == 1


@pytest.mark.asyncio
async def test_get_claim_dossier_404_existence_masking(async_client: AsyncClient):
    token_a = await get_auth_token(async_client, "owner_a@claimguard.com")
    token_b = await get_auth_token(async_client, "owner_b@claimguard.com")

    # User A creates a claim
    create_resp = await async_client.post(
        "/claims",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"title": "Confidential SIU Target Claim"},
    )
    claim_id = create_resp.json()["id"]

    # User B attempts to access User A's dossier -> strictly 404, never 403
    resp = await async_client.get(
        f"/claims/{claim_id}/dossier",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_export_claim_dossier_json(async_client: AsyncClient, monkeypatch):
    token = await get_auth_token(async_client, "export_user@claimguard.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await async_client.post(
        "/claims",
        headers=headers,
        json={"title": "Export JSON Test Claim"},
    )
    claim_id = create_resp.json()["id"]

    async def mock_export(owner_id: str, claim_id: str, format: DossierExportFormat):
        assert owner_id is not None
        assert format == DossierExportFormat.JSON
        return DossierExportResponse(
            claim_id=claim_id,
            format=format,
            content_type="application/json",
            filename=f"dossier_{claim_id}.json",
            content='{"dossier_id": "test-json-export"}',
        )

    monkeypatch.setattr(dossier_service, "export_dossier", mock_export)

    resp = await async_client.get(f"/claims/{claim_id}/dossier/export?format=json", headers=headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/json"
    assert resp.headers["content-disposition"] == f'attachment; filename="dossier_{claim_id}.json"'
    assert '{"dossier_id": "test-json-export"}' in resp.text

    # Audit check
    audit_resp = await async_client.get(f"/claims/{claim_id}/audit", headers=headers)
    assert audit_resp.status_code == 200
    events = audit_resp.json()["items"]
    assert any(e["action"] == "DOSSIER_EXPORTED" for e in events)


@pytest.mark.asyncio
async def test_export_claim_dossier_markdown(async_client: AsyncClient, monkeypatch):
    token = await get_auth_token(async_client, "md_user@claimguard.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await async_client.post(
        "/claims",
        headers=headers,
        json={"title": "Export MD Test Claim"},
    )
    claim_id = create_resp.json()["id"]

    async def mock_export(owner_id: str, claim_id: str, format: DossierExportFormat):
        assert owner_id is not None
        assert format == DossierExportFormat.MARKDOWN
        return DossierExportResponse(
            claim_id=claim_id,
            format=format,
            content_type="text/markdown; charset=utf-8",
            filename=f"dossier_{claim_id}.md",
            content="# FORENSIC SIU INVESTIGATION DOSSIER\n\nExecutive Summary",
        )

    monkeypatch.setattr(dossier_service, "export_dossier", mock_export)

    resp = await async_client.get(f"/claims/{claim_id}/dossier/export?format=markdown", headers=headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "text/markdown; charset=utf-8"
    assert resp.headers["content-disposition"] == f'attachment; filename="dossier_{claim_id}.md"'
    assert "# FORENSIC SIU INVESTIGATION DOSSIER" in resp.text


@pytest.mark.asyncio
async def test_export_claim_dossier_html(async_client: AsyncClient, monkeypatch):
    token = await get_auth_token(async_client, "html_user@claimguard.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await async_client.post(
        "/claims",
        headers=headers,
        json={"title": "Export HTML Test Claim"},
    )
    claim_id = create_resp.json()["id"]

    async def mock_export(owner_id: str, claim_id: str, format: DossierExportFormat):
        assert owner_id is not None
        assert format == DossierExportFormat.HTML
        return DossierExportResponse(
            claim_id=claim_id,
            format=format,
            content_type="text/html; charset=utf-8",
            filename=f"dossier_{claim_id}.html",
            content="<!DOCTYPE html><html><body><h1>SIU Forensic Dossier</h1></body></html>",
        )

    monkeypatch.setattr(dossier_service, "export_dossier", mock_export)

    resp = await async_client.get(f"/claims/{claim_id}/dossier/export?format=html", headers=headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "text/html; charset=utf-8"
    assert resp.headers["content-disposition"] == f'attachment; filename="dossier_{claim_id}.html"'
    assert "SIU Forensic Dossier" in resp.text


@pytest.mark.asyncio
async def test_export_claim_dossier_invalid_format_returns_422(async_client: AsyncClient):
    token = await get_auth_token(async_client, "invalid_fmt@claimguard.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await async_client.post(
        "/claims",
        headers=headers,
        json={"title": "Invalid Format Test Claim"},
    )
    claim_id = create_resp.json()["id"]

    resp = await async_client.get(f"/claims/{claim_id}/dossier/export?format=unsupported", headers=headers)
    assert resp.status_code == 422
