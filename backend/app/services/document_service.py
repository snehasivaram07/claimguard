import io
import uuid
from typing import BinaryIO

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import AppException, BadRequestError, ConflictError, NotFoundError
from app.core.logging import logger
from app.core.mime import validate_file_magic_bytes
from app.db.models.audit import AuditEvent
from app.graph.document_repo import DocumentRepository
from app.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
    IngestionStatus,
    PresignedUrlResponse,
)
from app.services.claim_service import claim_service
from app.storage.storage_service import StorageService, storage_service


class ChainedPrefixStream:
    """Combines an already-read byte prefix with the remaining file stream to preserve streaming."""

    def __init__(self, prefix: bytes, raw_stream: BinaryIO):
        self.prefix_io = io.BytesIO(prefix)
        self.raw_stream = raw_stream

    def read(self, size: int = -1) -> bytes:
        chunk = self.prefix_io.read(size)
        if chunk:
            return chunk
        return self.raw_stream.read(size)


class DocumentService:
    """Service orchestrating secure streaming upload, integrity verification, and graph persistence."""

    def __init__(
        self,
        document_repo: DocumentRepository | None = None,
        storage: StorageService | None = None,
    ):
        self._document_repo = document_repo
        self._storage = storage

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

    async def upload_document(
        self,
        owner_id: str,
        claim_id: str,
        upload_file: UploadFile,
        allow_duplicate: bool = False,
        document_type: str = "GENERAL_ATTACHMENT",
        db: AsyncSession | None = None,
        ip: str | None = None,
        request_id: str | None = None,
    ) -> DocumentResponse:
        # 1. Enforce claim ownership boundary (returns 404 if claim does not exist or is foreign)
        await claim_service.get_claim(owner_id=owner_id, claim_id=claim_id)

        # 2. Inspect magic bytes from the first 2048 bytes
        header_bytes = await upload_file.read(2048)
        if not header_bytes:
            raise BadRequestError("Uploaded file is empty")

        detected_mime = validate_file_magic_bytes(header_bytes)

        # 3. Chain the header bytes with the remainder of the file stream
        chained_stream = ChainedPrefixStream(header_bytes, upload_file.file)

        # 4. Generate unique document UUID and namespaced storage key
        document_id = str(uuid.uuid4())
        original_filename = upload_file.filename or "unnamed_document"
        object_key = self.storage.build_object_key(
            owner_id=owner_id,
            claim_id=claim_id,
            document_id=document_id,
            original_filename=original_filename,
        )

        # 5. Stream directly into S3 while computing SHA-256 on the fly
        try:
            upload_result = self.storage.put_object_stream(
                stream=chained_stream,
                object_key=object_key,
                content_type=detected_mime,
                max_size_bytes=settings.MAX_UPLOAD_SIZE_BYTES,
            )
        except ValueError as val_err:
            raise BadRequestError(str(val_err)) from val_err

        content_hash = upload_result["content_hash"]
        size_bytes = upload_result["size_bytes"]

        # 6. Duplicate detection: same hash in the SAME claim for the SAME owner
        existing_duplicate = self.document_repo.find_document_by_content_hash(
            owner_id=owner_id,
            claim_id=claim_id,
            content_hash=content_hash,
        )

        if existing_duplicate and not allow_duplicate:
            # Compensatory cleanup: purge uploaded object from S3
            self.storage.delete_object(object_key)
            raise ConflictError(
                "A document with identical content has already been uploaded to this claim",
                details={"existing_document_id": existing_duplicate["id"]},
            )

        # 7. Create Document node linked to Claim in FalkorDB
        doc_data = {
            "id": document_id,
            "object_key": object_key,
            "content_hash": content_hash,
            "document_type": document_type,
            "original_filename": original_filename,
            "size_bytes": size_bytes,
            "mime_type": detected_mime,
            "version": 1,
            "status": IngestionStatus.STORED.value,
        }

        try:
            created_node = self.document_repo.create_document(
                owner_id=owner_id,
                claim_id=claim_id,
                doc_data=doc_data,
            )
        except Exception as graph_err:
            # Compensatory cleanup: delete object from S3 if graph persistence fails
            logger.error(
                "FalkorDB Document node creation failed for %s. Deleting S3 object %s: %s",
                document_id,
                object_key,
                graph_err,
            )
            self.storage.delete_object(object_key)
            # TODO: Phase 2 background worker will also periodically sweep unreferenced storage keys
            raise AppException(
                message="Failed to persist document node in graph database",
                code="GRAPH_PERSISTENCE_FAILED",
                status_code=500,
            ) from graph_err

        # 8. Audit event persistence
        if db:
            audit = AuditEvent(
                user_id=owner_id,
                action="DOCUMENT_UPLOAD",
                resource_type="document",
                resource_id=document_id,
                ip=ip,
                request_id=request_id,
                outcome="SUCCESS",
                event_metadata={
                    "claim_id": claim_id,
                    "mime_type": detected_mime,
                    "size_bytes": size_bytes,
                    "content_hash": content_hash,
                },
            )
            db.add(audit)
            await db.commit()

        return DocumentResponse.model_validate(created_node)

    async def get_document(
        self,
        owner_id: str,
        claim_id: str,
        document_id: str,
    ) -> DocumentResponse:
        # Enforce claim boundary first
        await claim_service.get_claim(owner_id=owner_id, claim_id=claim_id)

        node_dict = self.document_repo.get_document(
            owner_id=owner_id,
            claim_id=claim_id,
            document_id=document_id,
        )
        if not node_dict:
            raise NotFoundError("Document not found")

        return DocumentResponse.model_validate(node_dict)

    async def list_documents(
        self,
        owner_id: str,
        claim_id: str,
        include_archived: bool = False,
    ) -> DocumentListResponse:
        # Enforce claim boundary
        await claim_service.get_claim(owner_id=owner_id, claim_id=claim_id)

        nodes = self.document_repo.list_documents_for_claim(
            owner_id=owner_id,
            claim_id=claim_id,
            include_archived=include_archived,
        )
        items = [DocumentResponse.model_validate(n) for n in nodes]
        return DocumentListResponse(
            items=items,
            total=len(items),
        )

    async def generate_download_url(
        self,
        owner_id: str,
        claim_id: str,
        document_id: str,
        db: AsyncSession | None = None,
        ip: str | None = None,
        request_id: str | None = None,
    ) -> PresignedUrlResponse:
        doc = await self.get_document(owner_id, claim_id, document_id)

        url = self.storage.generate_presigned_download_url(
            object_key=doc.object_key,
            original_filename=doc.original_filename,
            expires_in=settings.PRESIGNED_URL_EXPIRE_SECONDS,
        )

        if db:
            audit = AuditEvent(
                user_id=owner_id,
                action="DOCUMENT_DOWNLOAD_URL",
                resource_type="document",
                resource_id=document_id,
                ip=ip,
                request_id=request_id,
                outcome="SUCCESS",
                event_metadata={"claim_id": claim_id},
            )
            db.add(audit)
            await db.commit()

        return PresignedUrlResponse(
            document_id=document_id,
            download_url=url,
            expires_in_seconds=settings.PRESIGNED_URL_EXPIRE_SECONDS,
        )

    async def delete_document(
        self,
        owner_id: str,
        claim_id: str,
        document_id: str,
        db: AsyncSession | None = None,
        ip: str | None = None,
        request_id: str | None = None,
    ) -> bool:
        # Verify existence
        await self.get_document(owner_id, claim_id, document_id)

        success = self.document_repo.soft_delete_document(
            owner_id=owner_id,
            claim_id=claim_id,
            document_id=document_id,
        )

        if db and success:
            audit = AuditEvent(
                user_id=owner_id,
                action="DOCUMENT_DELETE",
                resource_type="document",
                resource_id=document_id,
                ip=ip,
                request_id=request_id,
                outcome="SUCCESS",
                event_metadata={"claim_id": claim_id, "mode": "soft_delete_archived"},
            )
            db.add(audit)
            await db.commit()

        return success


document_service = DocumentService()
