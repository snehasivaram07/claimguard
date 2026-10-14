import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient

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


@pytest.fixture(autouse=True)
def setup_in_memory_claim_repo(monkeypatch):
    test_repo = InMemoryClaimRepo()
    monkeypatch.setattr(claim_service, "_claim_repo", test_repo)
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
