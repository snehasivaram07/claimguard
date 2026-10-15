import json
from datetime import UTC, datetime
from typing import Any

from app.core.errors import NotFoundError
from app.core.logging import logger
from app.graph.claim_repo import ClaimRepository
from app.graph.document_repo import DocumentRepository
from app.graph.entity_repo import EntityRepository, entity_repo
from app.inference.claim_analysis_schemas import ClaimIntelligenceAnalysisV1
from app.inference.client import NebiusTokenFactoryClient, inference_client
from app.inference.output_parser import clean_json_text
from app.inference.prompts.claim_intelligence_v1 import (
    CLAIM_INTELLIGENCE_SYSTEM_PROMPT,
    build_claim_intelligence_user_prompt,
)
from app.inference.router import ModelRouter, TaskType, model_router
from app.schemas.document import IngestionStatus
from app.services.extraction_service import DocumentExtractionService, extraction_service


class ClaimNotFoundError(NotFoundError):
    """Raised when a claim does not exist or is unauthorized for requesting owner (404 masking)."""

    def __init__(self, message: str = "Claim not found"):
        super().__init__(message=message)


class ClaimIntelligenceService:
    """Orchestrates multi-document cross-validation, contradiction analysis, and graph entity linking."""

    def __init__(
        self,
        claim_repo: ClaimRepository | None = None,
        document_repo: DocumentRepository | None = None,
        entity_repository: EntityRepository | None = None,
        extraction_srv: DocumentExtractionService | None = None,
        client: NebiusTokenFactoryClient | None = None,
        router: ModelRouter | None = None,
    ):
        self._claim_repo = claim_repo
        self._document_repo = document_repo
        self._entity_repo = entity_repository
        self._extraction_service = extraction_srv
        self._client = client
        self._router = router

    @property
    def claim_repo(self) -> ClaimRepository:
        if self._claim_repo is None:
            self._claim_repo = ClaimRepository()
        return self._claim_repo

    @property
    def document_repo(self) -> DocumentRepository:
        if self._document_repo is None:
            self._document_repo = DocumentRepository()
        return self._document_repo

    @property
    def entity_repo(self) -> EntityRepository:
        if self._entity_repo is None:
            self._entity_repo = entity_repo
        return self._entity_repo

    @property
    def extraction_service(self) -> DocumentExtractionService:
        if self._extraction_service is None:
            self._extraction_service = extraction_service
        return self._extraction_service

    @property
    def client(self) -> NebiusTokenFactoryClient:
        if self._client is None:
            self._client = inference_client
        return self._client

    @property
    def router(self) -> ModelRouter:
        if self._router is None:
            self._router = model_router
        return self._router

    async def analyze_claim(
        self,
        owner_id: str,
        claim_id: str,
    ) -> ClaimIntelligenceAnalysisV1:
        """Aggregates all document evidence, links entities, calls Nemotron Super, and updates graph."""
        now = datetime.now(UTC).isoformat()

        # 1. Ownership & existence check (enforcing 404 existence masking)
        claim = self.claim_repo.get_claim(owner_id=owner_id, claim_id=claim_id)
        if not claim:
            raise ClaimNotFoundError()

        # 2. Retrieve all active documents attached to the claim
        docs = self.document_repo.list_documents_for_claim(
            owner_id=owner_id,
            claim_id=claim_id,
            include_archived=False,
        )

        if not docs:
            empty_analysis = ClaimIntelligenceAnalysisV1(
                claim_id=claim_id,
                overall_risk_score=0.0,
                executive_summary="No active documents uploaded for this claim.",
                timeline=[],
                discrepancies=[],
                unresolved_questions=[],
                confidence_score=1.0,
                analyzed_at=now,
            )
            self.claim_repo.update_claim_analysis(
                owner_id=owner_id,
                claim_id=claim_id,
                analysis_json=empty_analysis.model_dump_json(),
                risk_score=0.0,
            )
            return empty_analysis

        # 3. Assemble extractions and perform entity linking into FalkorDB
        extractions: list[dict[str, Any]] = []

        for doc in docs:
            doc_id = doc["id"]
            extraction_raw = doc.get("extraction_json")

            if not extraction_raw or doc.get("status") != IngestionStatus.COMPLETED.value:
                try:
                    # Auto-extract document if not yet processed
                    extracted = await self.extraction_service.extract_document(
                        owner_id=owner_id,
                        claim_id=claim_id,
                        document_id=doc_id,
                    )
                    extraction_data = extracted.model_dump()
                except Exception as ext_err:
                    logger.warning(
                        "Auto-extraction for document %s during claim analysis failed: %s",
                        doc_id,
                        ext_err,
                    )
                    extraction_data = {
                        "id": doc_id,
                        "original_filename": doc.get("original_filename", "unnamed"),
                        "document_type": doc.get("document_type", "other"),
                        "summary": "Extraction unavailable",
                    }
            else:
                try:
                    extraction_data = json.loads(extraction_raw)
                except Exception:
                    extraction_data = {"id": doc_id, "summary": "Unparseable extraction cache"}

            extraction_data["id"] = doc_id
            extraction_data["original_filename"] = doc.get("original_filename", "unnamed")
            extractions.append(extraction_data)

            # 4. Link extracted parties as first-class domain graph nodes in FalkorDB
            for party in extraction_data.get("parties", []):
                party_name = party.get("name")
                if not party_name:
                    continue
                role = party.get("role", "other")
                if role in ("claimant", "insured", "witness", "officer", "physician"):
                    self.entity_repo.upsert_person(
                        owner_id=owner_id,
                        claim_id=claim_id,
                        name=party_name,
                        role=role,
                        document_id=doc_id,
                    )
                else:
                    self.entity_repo.upsert_organization(
                        owner_id=owner_id,
                        claim_id=claim_id,
                        name=party_name,
                        org_type=role,
                        document_id=doc_id,
                    )

        # 5. Build prompt for Nemotron Super cross-validation
        user_prompt = build_claim_intelligence_user_prompt(
            claim_id=claim_id,
            claim_metadata=claim,
            extractions=extractions,
        )

        messages = [
            {"role": "system", "content": CLAIM_INTELLIGENCE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        model_name = self.router.resolve_model(TaskType.CROSS_DOCUMENT_ANALYSIS)

        # 6. Execute inference on Nebius Token Factory
        response = await self.client.chat_completion(
            messages=messages,
            model=model_name,
            temperature=0.0,
        )

        raw_output = response["choices"][0]["message"]["content"]
        cleaned_json = clean_json_text(raw_output)

        data = json.loads(cleaned_json)
        data["claim_id"] = claim_id
        data["analyzed_at"] = now

        analysis = ClaimIntelligenceAnalysisV1.model_validate(data)

        # 7. Persist intelligence report to FalkorDB Claim node
        self.claim_repo.update_claim_analysis(
            owner_id=owner_id,
            claim_id=claim_id,
            analysis_json=analysis.model_dump_json(),
            risk_score=analysis.overall_risk_score,
        )

        logger.info(
            "Claim intelligence analysis completed: claim_id=%s risk_score=%s discrepancies=%d",
            claim_id,
            analysis.overall_risk_score,
            len(analysis.discrepancies),
        )
        return analysis

    def get_claim_analysis(
        self,
        owner_id: str,
        claim_id: str,
    ) -> ClaimIntelligenceAnalysisV1 | None:
        """Retrieves cached claim intelligence report from FalkorDB node property."""
        claim = self.claim_repo.get_claim(owner_id=owner_id, claim_id=claim_id)
        if not claim:
            raise ClaimNotFoundError()

        raw_json = claim.get("analysis_json")
        if not raw_json:
            return None

        return ClaimIntelligenceAnalysisV1.model_validate_json(raw_json)


claim_intelligence_service = ClaimIntelligenceService()
