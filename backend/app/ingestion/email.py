import email
import re
from email import policy

from app.core.config import settings
from app.ingestion.models import ExtractedDocumentText, PageText


def _strip_html_tags(html: str) -> str:
    """Rudimentary regex tag stripper for fallback when only HTML parts exist."""
    clean = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", clean).strip()


def extract_email_text(
    data: bytes,
    max_chars: int | None = None,
) -> ExtractedDocumentText:
    """Extracts structured headers and plain-text message body from RFC 822 .eml messages."""
    char_limit = max_chars or settings.EXTRACTION_MAX_TEXT_CHARS

    msg = email.message_from_bytes(data, policy=policy.default)

    header_lines: list[str] = []
    for header in ["From", "To", "Subject", "Date"]:
        val = msg.get(header)
        if val:
            header_lines.append(f"{header}: {val}")

    headers_block = "\n".join(header_lines)

    # Extract body parts
    body_parts: list[str] = []
    html_fallback: list[str] = []

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = part.get_content_disposition()

            # Ignore attachments
            if disposition == "attachment":
                continue

            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    body_parts.append(payload.decode("utf-8", errors="replace"))
            elif content_type == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    html_fallback.append(payload.decode("utf-8", errors="replace"))
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            text = payload.decode("utf-8", errors="replace")
            if msg.get_content_type() == "text/html":
                html_fallback.append(text)
            else:
                body_parts.append(text)

    # Combine text body or fall back to stripped HTML
    body_text = "\n\n".join(body_parts).strip()
    if not body_text and html_fallback:
        body_text = "\n\n".join(_strip_html_tags(h) for h in html_fallback).strip()

    combined = f"{headers_block}\n\n{body_text}".strip()
    combined = combined.replace("\r\n", "\n").replace("\r", "\n")

    truncated = False
    if len(combined) > char_limit:
        combined = combined[:char_limit]
        truncated = True

    pages = [
        PageText(
            page_number=1,
            text=combined,
            char_start=0,
            char_end=len(combined),
        )
    ]

    return ExtractedDocumentText(
        text=combined,
        page_count=1,
        pages=pages,
        char_count=len(combined),
        mime_type="message/rfc822",
        truncated=truncated,
    )
