from app.core.config import settings
from app.ingestion.models import ExtractedDocumentText, PageText


def extract_plain_text(
    data: bytes,
    max_chars: int | None = None,
) -> ExtractedDocumentText:
    """Safely decodes and extracts content from plain text files with character bounds."""
    char_limit = max_chars or settings.EXTRACTION_MAX_TEXT_CHARS

    # Decode with replacement to handle any malformed byte sequences safely
    text = data.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")

    truncated = False
    if len(text) > char_limit:
        text = text[:char_limit]
        truncated = True

    pages = [
        PageText(
            page_number=1,
            text=text,
            char_start=0,
            char_end=len(text),
        )
    ]

    return ExtractedDocumentText(
        text=text,
        page_count=1,
        pages=pages,
        char_count=len(text),
        mime_type="text/plain",
        truncated=truncated,
    )
