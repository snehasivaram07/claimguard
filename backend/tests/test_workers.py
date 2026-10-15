import io
from unittest.mock import AsyncMock, patch

import pytest

from app.inference.schemas import DocumentExtractionV1, DocumentTypeEnum
from app.services.extraction_service import (
    DocumentExtractionServiceError,
    EmptyTextLayerError,
    ExtractionNotFoundError,
    UnsupportedDocumentTypeError,
    extraction_service,
)
from app.workers.extract_job import (
    EXIT_GENERAL_ERROR,
    EXIT_NOT_FOUND,
    EXIT_SUCCESS,
    EXIT_UNPROCESSABLE,
    build_arg_parser,
    execute_extraction_job,
    main,
)


def test_worker_build_arg_parser():
    parser = build_arg_parser()
    args = parser.parse_args(["user-1", "claim-1", "doc-1", "--json", "--quiet"])
    assert args.owner_id == "user-1"
    assert args.claim_id == "claim-1"
    assert args.document_id == "doc-1"
    assert args.emit_json is True
    assert args.quiet is True


@pytest.mark.asyncio
async def test_worker_execute_success(monkeypatch: pytest.MonkeyPatch):
    mock_extraction = DocumentExtractionV1(
        document_type=DocumentTypeEnum.POLICE_REPORT,
        summary="Test extraction summary.",
        all_entities_grounded=True,
    )

    monkeypatch.setattr(
        extraction_service,
        "extract_document",
        AsyncMock(return_value=mock_extraction),
    )

    stdout_capture = io.StringIO()
    with patch("sys.stdout", stdout_capture):
        exit_code = await execute_extraction_job(
            owner_id="user-1",
            claim_id="claim-1",
            document_id="doc-1",
            emit_json=True,
            quiet=False,
        )

    assert exit_code == EXIT_SUCCESS
    output = stdout_capture.getvalue()
    assert '"document_type": "police_report"' in output
    assert '"summary": "Test extraction summary."' in output


@pytest.mark.asyncio
async def test_worker_execute_not_found(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        extraction_service,
        "extract_document",
        AsyncMock(side_effect=ExtractionNotFoundError("Document not found")),
    )

    exit_code = await execute_extraction_job(
        owner_id="user-foreign",
        claim_id="claim-1",
        document_id="doc-1",
    )
    assert exit_code == EXIT_NOT_FOUND


@pytest.mark.asyncio
async def test_worker_execute_unprocessable_media_type(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        extraction_service,
        "extract_document",
        AsyncMock(side_effect=UnsupportedDocumentTypeError("Image requires OCR")),
    )

    exit_code = await execute_extraction_job(
        owner_id="user-1",
        claim_id="claim-1",
        document_id="doc-png",
    )
    assert exit_code == EXIT_UNPROCESSABLE


@pytest.mark.asyncio
async def test_worker_execute_empty_text_layer(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        extraction_service,
        "extract_document",
        AsyncMock(side_effect=EmptyTextLayerError("PDF has no text")),
    )

    exit_code = await execute_extraction_job(
        owner_id="user-1",
        claim_id="claim-1",
        document_id="doc-empty-pdf",
    )
    assert exit_code == EXIT_UNPROCESSABLE


@pytest.mark.asyncio
async def test_worker_execute_pipeline_general_error(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        extraction_service,
        "extract_document",
        AsyncMock(side_effect=DocumentExtractionServiceError("Inference failed", code="INFERENCE_FAILED")),
    )

    exit_code = await execute_extraction_job(
        owner_id="user-1",
        claim_id="claim-1",
        document_id="doc-1",
    )
    assert exit_code == EXIT_GENERAL_ERROR


def test_worker_main_cli_entrypoint():
    test_args = ["extract_job.py", "user-1", "claim-1", "doc-1", "--quiet"]

    with patch("sys.argv", test_args):
        with patch("app.workers.extract_job.execute_extraction_job", AsyncMock(return_value=EXIT_SUCCESS)):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == EXIT_SUCCESS
