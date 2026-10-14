import hashlib
import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from httpx import AsyncClient

from app.services.claim_service import claim_service
from app.services.document_service import document_service
from app.storage.storage_service import StorageService
from tests.test_claims import InMemoryClaimRepo


class InMemoryDocumentRepo:
    """In-memory simulation of DocumentRepository enforcing owner and claim isolation."""

    def __init__(self):
        self.documents = {}

    def create_document(self, owner_id: str, claim_id: str, doc_data: dict) -> dict:
        now = datetime.now(UTC).isoformat()
        doc_id = doc_data.get("id") or str(uuid.uuid4())
        record = {
            "id": doc_id,
            "claim_id": claim_id,
            "owner_id": owner_id,
            "object_key": doc_data["object_key"],
            "content_hash": doc_data["content_hash"],
            "document_type": doc_data.get("document_type", "GENERAL_ATTACHMENT"),
            "original_filename": doc_data.get("original_filename", "unnamed"),
            "size_bytes": doc_data.get("size_bytes", 0),
            "mime_type": doc_data.get("mime_type", "application/octet-stream"),
            "uploaded_at": now,
            "version": doc_data.get("version", 1),
            "status": doc_data.get("status", "STORED"),
            "created_at": now,
            "updated_at": now,
            "schema_version": 1,
        }
        self.documents[doc_id] = record
        return record

    def get_document(self, owner_id: str, claim_id: str, document_id: str) -> dict | None:
        doc = self.documents.get(document_id)
        if doc and doc["owner_id"] == owner_id and doc["claim_id"] == claim_id:
            return doc
        return None

    def list_documents_for_claim(
        self,
        owner_id: str,
        claim_id: str,
        include_archived: bool = False,
    ) -> list[dict]:
        matching = [
            d for d in self.documents.values()
            if d["owner_id"] == owner_id and d["claim_id"] == claim_id and (include_archived or d["status"] != "ARCHIVED")
        ]
        matching.sort(key=lambda x: x["created_at"], reverse=True)
        return matching

    def find_document_by_content_hash(
        self,
        owner_id: str,
        claim_id: str,
        content_hash: str,
    ) -> dict | None:
        for d in self.documents.values():
            if (
                d["owner_id"] == owner_id
                and d["claim_id"] == claim_id
                and d["content_hash"] == content_hash
                and d["status"] != "ARCHIVED"
            ):
                return d
        return None

    def soft_delete_document(self, owner_id: str, claim_id: str, document_id: str) -> bool:
        doc = self.get_document(owner_id, claim_id, document_id)
        if not doc:
            return False
        doc["status"] = "ARCHIVED"
        doc["updated_at"] = datetime.now(UTC).isoformat()
        return True


class MockStorageService(StorageService):
    """In-memory mock storage avoiding external MinIO requirement during unit tests."""

    def __init__(self):
        super().__init__(client=MagicMock(), bucket_name="test-bucket")
        self.stored_objects = {}

    def put_object_stream(
        self,
        stream,
        object_key: str,
        content_type: str = "application/octet-stream",
        max_size_bytes: int | None = None,
    ):
        del content_type  # Mock does not store metadata headers
        payload = stream.read()
        if max_size_bytes and len(payload) > max_size_bytes:
            raise ValueError(f"Uploaded file exceeds maximum allowed size of {max_size_bytes} bytes")
        content_hash = hashlib.sha256(payload).hexdigest()
        self.stored_objects[object_key] = payload
        return {
            "object_key": object_key,
            "content_hash": content_hash,
            "size_bytes": len(payload),
        }

    def delete_object(self, object_key: str) -> bool:
        self.stored_objects.pop(object_key, None)
        return True

    def generate_presigned_download_url(
        self,
        object_key: str,
        original_filename: str | None = None,
        expires_in: int = 300,
    ) -> str:
        del original_filename  # Unused in mock URL
        return f"https://s3.local/test-bucket/{object_key}?expires={expires_in}"


@pytest.fixture(autouse=True)
def setup_document_test_environment(monkeypatch):
    mock_doc_repo = InMemoryDocumentRepo()
    mock_claim_repo = InMemoryClaimRepo()
    mock_storage = MockStorageService()

    monkeypatch.setattr(document_service, "_document_repo", mock_doc_repo)
    monkeypatch.setattr(document_service, "_storage", mock_storage)
    monkeypatch.setattr(claim_service, "_claim_repo", mock_claim_repo)

    return mock_doc_repo, mock_claim_repo, mock_storage


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


async def create_test_claim(async_client: AsyncClient, token: str, title: str = "Test Claim") -> str:
    resp = await async_client.post(
        "/claims",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": title},
    )
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_upload_valid_pdf_happy_path(async_client: AsyncClient):
    token = await get_auth_token(async_client, "pdf_user@claimguard.com")
    claim_id = await create_test_claim(async_client, token)

    valid_pdf_content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    expected_hash = hashlib.sha256(valid_pdf_content).hexdigest()

    response = await async_client.post(
        f"/claims/{claim_id}/documents",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("medical_invoice.pdf", valid_pdf_content, "application/pdf")},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["claim_id"] == claim_id
    assert data["mime_type"] == "application/pdf"
    assert data["content_hash"] == expected_hash
    assert data["status"] == "STORED"
    assert data["original_filename"] == "medical_invoice.pdf"


@pytest.mark.asyncio
async def test_upload_invalid_magic_bytes_rejected(async_client: AsyncClient):
    token = await get_auth_token(async_client, "spoof_user@claimguard.com")
    claim_id = await create_test_claim(async_client, token)

    # Executable header falsely claiming to be PDF
    spoofed_content = b"MZ\x90\x00\x03\x00\x00\x00not a real pdf"

    response = await async_client.post(
        f"/claims/{claim_id}/documents",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("spoofed.pdf", spoofed_content, "application/pdf")},
    )

    assert response.status_code == 400
    assert "unsupported or contains an invalid binary signature" in response.json()["error"]["message"]


