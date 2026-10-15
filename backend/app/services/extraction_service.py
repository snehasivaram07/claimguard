from typing import Any

from fastapi import status

from app.core.errors import AppException, NotFoundError
from app.core.logging import logger
from app.graph.document_repo import DocumentRepository
from app.inference.client import InferenceError, NebiusTokenFactoryClient, inference_client
from app.inference.grounding import GroundingValidator, grounding_validator
from app.inference.guard import BaseGuard, default_guard
from app.inference.output_parser import ExtractionParseError, parse_with_repair
from app.inference.prompts.document_extraction_v1 import (
    EXTRACTION_SYSTEM_PROMPT,
    build_extraction_user_prompt,
)
from app.inference.router import ModelRouter, TaskType, model_router
from app.inference.schemas import DocumentExtractionV1
from app.ingestion.exceptions import IngestionError, NoTextLayerError, UnsupportedMediaTypeError
from app.ingestion.extractor import extract_document_text_async
from app.schemas.document import IngestionStatus
from app.storage.storage_service import StorageService, storage_service


class ExtractionNotFoundError(NotFoundError):
    """Raised when a document or claim cannot be found for the requesting owner (404 masking)."""

    def __init__(self, message: str = "Document not found"):
        super().__init__(message=message)


class DocumentExtractionServiceError(AppException):
    """Base exception for document extraction pipeline operations."""

    def __init__(
        self,
        message: str,
        code: str = "EXTRACTION_FAILED",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Any | None = None,
    ):
        super().__init__(message=message, code=code, status_code=status_code, details=details)


class UnsupportedDocumentTypeError(DocumentExtractionServiceError):
    """Raised when document MIME type cannot be extracted (e.g. image requiring OCR)."""

    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="UNSUPPORTED_MEDIA_TYPE",
            status_code=422,
        )


class EmptyTextLayerError(DocumentExtractionServiceError):
    """Raised when PDF or document contains no extractable text layer."""

    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="NO_TEXT_LAYER",
            status_code=422,
        )


