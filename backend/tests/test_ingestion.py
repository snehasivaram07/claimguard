import io

import pypdf
import pytest

from app.ingestion.exceptions import (
    CorruptedDocumentError,
    NoTextLayerError,
    UnsupportedMediaTypeError,
)
from app.ingestion.extractor import (
    extract_document_text,
    extract_document_text_async,
)
from app.storage.storage_service import StorageService

VALID_PDF_WITH_TEXT = (
    b"%PDF-1.4\n"
    b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
    b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
    b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
    b"4 0 obj << /Length 55 >> stream\n"
    b"BT /F1 12 Tf 72 712 Td (Claim Number: CLM-2026-999) Tj ET\n"
    b"endstream endobj\n"
    b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
    b"xref\n0 6\n"
    b"0000000000 65535 f \n"
    b"0000000009 00000 n \n"
    b"0000000058 00000 n \n"
    b"0000000115 00000 n \n"
    b"0000000266 00000 n \n"
    b"0000000373 00000 n \n"
    b"trailer << /Size 6 /Root 1 0 R >>\n"
    b"startxref\n448\n%%EOF"
)


def create_blank_pdf_bytes() -> bytes:
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=100, height=100)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def test_pdf_extraction_happy_path():
    result = extract_document_text(VALID_PDF_WITH_TEXT, "application/pdf")
    assert "Claim Number: CLM-2026-999" in result.text
    assert result.page_count == 1
    assert len(result.pages) == 1
    assert result.pages[0].page_number == 1
    assert result.mime_type == "application/pdf"
    assert not result.truncated


def test_pdf_no_text_layer_raises_error():
    blank_pdf = create_blank_pdf_bytes()
    with pytest.raises(NoTextLayerError) as exc_info:
        extract_document_text(blank_pdf, "application/pdf")
    assert "no extractable text layer" in str(exc_info.value)
    assert exc_info.value.status_code == 422


def test_pdf_corrupted_data_raises_error():
    bad_pdf = b"%PDF-1.4\ncorrupted gibberish\n%%EOF"
    with pytest.raises(CorruptedDocumentError):
        extract_document_text(bad_pdf, "application/pdf")


def test_pdf_character_cap_truncation():
    from app.ingestion.pdf import extract_pdf_text

    capped_res = extract_pdf_text(VALID_PDF_WITH_TEXT, max_chars=10)
    assert len(capped_res.text) <= 10
    assert capped_res.truncated is True


def test_plain_text_extraction():
    sample_text = "Policy Holder: Jane Doe\nIncident Date: 2026-03-15\nLoss Description: Hail damage to roof."
    data = sample_text.encode("utf-8")
    result = extract_document_text(data, "text/plain")

    assert result.text == sample_text
    assert result.page_count == 1
    assert len(result.pages) == 1
    assert result.pages[0].char_start == 0
    assert result.pages[0].char_end == len(sample_text)
    assert result.mime_type == "text/plain"


def test_plain_text_safe_decoding_of_invalid_bytes():
    corrupt_bytes = b"Incident Report \xff\xfe with invalid unicode"
    result = extract_document_text(corrupt_bytes, "text/plain")
    assert "Incident Report" in result.text


def test_email_extraction_rfc822():
    raw_email = (
        b"From: agent@insurance.com\r\n"
        b"To: claims@claimguard.com\r\n"
        b"Subject: Notice of Loss Claim CLM-888\r\n"
        b"Date: Mon, 15 Oct 2026 10:00:00 +0000\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"\r\n"
        b"Dear Adjuster,\r\n"
        b"Please find the initial notice of property damage.\r\n"
        b"Estimated cost is $15,000.\r\n"
    )
    result = extract_document_text(raw_email, "message/rfc822")
    assert "From: agent@insurance.com" in result.text
    assert "Subject: Notice of Loss Claim CLM-888" in result.text
    assert "Estimated cost is $15,000." in result.text
    assert result.page_count == 1
    assert result.mime_type == "message/rfc822"


def test_unsupported_image_types_raise_422():
    dummy_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    with pytest.raises(UnsupportedMediaTypeError) as exc_info:
        extract_document_text(dummy_png, "image/png")
    assert exc_info.value.status_code == 422
    assert "Optical Character Recognition (OCR)" in str(exc_info.value)

    dummy_jpeg = b"\xff\xd8\xff\xe0"
    with pytest.raises(UnsupportedMediaTypeError) as exc_info_jpeg:
        extract_document_text(dummy_jpeg, "image/jpeg")
    assert exc_info_jpeg.value.status_code == 422


@pytest.mark.asyncio
async def test_async_extraction_helper():
    sample_text = "Async extraction test content."
    result = await extract_document_text_async(sample_text.encode("utf-8"), "text/plain")
    assert result.text == sample_text


def test_derived_text_storage_helpers():
    storage = StorageService(bucket_name="test-bucket")
    storage._client = pytest.importorskip("unittest.mock").MagicMock()

    key = storage.build_derived_text_key("owner-1", "claim-2", "doc-3")
    assert key == "owner-1/claim-2/doc-3/derived/text.txt"
