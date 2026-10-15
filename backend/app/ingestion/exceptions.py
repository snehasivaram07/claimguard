class IngestionError(Exception):
    """Base exception for all document ingestion and text extraction operations."""

    def __init__(self, message: str, status_code: int = 500, error_code: str = "INGESTION_FAILED"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code


class UnsupportedMediaTypeError(IngestionError):
    """Raised when extraction is requested for an unsupported MIME type (e.g., images requiring OCR)."""

    def __init__(self, message: str = "Unsupported media type for text extraction"):
        super().__init__(
            message=message,
            status_code=422,
            error_code="UNSUPPORTED_MEDIA_TYPE",
        )


class NoTextLayerError(IngestionError):
    """Raised when a PDF contains no extractable text layer (e.g. scanned image-only PDF)."""

    def __init__(self, message: str = "Document contains no extractable text layer"):
        super().__init__(
            message=message,
            status_code=422,
            error_code="NO_TEXT_LAYER",
        )


class CorruptedDocumentError(IngestionError):
    """Raised when the document payload cannot be parsed due to corrupt data."""

    def __init__(self, message: str = "Document content is corrupted or unreadable"):
        super().__init__(
            message=message,
            status_code=422,
            error_code="CORRUPTED_DOCUMENT",
        )
