from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.db.models.audit import AuditEvent
from app.graph.claim_repo import ClaimRepository
from app.schemas.claim import (
    ClaimCreateRequest,
    ClaimListResponse,
    ClaimResponse,
    ClaimUpdateRequest,
)


class ClaimService:
    """Business logic for claim management and graph node synchronization."""

    def __init__(self, claim_repo: ClaimRepository | None = None):
        self._claim_repo = claim_repo

    @property
    def claim_repo(self) -> ClaimRepository:
        if self._claim_repo is None:
            self._claim_repo = ClaimRepository()
        return self._claim_repo

    async def create_claim(
        self,
        owner_id: str,
        request: ClaimCreateRequest,
        db: AsyncSession | None = None,
        ip: str | None = None,
        request_id: str | None = None,
    ) -> ClaimResponse:
        claim_data = request.model_dump()
        node_dict = self.claim_repo.create_claim(owner_id, claim_data)

        # Audit event
        if db:
            audit = AuditEvent(
                user_id=owner_id,
                action="CLAIM_CREATE",
                resource_type="claim",
                resource_id=node_dict["id"],
                ip=ip,
                request_id=request_id,
                outcome="SUCCESS",
                event_metadata={"title": node_dict.get("title")},
            )
            db.add(audit)
            await db.commit()

        return ClaimResponse.model_validate(node_dict)

    async def get_claim(self, owner_id: str, claim_id: str) -> ClaimResponse:
        node_dict = self.claim_repo.get_claim(owner_id, claim_id)
        if not node_dict:
            # 404 avoids leaking the existence of other users' claims
            raise NotFoundError("Claim not found")
        return ClaimResponse.model_validate(node_dict)

    async def list_claims(
        self,
        owner_id: str,
        skip: int = 0,
        limit: int = 50,
        include_archived: bool = False,
    ) -> ClaimListResponse:
        nodes = self.claim_repo.list_claims(
            owner_id=owner_id,
            skip=skip,
            limit=limit,
            include_archived=include_archived,
        )
        total = self.claim_repo.count_claims(owner_id=owner_id, include_archived=include_archived)

        items = [ClaimResponse.model_validate(n) for n in nodes]
        return ClaimListResponse(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
        )

    async def update_claim(
        self,
        owner_id: str,
        claim_id: str,
        request: ClaimUpdateRequest,
        db: AsyncSession | None = None,
        ip: str | None = None,
        request_id: str | None = None,
    ) -> ClaimResponse:
        existing = self.claim_repo.get_claim(owner_id, claim_id)
        if not existing:
            raise NotFoundError("Claim not found")

        updates = request.model_dump(exclude_unset=True)
        if "status" in updates and updates["status"] is not None:
            updates["status"] = updates["status"].value

        updated_dict = self.claim_repo.update_claim(owner_id, claim_id, updates)
        if not updated_dict:
            raise NotFoundError("Claim not found")

        if db:
            audit = AuditEvent(
                user_id=owner_id,
                action="CLAIM_UPDATE",
                resource_type="claim",
                resource_id=claim_id,
                ip=ip,
                request_id=request_id,
                outcome="SUCCESS",
                event_metadata={"updated_fields": list(updates.keys())},
            )
            db.add(audit)
            await db.commit()

        return ClaimResponse.model_validate(updated_dict)

    async def delete_claim(
        self,
        owner_id: str,
        claim_id: str,
        db: AsyncSession | None = None,
        ip: str | None = None,
        request_id: str | None = None,
    ) -> bool:
        existing = self.claim_repo.get_claim(owner_id, claim_id)
        if not existing:
            raise NotFoundError("Claim not found")

        success = self.claim_repo.soft_delete_claim(owner_id, claim_id)

        if db and success:
            audit = AuditEvent(
                user_id=owner_id,
                action="CLAIM_DELETE",
                resource_type="claim",
                resource_id=claim_id,
                ip=ip,
                request_id=request_id,
                outcome="SUCCESS",
                event_metadata={"mode": "soft_delete_archived"},
            )
            db.add(audit)
            await db.commit()

        return success

    def find_candidate_claims(self, _owner_id: str, _document_text: str) -> list[dict[str, Any]]:
        """Phase 2 Extension Stub: Claim matching engine.

        Matches unstructured document text to candidate open claims.
        Phase 1 returns an empty list as specified.
        """
        return []


claim_service = ClaimService()