class DocumentExtractionService:
    """Orchestrates end-to-end document text extraction, AI structured inference, and entity grounding."""

    def __init__(
        self,
        document_repo: DocumentRepository | None = None,
        storage: StorageService | None = None,
        client: NebiusTokenFactoryClient | None = None,
        router: ModelRouter | None = None,
        guard: BaseGuard | None = None,
        validator: GroundingValidator | None = None,
    ):
        self._document_repo = document_repo
        self._storage = storage
        self._client = client
        self._router = router
        self._guard = guard
        self._validator = validator

    @property
    def document_repo(self) -> DocumentRepository:
        if self._document_repo is None:
            self._document_repo = DocumentRepository()
        return self._document_repo

    @property
    def storage(self) -> StorageService:
        if self._storage is None:
            self._storage = storage_service
        return self._storage

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

    @property
    def guard(self) -> BaseGuard:
        if self._guard is None:
            self._guard = default_guard
        return self._guard

    @property
    def validator(self) -> GroundingValidator:
        if self._validator is None:
            self._validator = grounding_validator
        return self._validator

    async def extract_document(
        self,
        owner_id: str,
        claim_id: str,
        document_id: str,
    ) -> DocumentExtractionV1:
        """Executes full extraction pipeline: S3 fetch -> text parse -> guard -> Nemotron -> ground -> FalkorDB."""
        # 1. Ownership & existence check (strictly owner-scoped to preserve 404 existence masking)
        doc = self.document_repo.get_document(owner_id=owner_id, claim_id=claim_id, document_id=document_id)
        if not doc:
            raise ExtractionNotFoundError()

        # 2. Transition document node status to EXTRACTING
        self.document_repo.update_processing_status(
            owner_id=owner_id,
            claim_id=claim_id,
            document_id=document_id,
            status=IngestionStatus.EXTRACTING.value,
        )

        derived_artifact_created = False
        try:
            # 3. Stream document bytes from object storage
            stream = self.storage.get_object_stream(doc["object_key"])
            raw_bytes = stream.read()

            # 4. Ingestion text extraction (async with timeout)
            try:
                doc_text = await extract_document_text_async(raw_bytes, doc["mime_type"])
            except UnsupportedMediaTypeError as err:
                raise UnsupportedDocumentTypeError(str(err)) from err
            except NoTextLayerError as err:
                raise EmptyTextLayerError(str(err)) from err
            except IngestionError as err:
                raise DocumentExtractionServiceError(str(err), code="INGESTION_ERROR") from err

            # 5. Persist derived plain text artifact in S3
            derived_key = self.storage.save_derived_text(
                owner_id=owner_id,
                claim_id=claim_id,
                document_id=document_id,
                text_content=doc_text.text,
            )
            derived_artifact_created = True

            # 6. Guard sanitization and XML wrapping
            guard_result = self.guard.sanitize_and_wrap(doc_text.text)

            # 7. Model routing
            model_name = self.router.route(TaskType.DOCUMENT_EXTRACTION)

            # 8. Inference execution
            user_prompt = build_extraction_user_prompt(guard_result.wrapped_prompt_text)
            messages = [
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]

            try:
                resp = await self.client.chat_completion(
                    messages=messages,
                    model=model_name,
                    temperature=0.0,
                )
                raw_output = resp["choices"][0]["message"]["content"]
            except InferenceError as inf_err:
                logger.error(
                    "Inference failure during document extraction for document_id=%s: status_code=%s",
                    document_id,
                    inf_err.status_code,
                )
                raise DocumentExtractionServiceError(
                    "Inference service failed to process document",
                    code="INFERENCE_FAILED",
                    status_code=inf_err.status_code or 502,
                ) from inf_err

            # 9. Defensive parsing & 1-shot repair
            try:
                extraction = await parse_with_repair(
                    raw_text=raw_output,
                    client=self.client,
                    model=model_name,
                )
            except ExtractionParseError as parse_err:
                logger.error("Document extraction parsing failed for document_id=%s", document_id)
                raise DocumentExtractionServiceError(
                    "Failed to parse extraction output into structured schema",
                    code="EXTRACTION_PARSE_FAILED",
                    status_code=502,
                ) from parse_err

            # 10. Entity grounding against source document pages
            grounded_extraction = self.validator.ground(extraction, doc_text)

            # 11. Persist extraction JSON and update status to COMPLETED in FalkorDB
            extraction_json = grounded_extraction.model_dump_json()
            self.document_repo.update_extraction_metadata(
                owner_id=owner_id,
                claim_id=claim_id,
                document_id=document_id,
                extraction_json=extraction_json,
                document_type=grounded_extraction.document_type.value,
                summary=grounded_extraction.summary,
                status=IngestionStatus.COMPLETED.value,
                derived_text_key=derived_key,
            )

            logger.info(
                "Document extraction completed successfully: document_id=%s claim_id=%s all_grounded=%s",
                document_id,
                claim_id,
                grounded_extraction.all_entities_grounded,
            )
            return grounded_extraction

        except Exception as exc:
            # Compensatory rollback: purge derived text artifact if created
            if derived_artifact_created:
                try:
                    self.storage.delete_derived_text(owner_id, claim_id, document_id)
                except Exception as del_err:
                    logger.warning(
                        "Compensatory deletion of derived text failed: %s",
                        del_err,
                    )

            # Transition document status to FAILED_FINAL with specific error code
            error_code = getattr(exc, "code", "EXTRACTION_FAILED")
            self.document_repo.update_processing_status(
                owner_id=owner_id,
                claim_id=claim_id,
                document_id=document_id,
                status=IngestionStatus.FAILED_FINAL.value,
                error_code=error_code,
            )
            raise


extraction_service = DocumentExtractionService()
