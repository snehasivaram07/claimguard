import re

from app.core.config import settings
from app.core.errors import BadRequestError


def detect_mime_type_from_bytes(header_bytes: bytes) -> str | None:
    """Inspects the leading byte signature (magic bytes) to determine the true MIME type.

    Never trusts client-supplied headers or extensions.
    """
    if not header_bytes:
        return None

    # 1. PDF signature: %PDF-
    if header_bytes.startswith(b"%PDF-"):
        return "application/pdf"

    # 2. PNG signature: 89 50 4E 47 0D 0A 1A 0A
    if header_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"

    # 3. JPEG signature: FF D8 FF
    if header_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"

    # 4. EML (RFC 822 Email): starts with standard email header field tokens
    eml_header_patterns = [
        rb"(?i)^from:\s*",
        rb"(?i)^received:\s*",
        rb"(?i)^return-path:\s*",
        rb"(?i)^delivered-to:\s*",
        rb"(?i)^message-id:\s*",
        rb"(?i)^subject:\s*",
        rb"(?i)^date:\s*",
        rb"(?i)^mime-version:\s*1\.0",
    ]
    for pattern in eml_header_patterns:
        if re.search(pattern, header_bytes[:512]):
            return "message/rfc822"

    # 5. Plain text: valid UTF-8/ASCII without null bytes or binary control characters
    try:
        sample = header_bytes[:512]
        # Reject if contains binary null bytes
        if b"\x00" in sample:
            return None
        sample.decode("utf-8")
        # Check printable ASCII / Unicode ratio
        return "text/plain"
    except UnicodeDecodeError:
        return None


def validate_file_magic_bytes(
    header_bytes: bytes,
    allowed_mimes: list[str] | None = None,
) -> str:
    """Validates raw file signature against allowed MIME types.

    Raises BadRequestError on mismatch or disallowed type.
    """
    allowed = allowed_mimes or settings.ALLOWED_MIME_TYPES
    detected_mime = detect_mime_type_from_bytes(header_bytes)

    if not detected_mime:
        raise BadRequestError(
            "Uploaded file format is unsupported or contains an invalid binary signature"
        )

    if detected_mime not in allowed:
        raise BadRequestError(
            f"MIME type '{detected_mime}' is not permitted. Allowed types: {', '.join(allowed)}"
        )

    return detected_mime