@pytest.mark.asyncio
async def test_duplicate_document_in_same_claim_returns_409(async_client: AsyncClient):
    token = await get_auth_token(async_client, "dup_user@claimguard.com")
    claim_id = await create_test_claim(async_client, token)

    pdf_content = b"%PDF-1.5 duplicate test content"

    # First upload
    first_resp = await async_client.post(
        f"/claims/{claim_id}/documents",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("doc_v1.pdf", pdf_content, "application/pdf")},
    )
    assert first_resp.status_code == 201
    first_doc_id = first_resp.json()["id"]

    # Duplicate upload to SAME claim
    dup_resp = await async_client.post(
        f"/claims/{claim_id}/documents",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("doc_v2_renamed.pdf", pdf_content, "application/pdf")},
    )
    assert dup_resp.status_code == 409
    assert dup_resp.json()["error"]["code"] == "CONFLICT"
    assert dup_resp.json()["error"]["details"]["existing_document_id"] == first_doc_id

    # Duplicate upload with allow_duplicate=true override
    override_resp = await async_client.post(
        f"/claims/{claim_id}/documents?allow_duplicate=true",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("doc_v3_allowed.pdf", pdf_content, "application/pdf")},
    )
    assert override_resp.status_code == 201


@pytest.mark.asyncio
async def test_cross_user_duplicate_not_rejected(async_client: AsyncClient):
    token_a = await get_auth_token(async_client, "user_alpha@claimguard.com")
    token_b = await get_auth_token(async_client, "user_beta@claimguard.com")

    claim_a = await create_test_claim(async_client, token_a, "Claim A")
    claim_b = await create_test_claim(async_client, token_b, "Claim B")

    common_pdf = b"%PDF-1.4 standard public claim guide"

    # User A uploads
    resp_a = await async_client.post(
        f"/claims/{claim_a}/documents",
        headers={"Authorization": f"Bearer {token_a}"},
        files={"file": ("guide.pdf", common_pdf, "application/pdf")},
    )
    assert resp_a.status_code == 201

    # User B uploads exact same file to User B's claim -> MUST NOT be flagged as duplicate
    resp_b = await async_client.post(
        f"/claims/{claim_b}/documents",
        headers={"Authorization": f"Bearer {token_b}"},
        files={"file": ("guide.pdf", common_pdf, "application/pdf")},
    )
    assert resp_b.status_code == 201


@pytest.mark.asyncio
async def test_foreign_claim_and_document_returns_404(async_client: AsyncClient):
    token_a = await get_auth_token(async_client, "victim@claimguard.com")
    token_b = await get_auth_token(async_client, "attacker@claimguard.com")

    claim_a = await create_test_claim(async_client, token_a, "Victim Claim")
    pdf_content = b"%PDF-1.4 confidential medical record"

    doc_resp = await async_client.post(
        f"/claims/{claim_a}/documents",
        headers={"Authorization": f"Bearer {token_a}"},
        files={"file": ("medical.pdf", pdf_content, "application/pdf")},
    )
    doc_id = doc_resp.json()["id"]

    # Attacker tries to upload to Victim's claim -> 404
    att_upload = await async_client.post(
        f"/claims/{claim_a}/documents",
        headers={"Authorization": f"Bearer {token_b}"},
        files={"file": ("malicious.pdf", pdf_content, "application/pdf")},
    )
    assert att_upload.status_code == 404

    # Attacker queries metadata of Victim's document -> 404
    att_meta = await async_client.get(
        f"/claims/{claim_a}/documents/{doc_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert att_meta.status_code == 404

    # Attacker requests download URL of Victim's document -> 404
    att_down = await async_client.get(
        f"/claims/{claim_a}/documents/{doc_id}/download-url",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert att_down.status_code == 404


@pytest.mark.asyncio
async def test_presigned_download_url_generation(async_client: AsyncClient):
    token = await get_auth_token(async_client, "download_user@claimguard.com")
    claim_id = await create_test_claim(async_client, token)

    pdf_content = b"%PDF-1.4 download test file"
    doc_resp = await async_client.post(
        f"/claims/{claim_id}/documents",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("download_me.pdf", pdf_content, "application/pdf")},
    )
    doc_id = doc_resp.json()["id"]

    url_resp = await async_client.get(
        f"/claims/{claim_id}/documents/{doc_id}/download-url",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert url_resp.status_code == 200
    data = url_resp.json()
    assert "download_url" in data
    assert data["expires_in_seconds"] == 300


@pytest.mark.asyncio
async def test_soft_delete_document(async_client: AsyncClient):
    token = await get_auth_token(async_client, "delete_user@claimguard.com")
    claim_id = await create_test_claim(async_client, token)

    pdf_content = b"%PDF-1.4 deletion test file"
    doc_resp = await async_client.post(
        f"/claims/{claim_id}/documents",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("to_delete.pdf", pdf_content, "application/pdf")},
    )
    doc_id = doc_resp.json()["id"]

    # Delete
    del_resp = await async_client.delete(
        f"/claims/{claim_id}/documents/{doc_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert del_resp.status_code == 200

    # Verify excluded from active list
    list_resp = await async_client.get(
        f"/claims/{claim_id}/documents",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()["items"]) == 0

    # Verify present with include_archived=true
    archived_resp = await async_client.get(
        f"/claims/{claim_id}/documents?include_archived=true",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert archived_resp.status_code == 200
    assert len(archived_resp.json()["items"]) == 1
    assert archived_resp.json()["items"][0]["status"] == "ARCHIVED"
