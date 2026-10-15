import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient

from app.core.errors import BadRequestError
from app.inference.claim_analysis_schemas import (
    ClaimDiscrepancy,
    ClaimIntelligenceAnalysisV1,
    DiscrepancyCategory,
    DiscrepancySeverity,
    DocumentCitation,
    TimelineEvent,
)
from app.services.claim_intelligence_service import claim_intelligence_service
from app.services.claim_service import claim_service


class InMemoryClaimRepo:
    """In-memory simulation of ClaimRepository enforcing strict owner isolation."""

    def __init__(self):
        self.claims = {}

    def create_claim(self, owner_id: str, claim_data: dict) -> dict:
        now = datetime.now(UTC).isoformat()
        claim_id = claim_data.get("id") or str(uuid.uuid4())
        record = {
            "id": claim_id,
            "owner_id": owner_id,
            "title": claim_data.get("title", ""),
            "claim_type": claim_data.get("claim_type", "GENERAL"),
            "claim_number": claim_data.get("claim_number"),
            "policy_number": claim_data.get("policy_number"),
            "description": claim_data.get("description", ""),
            "status": claim_data.get("status", "OPEN"),
            "created_at": now,
            "updated_at": now,
            "schema_version": 1,
        }
        self.claims[claim_id] = record
        return record

    def get_claim(self, owner_id: str, claim_id: str) -> dict | None:
        record = self.claims.get(claim_id)
        if record and record["owner_id"] == owner_id:
            return record
        return None

    def list_claims(
        self,
        owner_id: str,
        skip: int = 0,
        limit: int = 50,
        include_archived: bool = False,
    ) -> list[dict]:
        user_claims = [
            c for c in self.claims.values()
            if c["owner_id"] == owner_id and (include_archived or c["status"] != "ARCHIVED")
        ]
        user_claims.sort(key=lambda x: x["created_at"], reverse=True)
        return user_claims[skip : skip + limit]

    def count_claims(self, owner_id: str, include_archived: bool = False) -> int:
        return len(self.list_claims(owner_id, 0, 10000, include_archived))

    def update_claim(self, owner_id: str, claim_id: str, updates: dict) -> dict | None:
        record = self.get_claim(owner_id, claim_id)
        if not record:
            return None
        for k, v in updates.items():
            if k not in ("id", "owner_id", "created_at", "schema_version"):
                record[k] = v
        record["updated_at"] = datetime.now(UTC).isoformat()
        return record

    def soft_delete_claim(self, owner_id: str, claim_id: str) -> bool:
        record = self.get_claim(owner_id, claim_id)
        if not record:
            return False
        record["status"] = "ARCHIVED"
        record["updated_at"] = datetime.now(UTC).isoformat()
        return True

    def update_claim_analysis(
        self,
        owner_id: str,
        claim_id: str,
        analysis_json: str,
        risk_score: float,
    ) -> bool:
        record = self.get_claim(owner_id, claim_id)
        if not record:
            return False
        record["analysis_json"] = analysis_json
        record["risk_score"] = risk_score
        return True


@pytest.fixture(autouse=True)
def setup_in_memory_claim_repo(monkeypatch):
    test_repo = InMemoryClaimRepo()
    monkeypatch.setattr(claim_service, "_claim_repo", test_repo)
    monkeypatch.setattr(claim_intelligence_service, "_claim_repo", test_repo)
    return test_repo


async def get_auth_token(async_client: AsyncClient, email: str) -> str:
    await async_client.post(
        "/auth/register",
        json={"email": email, "password": "password12345"},
    )
    login_resp = await async_client.post(
        "/auth/login",
        json={"email": email, "password": "password12345"},
    )
    return login_resp.json()["access_token"]


