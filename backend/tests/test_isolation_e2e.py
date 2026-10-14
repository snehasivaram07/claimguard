import pytest
from httpx import AsyncClient

from app.services.claim_service import claim_service
from app.services.document_service import document_service
from tests.test_claims import InMemoryClaimRepo
from tests.test_documents import InMemoryDocumentRepo, MockStorageService

VALID_PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<< /Title (Sensitive Report) >>\nendobj\ntrailer\n<<>>\n%%EOF"


@pytest.fixture(autouse=True)
def setup_e2e_isolation_environment(monkeypatch):
    mock_claim_repo = InMemoryClaimRepo()
    mock_doc_repo = InMemoryDocumentRepo()
    mock_storage = MockStorageService()

    monkeypatch.setattr(claim_service, "_claim_repo", mock_claim_repo)
    monkeypatch.setattr(document_service, "_document_repo", mock_doc_repo)
    monkeypatch.setattr(document_service, "_storage", mock_storage)

    return mock_claim_repo, mock_doc_repo, mock_storage


async def register_and_login(async_client: AsyncClient, email: str, password: str = "P@ssword12345") -> str:
    await async_client.post("/auth/register", json={"email": email, "password": password})
    login_resp = await async_client.post("/auth/login", json={"email": email, "password": password})
    return login_resp.json()["access_token"]


@pytest.mark.asyncio
async def test_multi_tenant_complete_isolation_masks_all_foreign_resources(async_client: AsyncClient):
    # Setup Tenant A and Tenant B
    token_a = await register_and_login(async_client, "tenant_a@claimguard.com")
    token_b = await register_and_login(async_client, "tenant_b@claimguard.com")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. Tenant A creates Claim A
    claim_a_resp = await async_client.post(
        "/claims",
        headers=headers_a,
        json={
            "title": "Tenant A Secret Claim",
            "claim_type": "PROPERTY",
            "claim_number": "SEC-A-001",
        },
    )
    assert claim_a_resp.status_code == 201
    claim_a_id = claim_a_resp.json()["id"]

    # 2. Tenant A uploads Document A to Claim A
    doc_a_resp = await async_client.post(
        f"/claims/{claim_a_id}/documents",
        headers=headers_a,
        files={"file": ("tenant_a_doc.pdf", VALID_PDF_BYTES, "application/pdf")},
    )
    assert doc_a_resp.status_code == 201
    doc_a_id = doc_a_resp.json()["id"]

    # 3. Tenant B probes Tenant A's Claim endpoints - MUST ALL RETURN 404 (NEVER 403)
    # 3.1 Get claim
    resp = await async_client.get(f"/claims/{claim_a_id}", headers=headers_b)
    assert resp.status_code == 404
    assert resp.status_code != 403

    # 3.2 Update claim
    resp = await async_client.patch(
        f"/claims/{claim_a_id}",
        headers=headers_b,
        json={"title": "Hacked Title"},
    )
    assert resp.status_code == 404
    assert resp.status_code != 403

    # 3.3 Delete claim
    resp = await async_client.delete(f"/claims/{claim_a_id}", headers=headers_b)
    assert resp.status_code == 404
    assert resp.status_code != 403

    # 3.4 List documents of foreign claim
    resp = await async_client.get(f"/claims/{claim_a_id}/documents", headers=headers_b)
    assert resp.status_code == 404
    assert resp.status_code != 403

    # 3.5 Upload document to foreign claim
    resp = await async_client.post(
        f"/claims/{claim_a_id}/documents",
        headers=headers_b,
        files={"file": ("injected.pdf", VALID_PDF_BYTES, "application/pdf")},
    )
    assert resp.status_code == 404
    assert resp.status_code != 403

    # 3.6 Get metadata of foreign document
    resp = await async_client.get(f"/claims/{claim_a_id}/documents/{doc_a_id}", headers=headers_b)
    assert resp.status_code == 404
    assert resp.status_code != 403

    # 3.7 Request presigned download URL for foreign document
    resp = await async_client.get(
        f"/claims/{claim_a_id}/documents/{doc_a_id}/download-url",
        headers=headers_b,
    )
    assert resp.status_code == 404
    assert resp.status_code != 403

    # 3.8 Soft-delete foreign document
    resp = await async_client.delete(f"/claims/{claim_a_id}/documents/{doc_a_id}", headers=headers_b)
    assert resp.status_code == 404
    assert resp.status_code != 403

    # 3.9 Access foreign claim audit trail
    resp = await async_client.get(f"/claims/{claim_a_id}/audit", headers=headers_b)
    assert resp.status_code == 404
    assert resp.status_code != 403


@pytest.mark.asyncio
async def test_cross_tenant_document_duplicate_isolation(async_client: AsyncClient):
    token_a = await register_and_login(async_client, "dup_tenant_a@claimguard.com")
    token_b = await register_and_login(async_client, "dup_tenant_b@claimguard.com")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Tenant A creates claim and uploads document
    claim_a_resp = await async_client.post("/claims", headers=headers_a, json={"title": "Claim A"})
    claim_a_id = claim_a_resp.json()["id"]

    upload_1 = await async_client.post(
        f"/claims/{claim_a_id}/documents",
        headers=headers_a,
        files={"file": ("contract.pdf", VALID_PDF_BYTES, "application/pdf")},
    )
    assert upload_1.status_code == 201

    # Tenant A uploads duplicate to SAME claim -> 409 Conflict
    upload_dup_same_claim = await async_client.post(
        f"/claims/{claim_a_id}/documents",
        headers=headers_a,
        files={"file": ("contract_copy.pdf", VALID_PDF_BYTES, "application/pdf")},
    )
    assert upload_dup_same_claim.status_code == 409
    assert upload_dup_same_claim.json()["error"]["code"] == "CONFLICT"

    # Tenant B creates claim and uploads SAME file -> 201 Created (isolated per-tenant)
    claim_b_resp = await async_client.post("/claims", headers=headers_b, json={"title": "Claim B"})
    claim_b_id = claim_b_resp.json()["id"]

    upload_tenant_b = await async_client.post(
        f"/claims/{claim_b_id}/documents",
        headers=headers_b,
        files={"file": ("contract_tenant_b.pdf", VALID_PDF_BYTES, "application/pdf")},
    )
    assert upload_tenant_b.status_code == 201
    assert upload_tenant_b.json()["content_hash"] == upload_1.json()["content_hash"]


@pytest.mark.asyncio
async def test_storage_compensation_on_graph_persistence_failure(
    async_client: AsyncClient,
    setup_e2e_isolation_environment,
    monkeypatch,
):
    _, mock_doc_repo, mock_storage = setup_e2e_isolation_environment

    token = await register_and_login(async_client, "compensate_user@claimguard.com")
    headers = {"Authorization": f"Bearer {token}"}

    claim_resp = await async_client.post("/claims", headers=headers, json={"title": "Compensation Claim"})
    claim_id = claim_resp.json()["id"]

    # Simulate FalkorDB graph persistence failure
    def failing_create_document(*_args, **_kwargs):
        raise RuntimeError("Simulated FalkorDB transaction crash during node persistence")

    monkeypatch.setattr(mock_doc_repo, "create_document", failing_create_document)

    # Attempt document upload
    upload_resp = await async_client.post(
        f"/claims/{claim_id}/documents",
        headers=headers,
        files={"file": ("fail_doc.pdf", VALID_PDF_BYTES, "application/pdf")},
    )

    # Must fail with 500
    assert upload_resp.status_code == 500

    # Verify that the two-phase compensation successfully purged the uploaded file from storage
    assert len(mock_storage.stored_objects) == 0
