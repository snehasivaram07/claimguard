import io

import pypdf
import pypdf.errors

from app.core.config import settings
from app.core.logging import logger
from app.ingestion.exceptions import CorruptedDocumentError, NoTextLayerError
from app.ingestion.models import ExtractedDocumentText, PageText


def extract_pdf_text(
    data: bytes,
    max_pages: int | None = None,
    max_chars: int | None = None,
) -> ExtractedDocumentText:
    """Extracts text from a PDF's text layer with page and character limits."""
    page_limit = max_pages or settings.EXTRACTION_MAX_PAGES
    char_limit = max_chars or settings.EXTRACTION_MAX_TEXT_CHARS

    try:
        reader = pypdf.PdfReader(io.BytesIO(data))
    except (pypdf.errors.PdfReadError, Exception) as e:
        logger.warning("PDF parsing failed with reader error: %s", e)
        raise CorruptedDocumentError(f"Failed to read PDF document: {e}") from e

    if reader.is_encrypted:
        try:
            # Attempt decrypt with empty password (common for standard open PDFs)
            reader.decrypt("")
        except Exception as e:
            raise CorruptedDocumentError("Encrypted password-protected PDFs are not supported") from e

    total_pages = len(reader.pages)
    pages_to_read = min(total_pages, page_limit)

    extracted_pages: list[PageText] = []
    full_text_chunks: list[str] = []
    current_char_offset = 0
    truncated = False

    for idx in range(pages_to_read):
        page = reader.pages[idx]
        try:
            page_text = page.extract_text() or ""
        except Exception as page_err:
            logger.warning("Error extracting text on page %s: %s", idx + 1, page_err)
            page_text = ""

        # Normalize line endings
        page_text = page_text.replace("\r\n", "\n").replace("\r", "\n")

        # Check character limit
        if current_char_offset + len(page_text) > char_limit:
            allowed_chars = max(0, char_limit - current_char_offset)
            page_text = page_text[:allowed_chars]
            truncated = True

        start_offset = current_char_offset
        end_offset = start_offset + len(page_text)

        extracted_pages.append(
            PageText(
                page_number=idx + 1,
                text=page_text,
                char_start=start_offset,
                char_end=end_offset,
            )
        )
        full_text_chunks.append(page_text)
        current_char_offset = end_offset

        if truncated:
            break

    full_text = "\n\n".join(full_text_chunks).strip()

    # If the combined extracted text is completely empty, this is an image-only PDF
    if not full_text:
        raise NoTextLayerError(
            f"PDF document (pages={total_pages}) has no extractable text layer. "
            "Optical Character Recognition (OCR) is required."
        )

    return ExtractedDocumentText(
        text=full_text,
        page_count=total_pages,
        pages=extracted_pages,
        char_count=len(full_text),
        mime_type="application/pdf",
        truncated=truncated or (total_pages > page_limit),
    )
