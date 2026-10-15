from app.inference.schemas import (
    DocumentExtractionV1,
    ExtractedAmount,
    ExtractedDate,
    ExtractedParty,
)
from app.ingestion.models import ExtractedDocumentText, PageText


class GroundingValidator:
    """Validates extracted entity claims against original document text to identify hallucinations."""

    @staticmethod
    def _find_date_in_pages(date_entity: ExtractedDate, pages: list[PageText]) -> bool:
        query = date_entity.value.strip().lower()
        if not query:
            return False

        for page in pages:
            page_text_lower = page.text.lower()
            idx = page_text_lower.find(query)
            if idx != -1:
                date_entity.grounded = True
                date_entity.page_number = page.page_number
                date_entity.char_start = page.char_start + idx
                date_entity.char_end = date_entity.char_start + len(query)
                return True

        date_entity.grounded = False
        date_entity.page_number = None
        date_entity.char_start = None
        date_entity.char_end = None
        return False

    @staticmethod
    def _find_party_in_pages(party_entity: ExtractedParty, pages: list[PageText]) -> bool:
        query = party_entity.name.strip().lower()
        if not query:
            return False

        for page in pages:
            page_text_lower = page.text.lower()
            idx = page_text_lower.find(query)
            if idx != -1:
                party_entity.grounded = True
                party_entity.page_number = page.page_number
                party_entity.char_start = page.char_start + idx
                party_entity.char_end = party_entity.char_start + len(query)
                return True

        party_entity.grounded = False
        party_entity.page_number = None
        party_entity.char_start = None
        party_entity.char_end = None
        return False

    @staticmethod
    def _find_amount_in_pages(amount_entity: ExtractedAmount, pages: list[PageText]) -> bool:
        val = amount_entity.amount
        candidates: list[str] = [
            f"{val:.2f}",
            f"{val:,.2f}",
        ]
        if val.is_integer():
            int_val = int(val)
            candidates.extend([str(int_val), f"{int_val:,}"])

        # Deduplicate while preserving order
        unique_candidates = list(dict.fromkeys(candidates))

        for page in pages:
            page_text = page.text
            for candidate in unique_candidates:
                idx = page_text.find(candidate)
                if idx != -1:
                    amount_entity.grounded = True
                    amount_entity.page_number = page.page_number
                    amount_entity.char_start = page.char_start + idx
                    amount_entity.char_end = amount_entity.char_start + len(candidate)
                    return True

        amount_entity.grounded = False
        amount_entity.page_number = None
        amount_entity.char_start = None
        amount_entity.char_end = None
        return False

    def ground(
        self,
        extraction: DocumentExtractionV1,
        doc_text: ExtractedDocumentText,
    ) -> DocumentExtractionV1:
        """Grounds all extracted dates, parties, and amounts against the source document pages."""
        pages = doc_text.pages
        if not pages and doc_text.text:
            pages = [
                PageText(
                    page_number=1,
                    text=doc_text.text,
                    char_start=0,
                    char_end=len(doc_text.text),
                )
            ]

        grounding_results: list[bool] = []

        # Ground dates
        for d in extraction.dates:
            success = self._find_date_in_pages(d, pages)
            grounding_results.append(success)

        # Ground parties
        for p in extraction.parties:
            success = self._find_party_in_pages(p, pages)
            grounding_results.append(success)

        # Ground amounts
        for a in extraction.amounts:
            success = self._find_amount_in_pages(a, pages)
            grounding_results.append(success)

        if not grounding_results:
            extraction.all_entities_grounded = True
        else:
            extraction.all_entities_grounded = all(grounding_results)

        return extraction


grounding_validator = GroundingValidator()
