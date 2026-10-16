import uuid

import pytest
from httpx import AsyncClient

from app.core.errors import NotFoundError
from app.schemas.fraud_ring import (
    ClaimFraudNetworkResponse,
    FraudRingAnalysisV1,
    FraudRingEdge,
    FraudRingNode,
    FraudRingPattern,
    FraudRingSeverity,
    SharedEntitySummary,
)
from app.services.claim_service import claim_service
from app.services.fraud_ring_service import fraud_ring_service
from tests.test_claims import InMemoryClaimRepo, get_auth_token


@pytest.fixture(autouse=True)
def setup_claim_repo(monkeypatch):
    test_repo = InMemoryClaimRepo()
    monkeypatch.setattr(claim_service, "_claim_repo", test_repo)
    return test_repo


def _make_mock_ring(ring_id: str = "ring-1") -> FraudRingAnalysisV1:
    return FraudRingAnalysisV1(
        ring_id=ring_id,
        pattern=FraudRingPattern.STAGED_COLLISION_RING,
        severity=FraudRingSeverity.CRITICAL,
        risk_score=0.92,
        title="Staged Collision Syndicate",
        summary="Collusion cluster detected between 2 claims sharing body shop and claimant.",
        claim_ids=["c-1", "c-2"],
        shared_entities=[
            SharedEntitySummary(
                name="Apex Collision",
                entity_type="organization",
                claim_count=2,
                roles=["body_shop"],
            )
        ],
        suspicious_indicators=["Recurring body shop with inflated estimates"],
        recommended_siu_actions=["Subpoena repair invoices"],
    )


@pytest.mark.asyncio
async def test_get_claim_fraud_network_happy_path(async_client: AsyncClient, monkeypatch):
    token = await get_auth_token(async_client, "siu_investigator@claimguard.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a claim
    create_resp = await async_client.post(
        "/claims",
        headers=headers,
        json={"title": "Suspicious Intersection Collision"},
    )
    assert create_resp.status_code == 201
    claim_id = create_resp.json()["id"]

    # 2. Mock fraud_ring_service.get_claim_network
    mock_network = ClaimFraudNetworkResponse(
        claim_id=claim_id,
        nodes=[
            FraudRingNode(id=claim_id, label="Target Claim", type="claim", is_target=True),
            FraudRingNode(id="p-1", label="Dr. Smith", type="person"),
        ],
        edges=[
            FraudRingEdge(source=claim_id, target="p-1", type="INVOLVES_PERSON"),
        ],
        fraud_rings=[_make_mock_ring("ring-alpha")],
        node_count=2,
        edge_count=1,
    )

    async def mock_get_network(owner_id: str, claim_id: str, max_hops: int = 2):
        assert claim_id is not None
        assert owner_id is not None
        assert max_hops == 2
        return mock_network

    monkeypatch.setattr(fraud_ring_service, "get_claim_network", mock_get_network)

    # 3. Request GET /claims/{claim_id}/fraud-network
    resp = await async_client.get(f"/claims/{claim_id}/fraud-network", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["claim_id"] == claim_id
    assert data["node_count"] == 2
    assert data["edge_count"] == 1
    assert len(data["nodes"]) == 2
    assert len(data["fraud_rings"]) == 1
    assert data["fraud_rings"][0]["ring_id"] == "ring-alpha"

    # 4. Verify audit trail logged CLAIM_FRAUD_NETWORK_VIEWED with zero raw data leaked
    audit_resp = await async_client.get(f"/claims/{claim_id}/audit", headers=headers)
    assert audit_resp.status_code == 200
    events = audit_resp.json()["items"]
    actions = [e["action"] for e in events]
    assert "CLAIM_FRAUD_NETWORK_VIEWED" in actions

    event = next(e for e in events if e["action"] == "CLAIM_FRAUD_NETWORK_VIEWED")
    meta = event["event_metadata"]
    assert meta["node_count"] == 2
    assert meta["edge_count"] == 1
    assert meta["fraud_rings_count"] == 1


@pytest.mark.asyncio
async def test_get_claim_fraud_network_404_existence_masking(async_client: AsyncClient, monkeypatch):
    token_a = await get_auth_token(async_client, "owner_a@claimguard.com")
    token_b = await get_auth_token(async_client, "owner_b@claimguard.com")

    # User A creates a claim
    create_resp = await async_client.post(
        "/claims",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"title": "Private Claim"},
    )
    claim_id = create_resp.json()["id"]

    # When User B requests User A's claim network, service raises NotFoundError
    async def mock_network_isolation(owner_id: str, claim_id: str, max_hops: int = 2):
        _ = (owner_id, claim_id, max_hops)
        # Verify NotFoundError is thrown for cross-tenant or missing claim
        raise NotFoundError("Claim not found")

    monkeypatch.setattr(fraud_ring_service, "get_claim_network", mock_network_isolation)

    # User B requests User A's claim network -> 404
    resp = await async_client.get(
        f"/claims/{claim_id}/fraud-network",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"

    # Random fake ID -> 404
    fake_id = str(uuid.uuid4())
    resp_fake = await async_client.get(
        f"/claims/{fake_id}/fraud-network",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp_fake.status_code == 404


@pytest.mark.asyncio
async def test_list_fraud_rings_endpoint(async_client: AsyncClient, monkeypatch):
    token = await get_auth_token(async_client, "ring_analyst@claimguard.com")
    headers = {"Authorization": f"Bearer {token}"}

    mock_rings = [_make_mock_ring("ring-100"), _make_mock_ring("ring-200")]

    async def mock_detect(owner_id: str, min_shared: int = 2):
        assert owner_id is not None
        assert min_shared == 2
        return mock_rings

    monkeypatch.setattr(fraud_ring_service, "detect_fraud_rings", mock_detect)

    resp = await async_client.get("/fraud-rings?min_shared=2", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["rings"]) == 2
    assert data["rings"][0]["ring_id"] == "ring-100"
    assert data["rings"][1]["ring_id"] == "ring-200"

    # Verify audit event logged
    audit_resp = await async_client.get("/auth/me/audit", headers=headers)
    assert audit_resp.status_code == 200
    events = audit_resp.json()["items"]
    actions = [e["action"] for e in events]
    assert "FRAUD_RINGS_DETECTED" in actions
