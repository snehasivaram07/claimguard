import io
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.config import settings
from app.graph.document_repo import DocumentRepository
from app.inference.client import FinalInferenceError, NebiusTokenFactoryClient
from app.inference.schemas import (
    DocumentExtractionV1,
    DocumentTypeEnum,
)
from app.schemas.document import IngestionStatus
from app.services.extraction_service import (
    DocumentExtractionService,
    DocumentExtractionServiceError,
    EmptyTextLayerError,
    ExtractionNotFoundError,
    UnsupportedDocumentTypeError,
)
from app.storage.storage_service import StorageService


@pytest.fixture
def mock_storage():
    storage = MagicMock(spec=StorageService)
    # Simulate saving and deleting derived text
    storage.save_derived_text.return_value = "owner-1/claim-1/doc-1/derived/text.txt"
    storage.delete_derived_text.return_value = True
    return storage


@pytest.fixture
def mock_document_repo():
    repo = MagicMock(spec=DocumentRepository)
    repo.get_document.return_value = {
        "id": "doc-1",
        "claim_id": "claim-1",
        "owner_id": "owner-1",
        "object_key": "owner-1/claim-1/doc-1/test.txt",
        "mime_type": "text/plain",
        "status": "STORED",
    }
    repo.update_processing_status.return_value = True
    repo.update_extraction_metadata.return_value = True
    return repo


@pytest.fixture
def mock_llm_client():
    client = MagicMock(spec=NebiusTokenFactoryClient)
    return client


# ============================================================================
# Extraction Service Unit & Pipeline Tests
# ============================================================================


@pytest.mark.asyncio
async def test_extract_document_success(monkeypatch, mock_document_repo, mock_storage, mock_llm_client):
    monkeypatch.setattr(settings, "INFERENCE_ENABLED", True)

    raw_doc_text = "Police Report incident on 2024-03-10 by Officer Blake. Damage estimated at 2,500.00 USD."
    mock_storage.get_object_stream.return_value = io.BytesIO(raw_doc_text.encode("utf-8"))

    llm_payload = json.dumps({
        "document_type": "police_report",
        "summary": "Police report of collision.",
        "dates": [{"value": "2024-03-10", "context": "incident date"}],
        "parties": [{"name": "Officer Blake", "role": "officer"}],
        "amounts": [{"amount": 2500.0, "amount_type": "estimated_repair"}],
        "key_facts": ["Incident filed on scene."],
        "confidence_score": 0.95,
    })

    mock_llm_client.chat_completion = AsyncMock(
        return_value={"choices": [{"message": {"content": llm_payload}}]}
    )

    service = DocumentExtractionService(
        document_repo=mock_document_repo,
        storage=mock_storage,
        client=mock_llm_client,
    )

    result = await service.extract_document(
        owner_id="owner-1",
        claim_id="claim-1",
        document_id="doc-1",
    )

    assert isinstance(result, DocumentExtractionV1)
    assert result.document_type == DocumentTypeEnum.POLICE_REPORT
    assert result.all_entities_grounded is True
    assert result.dates[0].grounded is True
    assert result.parties[0].grounded is True
    assert result.amounts[0].grounded is True

    # Verify status transitions
    mock_document_repo.update_processing_status.assert_called_with(
        owner_id="owner-1",
        claim_id="claim-1",
        document_id="doc-1",
        status=IngestionStatus.EXTRACTING.value,
    )
    mock_storage.save_derived_text.assert_called_once()
    mock_document_repo.update_extraction_metadata.assert_called_once()


@pytest.mark.asyncio
async def test_extract_document_not_found(mock_document_repo, mock_storage, mock_llm_client):
    mock_document_repo.get_document.return_value = None

    service = DocumentExtractionService(
        document_repo=mock_document_repo,
        storage=mock_storage,
        client=mock_llm_client,
    )

    with pytest.raises(ExtractionNotFoundError):
        await service.extract_document(
            owner_id="owner-foreign",
            claim_id="claim-1",
            document_id="doc-1",
        )

    # 404 masking: 0 storage reads, 0 inference calls
    mock_storage.get_object_stream.assert_not_called()
    mock_llm_client.chat_completion.assert_not_called()


@pytest.mark.asyncio
async def test_extract_document_unsupported_media_type(mock_document_repo, mock_storage, mock_llm_client):
    mock_document_repo.get_document.return_value = {
        "id": "doc-png",
        "claim_id": "claim-1",
        "owner_id": "owner-1",
        "object_key": "owner-1/claim-1/doc-png/image.png",
        "mime_type": "image/png",
        "status": "STORED",
    }
    mock_storage.get_object_stream.return_value = io.BytesIO(b"\x89PNG\r\n\x1a\nfake_image_bytes")

    service = DocumentExtractionService(
        document_repo=mock_document_repo,
        storage=mock_storage,
        client=mock_llm_client,
    )

    with pytest.raises(UnsupportedDocumentTypeError) as exc_info:
        await service.extract_document(
            owner_id="owner-1",
            claim_id="claim-1",
            document_id="doc-png",
        )

    assert exc_info.value.code == "UNSUPPORTED_MEDIA_TYPE"
    # Document status marked FAILED_FINAL with error code
    mock_document_repo.update_processing_status.assert_called_with(
        owner_id="owner-1",
        claim_id="claim-1",
        document_id="doc-png",
        status=IngestionStatus.FAILED_FINAL.value,
        error_code="UNSUPPORTED_MEDIA_TYPE",
    )
    mock_llm_client.chat_completion.assert_not_called()


