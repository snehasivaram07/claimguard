from dataclasses import dataclass, field


@dataclass(frozen=True)
class PageText:
    """Represents text extracted from a single document page with character offset bounds."""

    page_number: int
    text: str
    char_start: int
    char_end: int


@dataclass
class ExtractedDocumentText:
    """Aggregated text extraction output with per-page offsets for grounding validation."""

    text: str
    page_count: int
    pages: list[PageText] = field(default_factory=list)
    char_count: int = 0
    mime_type: str = "text/plain"
    truncated: bool = False

    def __post_init__(self):
        if not self.char_count:
            self.char_count = len(self.text)
