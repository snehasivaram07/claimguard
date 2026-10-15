import asyncio

from app.core.logging import logger
from app.ingestion.email import extract_email_text
from app.ingestion.exceptions import IngestionError, UnsupportedMediaTypeError
from app.ingestion.models import ExtractedDocumentText
from app.ingestion.pdf import extract_pdf_text
from app.ingestion.text import extract_plain_text


def extract_document_text(data: bytes, mime_type: str) -> ExtractedDocumentText:
    """Dispatches text extraction according to MIME type with strict hostile-document safety."""
    normalized_mime = mime_type.lower().strip()

    if normalized_mime == "application/pdf":
        return extract_pdf_text(data)

    if normalized_mime == "text/plain":
        return extract_plain_text(data)

    if normalized_mime in ("message/rfc822", "application/eml"):
        return extract_email_text(data)

    if normalized_mime in ("image/png", "image/jpeg", "image/jpg"):
        raise UnsupportedMediaTypeError(
            f"Image MIME type '{mime_type}' requires Optical Character Recognition (OCR), "
            "which is reserved for Phase 3."
        )

    raise UnsupportedMediaTypeError(
        f"MIME type '{mime_type}' is not supported for text extraction in Phase 2."
    )


async def extract_document_text_async(
    data: bytes,
    mime_type: str,
    timeout_seconds: float = 30.0,
) -> ExtractedDocumentText:
    """Safely executes text extraction in a background thread with an async timeout."""
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(extract_document_text, data, mime_type),
            timeout=timeout_seconds,
        )
    except TimeoutError as timeout_err:
        logger.error(
            "Text extraction timed out after %ss for mime_type=%s",
            timeout_seconds,
            mime_type,
        )
        raise IngestionError(
            f"Document text extraction timed out after {timeout_seconds} seconds"
        ) from timeout_err