@pytest.mark.asyncio
async def test_extract_document_no_text_layer(mock_document_repo, mock_storage, mock_llm_client):
    # Minimal valid PDF with 0 extractable characters
    empty_pdf_bytes = (
        b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R >>\nendobj\n"
        b"xref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000060 00000 n\n0000000115 00000 n\n"
        b"trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n165\n%%EOF\n"
    )

    mock_document_repo.get_document.return_value = {
        "id": "doc-pdf",
        "claim_id": "claim-1",
        "owner_id": "owner-1",
        "object_key": "owner-1/claim-1/doc-pdf/empty.pdf",
        "mime_type": "application/pdf",
        "status": "STORED",
    }
    mock_storage.get_object_stream.return_value = io.BytesIO(empty_pdf_bytes)

    service = DocumentExtractionService(
        document_repo=mock_document_repo,
        storage=mock_storage,
        client=mock_llm_client,
    )

    with pytest.raises(EmptyTextLayerError) as exc_info:
        await service.extract_document(
            owner_id="owner-1",
            claim_id="claim-1",
            document_id="doc-pdf",
        )

    assert exc_info.value.code == "NO_TEXT_LAYER"
    mock_document_repo.update_processing_status.assert_called_with(
        owner_id="owner-1",
        claim_id="claim-1",
        document_id="doc-pdf",
        status=IngestionStatus.FAILED_FINAL.value,
        error_code="NO_TEXT_LAYER",
    )
    mock_llm_client.chat_completion.assert_not_called()


@pytest.mark.asyncio
async def test_extract_document_inference_failure_compensatory_cleanup(
    monkeypatch, mock_document_repo, mock_storage, mock_llm_client
):
    monkeypatch.setattr(settings, "INFERENCE_ENABLED", True)

    raw_text = "Valid text for extraction."
    mock_storage.get_object_stream.return_value = io.BytesIO(raw_text.encode("utf-8"))

    # LLM fails with an InferenceError
    mock_llm_client.chat_completion = AsyncMock(
        side_effect=FinalInferenceError("Nebius service returned 500", status_code=500)
    )

    service = DocumentExtractionService(
        document_repo=mock_document_repo,
        storage=mock_storage,
        client=mock_llm_client,
    )

    with pytest.raises(DocumentExtractionServiceError):
        await service.extract_document(
            owner_id="owner-1",
            claim_id="claim-1",
            document_id="doc-1",
        )

    # Verify compensatory cleanup: derived text deleted
    mock_storage.delete_derived_text.assert_called_once_with("owner-1", "claim-1", "doc-1")

    # Verify status marked FAILED_FINAL
    mock_document_repo.update_processing_status.assert_called_with(
        owner_id="owner-1",
        claim_id="claim-1",
        document_id="doc-1",
        status=IngestionStatus.FAILED_FINAL.value,
        error_code="INFERENCE_FAILED",
    )


# ============================================================================
# DocumentRepository Update Methods Isolated Tests
# ============================================================================


def test_document_repo_update_methods_cypher_isolation():
    mock_execute = MagicMock(return_value=[[{"id": "doc-123"}]])
    repo = DocumentRepository()
    repo._execute = mock_execute

    # 1. Test update_processing_status
    status_updated = repo.update_processing_status(
        owner_id="user-1",
        claim_id="claim-1",
        document_id="doc-123",
        status="EXTRACTING",
        error_code=None,
    )
    assert status_updated is True
    query, params = mock_execute.call_args[0]
    assert "MATCH (u:User {id: $owner_id})-[:OWNS]->(c:Claim {id: $claim_id, owner_id: $owner_id})-[:HAS_DOCUMENT]->(d:Document {id: $document_id, owner_id: $owner_id})" in query
    assert params["owner_id"] == "user-1"
    assert params["status"] == "EXTRACTING"

    # 2. Test update_extraction_metadata
    metadata_updated = repo.update_extraction_metadata(
        owner_id="user-1",
        claim_id="claim-1",
        document_id="doc-123",
        extraction_json='{"summary": "Test"}',
        document_type="police_report",
        summary="Test",
        status="COMPLETED",
        derived_text_key="user-1/claim-1/doc-123/derived/text.txt",
    )
    assert metadata_updated is True
    query2, params2 = mock_execute.call_args[0]
    assert "d.extraction_json = $extraction_json" in query2
    assert params2["document_type"] == "police_report"
    assert params2["derived_text_key"] == "user-1/claim-1/doc-123/derived/text.txt"
