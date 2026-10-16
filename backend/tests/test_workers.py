import io
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from app.core.errors import BadRequestError, NotFoundError
from app.inference.claim_analysis_schemas import ClaimIntelligenceAnalysisV1
from app.inference.schemas import DocumentExtractionV1, DocumentTypeEnum
from app.schemas.dossier import DossierExportFormat, DossierExportResponse
from app.schemas.fraud_ring import (
    FraudRingAnalysisV1,
    FraudRingPattern,
    FraudRingSeverity,
)
from app.services.claim_intelligence_service import (
    ClaimNotFoundError,
    claim_intelligence_service,
)
from app.services.dossier_service import dossier_service
from app.services.extraction_service import (
    DocumentExtractionServiceError,
    EmptyTextLayerError,
    ExtractionNotFoundError,
    UnsupportedDocumentTypeError,
    extraction_service,
)
from app.services.fraud_ring_service import fraud_ring_service
from app.workers.analyze_claim_job import (
    build_arg_parser as build_claim_arg_parser,
)
from app.workers.analyze_claim_job import (
    execute_claim_analysis_job,
)
from app.workers.analyze_claim_job import (
    main as claim_worker_main,
)
from app.workers.detect_fraud_rings_job import (
    build_arg_parser as build_fraud_rings_arg_parser,
)
from app.workers.detect_fraud_rings_job import (
    execute_fraud_ring_detection_job,
)
from app.workers.detect_fraud_rings_job import (
    main as fraud_rings_worker_main,
)
from app.workers.export_dossier_job import (
    build_arg_parser as build_dossier_arg_parser,
)
from app.workers.export_dossier_job import (
    execute_dossier_export_job,
)
from app.workers.export_dossier_job import (
    main as dossier_worker_main,
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


def test_claim_analysis_worker_build_arg_parser():
    parser = build_claim_arg_parser()
    args = parser.parse_args(["user-1", "claim-1", "--json", "--quiet"])
    assert args.owner_id == "user-1"
    assert args.claim_id == "claim-1"
    assert args.emit_json is True
    assert args.quiet is True


@pytest.mark.asyncio
async def test_claim_analysis_worker_execute_success(monkeypatch: pytest.MonkeyPatch):
    mock_analysis = ClaimIntelligenceAnalysisV1(
        claim_id="claim-1",
        overall_risk_score=0.45,
        executive_summary="Analysis completed without major contradictions.",
    )

    monkeypatch.setattr(
        claim_intelligence_service,
        "analyze_claim",
        AsyncMock(return_value=mock_analysis),
    )

    stdout_capture = io.StringIO()
    with patch("sys.stdout", stdout_capture):
        exit_code = await execute_claim_analysis_job(
            owner_id="user-1",
            claim_id="claim-1",
            emit_json=True,
            quiet=False,
        )

    assert exit_code == EXIT_SUCCESS
    output = stdout_capture.getvalue()
    assert '"claim_id": "claim-1"' in output
    assert '"overall_risk_score": 0.45' in output
    assert '"executive_summary": "Analysis completed without major contradictions."' in output


@pytest.mark.asyncio
async def test_claim_analysis_worker_execute_not_found(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        claim_intelligence_service,
        "analyze_claim",
        AsyncMock(side_effect=ClaimNotFoundError("Claim not found")),
    )

    exit_code = await execute_claim_analysis_job(
        owner_id="foreign-user",
        claim_id="claim-1",
    )
    assert exit_code == EXIT_NOT_FOUND


@pytest.mark.asyncio
async def test_claim_analysis_worker_execute_unprocessable(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        claim_intelligence_service,
        "analyze_claim",
        AsyncMock(side_effect=BadRequestError("Zero extracted documents available for claim analysis")),
    )

    exit_code = await execute_claim_analysis_job(
        owner_id="user-1",
        claim_id="claim-1",
    )
    assert exit_code == EXIT_UNPROCESSABLE


@pytest.mark.asyncio
async def test_claim_analysis_worker_execute_general_error(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        claim_intelligence_service,
        "analyze_claim",
        AsyncMock(side_effect=RuntimeError("Unexpected connection drop")),
    )

    exit_code = await execute_claim_analysis_job(
        owner_id="user-1",
        claim_id="claim-1",
    )
    assert exit_code == EXIT_GENERAL_ERROR


def test_claim_analysis_worker_main_cli_entrypoint():
    test_args = ["analyze_claim_job.py", "user-1", "claim-1", "--quiet"]

    with patch("sys.argv", test_args):
        with patch("app.workers.analyze_claim_job.execute_claim_analysis_job", AsyncMock(return_value=EXIT_SUCCESS)):
            with pytest.raises(SystemExit) as exc_info:
                claim_worker_main()
            assert exc_info.value.code == EXIT_SUCCESS


def test_fraud_rings_worker_build_arg_parser():
    parser = build_fraud_rings_arg_parser()
    args = parser.parse_args(["user-1", "--min-shared", "3", "--json", "--quiet"])
    assert args.owner_id == "user-1"
    assert args.min_shared == 3
    assert args.emit_json is True
    assert args.quiet is True


@pytest.mark.asyncio
async def test_fraud_rings_worker_execute_success(monkeypatch: pytest.MonkeyPatch):
    mock_ring = FraudRingAnalysisV1(
        ring_id="ring-123",
        pattern=FraudRingPattern.STAGED_COLLISION_RING,
        severity=FraudRingSeverity.HIGH,
        risk_score=0.88,
        title="Test Fraud Syndicate",
        summary="Coordinated collisions detected.",
        claim_ids=["c-1", "c-2"],
    )

    monkeypatch.setattr(
        fraud_ring_service,
        "detect_fraud_rings",
        AsyncMock(return_value=[mock_ring]),
    )

    stdout_capture = io.StringIO()
    with patch("sys.stdout", stdout_capture):
        exit_code = await execute_fraud_ring_detection_job(
            owner_id="user-1",
            min_shared=2,
            emit_json=True,
            quiet=False,
        )

    assert exit_code == EXIT_SUCCESS
    output = stdout_capture.getvalue()
    assert '"ring_id": "ring-123"' in output
    assert '"pattern": "staged_collision_ring"' in output


@pytest.mark.asyncio
async def test_fraud_rings_worker_execute_invalid_threshold():
    exit_code = await execute_fraud_ring_detection_job(
        owner_id="user-1",
        min_shared=0,
    )
    assert exit_code == EXIT_UNPROCESSABLE


@pytest.mark.asyncio
async def test_fraud_rings_worker_execute_general_error(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        fraud_ring_service,
        "detect_fraud_rings",
        AsyncMock(side_effect=RuntimeError("Graph engine connection error")),
    )

    exit_code = await execute_fraud_ring_detection_job(
        owner_id="user-1",
        min_shared=2,
    )
    assert exit_code == EXIT_GENERAL_ERROR


def test_fraud_rings_worker_main_cli_entrypoint():
    test_args = ["detect_fraud_rings_job.py", "user-1", "--quiet"]

    with patch("sys.argv", test_args):
        with patch("app.workers.detect_fraud_rings_job.execute_fraud_ring_detection_job", AsyncMock(return_value=EXIT_SUCCESS)):
            with pytest.raises(SystemExit) as exc_info:
                fraud_rings_worker_main()
            assert exc_info.value.code == EXIT_SUCCESS


def test_dossier_worker_build_arg_parser():
    parser = build_dossier_arg_parser()
    args = parser.parse_args([
        "user-1",
        "claim-1",
        "--format",
        "html",
        "--output",
        "/tmp/report.html",
        "--stdout",
        "--quiet",
    ])
    assert args.owner_id == "user-1"
    assert args.claim_id == "claim-1"
    assert args.format_str == "html"
    assert args.output_path == "/tmp/report.html"
    assert args.print_stdout is True
    assert args.quiet is True


@pytest.mark.asyncio
async def test_dossier_worker_execute_success_stdout(monkeypatch: pytest.MonkeyPatch):
    mock_resp = DossierExportResponse(
        claim_id="claim-1",
        format=DossierExportFormat.MARKDOWN,
        content_type="text/markdown; charset=utf-8",
        filename="dossier_claim-1.md",
        content="# SIU Forensic Dossier\n\nExecutive Summary",
    )

    monkeypatch.setattr(
        dossier_service,
        "export_dossier",
        AsyncMock(return_value=mock_resp),
    )

    stdout_capture = io.StringIO()
    with patch("sys.stdout", stdout_capture):
        exit_code = await execute_dossier_export_job(
            owner_id="user-1",
            claim_id="claim-1",
            format_str="markdown",
            print_stdout=True,
            quiet=False,
        )

    assert exit_code == EXIT_SUCCESS
    output = stdout_capture.getvalue()
    assert "# SIU Forensic Dossier" in output
    assert "Executive Summary" in output


@pytest.mark.asyncio
async def test_dossier_worker_execute_success_file_output(tmp_path, monkeypatch: pytest.MonkeyPatch):
    mock_resp = DossierExportResponse(
        claim_id="claim-2",
        format=DossierExportFormat.JSON,
        content_type="application/json",
        filename="dossier_claim-2.json",
        content='{"claim_id": "claim-2", "risk_score": 0.85}',
    )

    monkeypatch.setattr(
        dossier_service,
        "export_dossier",
        AsyncMock(return_value=mock_resp),
    )

    dest_file = str(tmp_path / "sub" / "out.json")
    exit_code = await execute_dossier_export_job(
        owner_id="user-1",
        claim_id="claim-2",
        format_str="json",
        output_path=dest_file,
        print_stdout=False,
        quiet=True,
    )

    assert exit_code == EXIT_SUCCESS
    saved_content = Path(dest_file).read_text(encoding="utf-8")
    assert '{"claim_id": "claim-2", "risk_score": 0.85}' in saved_content


@pytest.mark.asyncio
async def test_dossier_worker_execute_not_found(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        dossier_service,
        "export_dossier",
        AsyncMock(side_effect=NotFoundError("Claim not found")),
    )

    exit_code = await execute_dossier_export_job(
        owner_id="user-1",
        claim_id="claim-missing",
    )
    assert exit_code == EXIT_NOT_FOUND


@pytest.mark.asyncio
async def test_dossier_worker_execute_invalid_format():
    exit_code = await execute_dossier_export_job(
        owner_id="user-1",
        claim_id="claim-1",
        format_str="invalid_pdf",
    )
    assert exit_code == EXIT_UNPROCESSABLE


@pytest.mark.asyncio
async def test_dossier_worker_execute_general_error(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        dossier_service,
        "export_dossier",
        AsyncMock(side_effect=RuntimeError("FalkorDB connection timeout")),
    )

    exit_code = await execute_dossier_export_job(
        owner_id="user-1",
        claim_id="claim-1",
    )
    assert exit_code == EXIT_GENERAL_ERROR


def test_dossier_worker_main_cli_entrypoint():
    test_args = ["export_dossier_job.py", "user-1", "claim-1", "--format", "json", "--quiet"]

    with patch("sys.argv", test_args):
        with patch("app.workers.export_dossier_job.execute_dossier_export_job", AsyncMock(return_value=EXIT_SUCCESS)):
            with pytest.raises(SystemExit) as exc_info:
                dossier_worker_main()
            assert exc_info.value.code == EXIT_SUCCESS


