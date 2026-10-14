import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit import AuditEvent
from app.services.audit_service import audit_service
from app.services.claim_service import claim_service
from tests.test_claims import InMemoryClaimRepo


@pytest.fixture(autouse=True)
def setup_claims_mock(monkeypatch):
    test_repo = InMemoryClaimRepo()
    monkeypatch.setattr(claim_service, "_claim_repo", test_repo)
    return test_repo


@pytest.mark.asyncio
async def test_audit_service_record_and_query(test_db_session: AsyncSession):
    # Record multiple events
    ev1 = await audit_service.record_event(
        test_db_session,
        action="TEST_ACTION_1",
        resource_type="claim",
        resource_id="clm-100",
        user_id="user-1",
        ip="127.0.0.1",
        request_id="req-1",
        outcome="SUCCESS",
        metadata={"key": "val1"},
    )
    assert isinstance(ev1, AuditEvent)
    assert ev1.event_id is not None

    await audit_service.record_event(
        test_db_session,
        action="TEST_ACTION_2",
        resource_type="claim",
        resource_id="clm-100",
        user_id="user-1",
        outcome="FAILURE",
    )

    await audit_service.record_event(
        test_db_session,
        action="TEST_ACTION_3",
        resource_type="document",
        resource_id="doc-200",
        user_id="user-2",
        outcome="SUCCESS",
    )

    # 1. Query by user
    user1_events, total = await audit_service.get_user_audit_events(test_db_session, "user-1")
    assert total == 2
    assert len(user1_events) == 2
    assert {e.action for e in user1_events} == {"TEST_ACTION_1", "TEST_ACTION_2"}

    # 2. Query by claim
    claim_events, total_claim = await audit_service.get_claim_audit_events(test_db_session, "clm-100")
    assert total_claim == 2
    assert len(claim_events) == 2

    # 3. Multi-filter query
    failure_events, total_fail = await audit_service.query_events(
        test_db_session,
        outcome="FAILURE",
    )
    assert total_fail == 1
    assert failure_events[0].action == "TEST_ACTION_2"


@pytest.mark.asyncio
async def test_me_audit_endpoint(async_client: AsyncClient):
    # Register and login to generate auth audit records
    await async_client.post(
        "/auth/register",
        json={"email": "audit_user@claimguard.com", "password": "password12345"},
    )
    login_resp = await async_client.post(
        "/auth/login",
        json={"email": "audit_user@claimguard.com", "password": "password12345"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Query personal audit trail
    audit_resp = await async_client.get("/auth/me/audit", headers=headers)
    assert audit_resp.status_code == 200
    data = audit_resp.json()
    assert "total" in data
    assert "items" in data
    assert data["total"] >= 2  # Registration + Login

    actions = [item["action"] for item in data["items"]]
    assert "LOGIN" in actions
    assert "REGISTER" in actions


@pytest.mark.asyncio
async def test_claim_audit_endpoint_and_isolation(async_client: AsyncClient):
    # User 1 registers and creates a claim
    await async_client.post(
        "/auth/register",
        json={"email": "owner_audit@claimguard.com", "password": "password12345"},
    )
    login_1 = await async_client.post(
        "/auth/login",
        json={"email": "owner_audit@claimguard.com", "password": "password12345"},
    )
    token_1 = login_1.json()["access_token"]
    headers_1 = {"Authorization": f"Bearer {token_1}"}

    claim_resp = await async_client.post(
        "/claims",
        headers=headers_1,
        json={"title": "Audited Claim"},
    )
    claim_id = claim_resp.json()["id"]

    # Owner can view audit trail
    audit_resp = await async_client.get(f"/claims/{claim_id}/audit", headers=headers_1)
    assert audit_resp.status_code == 200
    data = audit_resp.json()
    assert data["total"] >= 1
    assert data["items"][0]["action"] == "CLAIM_CREATE"
    assert data["items"][0]["resource_id"] == claim_id

    # User 2 registers and attempts to view User 1's claim audit trail
    await async_client.post(
        "/auth/register",
        json={"email": "foreign_audit@claimguard.com", "password": "password12345"},
    )
    login_2 = await async_client.post(
        "/auth/login",
        json={"email": "foreign_audit@claimguard.com", "password": "password12345"},
    )
    token_2 = login_2.json()["access_token"]
    headers_2 = {"Authorization": f"Bearer {token_2}"}

    # Must return 404 Not Found to mask existence, NOT 403
    foreign_resp = await async_client.get(f"/claims/{claim_id}/audit", headers=headers_2)
    assert foreign_resp.status_code == 404