@pytest.mark.asyncio
async def test_claim_lifecycle_happy_path(async_client: AsyncClient):
    token = await get_auth_token(async_client, "user_a@claimguard.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create claim
    create_resp = await async_client.post(
        "/claims",
        headers=headers,
        json={
            "title": "Water Damage in Kitchen",
            "claim_type": "PROPERTY",
            "claim_number": "CLM-2026-001",
            "policy_number": "POL-999",
            "description": "Burst pipe under kitchen sink",
        },
    )
    assert create_resp.status_code == 201
    created_claim = create_resp.json()
    assert created_claim["title"] == "Water Damage in Kitchen"
    assert created_claim["status"] == "OPEN"
    claim_id = created_claim["id"]

    # 2. Get claim
    get_resp = await async_client.get(f"/claims/{claim_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == claim_id

    # 3. Update claim
    update_resp = await async_client.patch(
        f"/claims/{claim_id}",
        headers=headers,
        json={"title": "Major Water Damage in Kitchen", "status": "CLOSED"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "Major Water Damage in Kitchen"
    assert update_resp.json()["status"] == "CLOSED"

    # 4. Soft-delete claim
    delete_resp = await async_client.delete(f"/claims/{claim_id}", headers=headers)
    assert delete_resp.status_code == 200

    # 5. Verify claim is excluded from default list
    list_resp = await async_client.get("/claims", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()["items"]) == 0

    # 6. Verify claim is included when include_archived=True
    archived_list_resp = await async_client.get("/claims?include_archived=true", headers=headers)
    assert archived_list_resp.status_code == 200
    assert len(archived_list_resp.json()["items"]) == 1
    assert archived_list_resp.json()["items"][0]["status"] == "ARCHIVED"


@pytest.mark.asyncio
async def test_tenant_isolation_foreign_claim_returns_404(async_client: AsyncClient):
    token_a = await get_auth_token(async_client, "owner_a@claimguard.com")
    token_b = await get_auth_token(async_client, "owner_b@claimguard.com")

    # User A creates a claim
    create_resp = await async_client.post(
        "/claims",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"title": "Confidential Commercial Claim"},
    )
    claim_id = create_resp.json()["id"]

    # User B lists claims -> must NOT see User A's claim
    list_resp = await async_client.get("/claims", headers={"Authorization": f"Bearer {token_b}"})
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 0

    # User B queries User A's claim ID -> MUST return 404 (NOT 403 to avoid leaking existence)
    get_resp = await async_client.get(
        f"/claims/{claim_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert get_resp.status_code == 404
    assert get_resp.json()["error"]["code"] == "NOT_FOUND"

    # User B tries to update User A's claim -> 404
    patch_resp = await async_client.patch(
        f"/claims/{claim_id}",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"title": "Hacked Title"},
    )
    assert patch_resp.status_code == 404

    # User B tries to delete User A's claim -> 404
    del_resp = await async_client.delete(
        f"/claims/{claim_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert del_resp.status_code == 404


def test_find_candidate_claims_stub():
    candidates = claim_service.find_candidate_claims("user-1", "Sample document text")
    assert candidates == []


def _make_mock_analysis(claim_id: str) -> ClaimIntelligenceAnalysisV1:
    return ClaimIntelligenceAnalysisV1(
        claim_id=claim_id,
        overall_risk_score=0.85,
        confidence_score=0.92,
        executive_summary="Multiple contradictions found between police report and repair estimate.",
        timeline=[
            TimelineEvent(
                date="2026-03-01T14:30:00",
                event_description="Collision at intersection",
                document_id="doc-1",
                source_context="Police report stated 2:30 PM",
            )
        ],
        discrepancies=[
            ClaimDiscrepancy(
                id="disc-1",
                title="Date Discrepancy",
                description="Date mismatch between police report and repair invoice",
                category=DiscrepancyCategory.DATE_INCONSISTENCY,
                severity=DiscrepancySeverity.CRITICAL,
                confidence=0.95,
                citations=[
                    DocumentCitation(
                        document_id="doc-1",
                        quoted_statement="2026-03-01",
                    )
                ],
            )
        ],
        unresolved_questions=["Why does invoice date precede accident date?"],
    )


@pytest.mark.asyncio
async def test_analyze_claim_endpoint_happy_path(async_client: AsyncClient, monkeypatch):
    token = await get_auth_token(async_client, "analyst_user@claimguard.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a claim
    create_resp = await async_client.post(
        "/claims",
        headers=headers,
        json={"title": "Multi-doc Claim for Intelligence Analysis"},
    )
    assert create_resp.status_code == 201
    claim_id = create_resp.json()["id"]

    # 2. Mock claim_intelligence_service.analyze_claim
    mock_analysis = _make_mock_analysis(claim_id)
    async def mock_analyze(owner_id: str, claim_id: str):
        assert owner_id is not None
        assert claim_id is not None
        return mock_analysis

    monkeypatch.setattr(claim_intelligence_service, "analyze_claim", mock_analyze)

    # 3. Call POST /claims/{claim_id}/analyze
    resp = await async_client.post(f"/claims/{claim_id}/analyze", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["claim_id"] == claim_id
    assert data["overall_risk_score"] == 0.85
    assert data["confidence_score"] == 0.92
    assert len(data["timeline"]) == 1
    assert len(data["discrepancies"]) == 1

    # 4. Verify audit trail: CLAIM_ANALYSIS_REQUESTED & CLAIM_ANALYSIS_COMPLETED
    audit_resp = await async_client.get(f"/claims/{claim_id}/audit", headers=headers)
    assert audit_resp.status_code == 200
    events = audit_resp.json()["items"]
    actions = [e["action"] for e in events]
    assert "CLAIM_ANALYSIS_REQUESTED" in actions
    assert "CLAIM_ANALYSIS_COMPLETED" in actions

    # Verify audit event metadata contains NO raw text or prompts
    completed_event = next(e for e in events if e["action"] == "CLAIM_ANALYSIS_COMPLETED")
    meta = completed_event["event_metadata"]
    assert meta["overall_risk_score"] == 0.85
    assert meta["confidence_score"] == 0.92
    assert meta["discrepancies_count"] == 1
    assert "executive_summary" not in meta


@pytest.mark.asyncio
async def test_get_claim_intelligence_endpoint(async_client: AsyncClient, monkeypatch):
    token = await get_auth_token(async_client, "intel_user@claimguard.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await async_client.post(
        "/claims",
        headers=headers,
        json={"title": "Claim for Cached Intelligence"},
    )
    claim_id = create_resp.json()["id"]

    mock_analysis = _make_mock_analysis(claim_id)
    def mock_get(owner_id: str, claim_id: str):
        assert owner_id is not None
        assert claim_id is not None
        return mock_analysis

    monkeypatch.setattr(claim_intelligence_service, "get_claim_analysis", mock_get)

    resp = await async_client.get(f"/claims/{claim_id}/intelligence", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["claim_id"] == claim_id
    assert data["overall_risk_score"] == 0.85


@pytest.mark.asyncio
async def test_claim_analysis_404_existence_masking(async_client: AsyncClient):
    token_a = await get_auth_token(async_client, "intel_owner_a@claimguard.com")
    token_b = await get_auth_token(async_client, "intel_owner_b@claimguard.com")

    # User A creates a claim
    create_resp = await async_client.post(
        "/claims",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"title": "User A Sensitive Claim"},
    )
    claim_id = create_resp.json()["id"]

    # User B attempts to analyze User A's claim -> 404
    resp = await async_client.post(
        f"/claims/{claim_id}/analyze",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"

    # User B attempts to read User A's claim intelligence -> 404
    resp_get = await async_client.get(
        f"/claims/{claim_id}/intelligence",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp_get.status_code == 404
    assert resp_get.json()["error"]["code"] == "NOT_FOUND"

    # Random non-existent UUID -> 404
    fake_id = str(uuid.uuid4())
    resp_fake = await async_client.post(
        f"/claims/{fake_id}/analyze",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp_fake.status_code == 404


@pytest.mark.asyncio
async def test_claim_analysis_failure_audit_logging(async_client: AsyncClient, monkeypatch):
    token = await get_auth_token(async_client, "intel_fail@claimguard.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await async_client.post(
        "/claims",
        headers=headers,
        json={"title": "Failing Analysis Claim"},
    )
    claim_id = create_resp.json()["id"]

    async def mock_fail(owner_id: str, claim_id: str):
        assert owner_id is not None
        assert claim_id is not None
        raise BadRequestError("Zero extracted documents available for claim analysis")

    monkeypatch.setattr(claim_intelligence_service, "analyze_claim", mock_fail)

    resp = await async_client.post(f"/claims/{claim_id}/analyze", headers=headers)
    assert resp.status_code == 400

    # Verify CLAIM_ANALYSIS_FAILED in audit trail
    audit_resp = await async_client.get(f"/claims/{claim_id}/audit", headers=headers)
    assert audit_resp.status_code == 200
    events = audit_resp.json()["items"]
    actions = [e["action"] for e in events]
    assert "CLAIM_ANALYSIS_REQUESTED" in actions
    assert "CLAIM_ANALYSIS_FAILED" in actions

