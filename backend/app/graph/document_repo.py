import uuid
from datetime import UTC, datetime
from typing import Any

from app.graph.base_repo import BaseGraphRepository


class DocumentRepository(BaseGraphRepository):
    """FalkorDB repository for Document nodes and (:Claim)-[:HAS_DOCUMENT]->(:Document) relationships.

    All Cypher queries enforce strict owner and claim containment.
    """

    def create_document(
        self,
        owner_id: str,
        claim_id: str,
        doc_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Creates a Document node linked to an existing Claim owned by the user."""
        now = datetime.now(UTC).isoformat()
        doc_id = doc_data.get("id") or str(uuid.uuid4())

        query = """
        MATCH (u:User {id: $owner_id})-[:OWNS]->(c:Claim {id: $claim_id, owner_id: $owner_id})
        CREATE (d:Document {
            id: $doc_id,
            claim_id: $claim_id,
            owner_id: $owner_id,
            object_key: $object_key,
            content_hash: $content_hash,
            document_type: $document_type,
            original_filename: $original_filename,
            size_bytes: $size_bytes,
            mime_type: $mime_type,
            uploaded_at: $now,
            version: $version,
            status: $status,
            created_at: $now,
            updated_at: $now,
            schema_version: $schema_version
        })
        CREATE (c)-[:HAS_DOCUMENT]->(d)
        RETURN d
        """

        params = {
            "owner_id": owner_id,
            "claim_id": claim_id,
            "doc_id": doc_id,
            "object_key": doc_data["object_key"],
            "content_hash": doc_data["content_hash"],
            "document_type": doc_data.get("document_type", "GENERAL_ATTACHMENT"),
            "original_filename": doc_data.get("original_filename", "unnamed"),
            "size_bytes": doc_data.get("size_bytes", 0),
            "mime_type": doc_data.get("mime_type", "application/octet-stream"),
            "version": doc_data.get("version", 1),
            "status": doc_data.get("status", "STORED"),
            "now": now,
            "schema_version": self.SCHEMA_VERSION,
        }

        rows = self._execute(query, params)
        if not rows or not rows[0]:
            raise RuntimeError(f"Claim {claim_id} not found for owner or Document creation failed")

        return self._node_to_dict(rows[0][0])

    def get_document(
        self,
        owner_id: str,
        claim_id: str,
        document_id: str,
    ) -> dict[str, Any] | None:
        """Retrieves document metadata, strictly validating owner and claim containment."""
        query = """
        MATCH (u:User {id: $owner_id})-[:OWNS]->(c:Claim {id: $claim_id, owner_id: $owner_id})-[:HAS_DOCUMENT]->(d:Document {id: $document_id, owner_id: $owner_id})
        RETURN d
        """
        params = {
            "owner_id": owner_id,
            "claim_id": claim_id,
            "document_id": document_id,
        }
        rows = self._execute(query, params)
        if not rows or not rows[0]:
            return None
        return self._node_to_dict(rows[0][0])

    def list_documents_for_claim(
        self,
        owner_id: str,
        claim_id: str,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        """Lists all documents attached to a specific claim owned by the user."""
        query = """
        MATCH (u:User {id: $owner_id})-[:OWNS]->(c:Claim {id: $claim_id, owner_id: $owner_id})-[:HAS_DOCUMENT]->(d:Document {owner_id: $owner_id})
        WHERE ($include_archived = true OR d.status <> 'ARCHIVED')
        RETURN d
        ORDER BY d.created_at DESC
        """
        params = {
            "owner_id": owner_id,
            "claim_id": claim_id,
            "include_archived": include_archived,
        }
        rows = self._execute(query, params)
        return [self._node_to_dict(row[0]) for row in rows if row and row[0]]

    def find_document_by_content_hash(
        self,
        owner_id: str,
        claim_id: str,
        content_hash: str,
    ) -> dict[str, Any] | None:
        """Detects duplicates within the SAME claim for the SAME owner.

        CRITICAL ISOLATION RULE: Never compare hashes across owners.
        """
        query = """
        MATCH (u:User {id: $owner_id})-[:OWNS]->(c:Claim {id: $claim_id, owner_id: $owner_id})-[:HAS_DOCUMENT]->(d:Document {content_hash: $content_hash, owner_id: $owner_id})
        WHERE d.status <> 'ARCHIVED'
        RETURN d
        LIMIT 1
        """
        params = {
            "owner_id": owner_id,
            "claim_id": claim_id,
            "content_hash": content_hash,
        }
        rows = self._execute(query, params)
        if not rows or not rows[0]:
            return None
        return self._node_to_dict(rows[0][0])

    def soft_delete_document(
        self,
        owner_id: str,
        claim_id: str,
        document_id: str,
    ) -> bool:
        """Marks a document as ARCHIVED (soft delete), never removing nodes destructively."""
        now = datetime.now(UTC).isoformat()
        query = """
        MATCH (u:User {id: $owner_id})-[:OWNS]->(c:Claim {id: $claim_id, owner_id: $owner_id})-[:HAS_DOCUMENT]->(d:Document {id: $document_id, owner_id: $owner_id})
        SET d.status = 'ARCHIVED', d.updated_at = $now
        RETURN d.id
        """
        params = {
            "owner_id": owner_id,
            "claim_id": claim_id,
            "document_id": document_id,
            "now": now,
        }
        rows = self._execute(query, params)
        return bool(rows and rows[0])

    def update_processing_status(
        self,
        owner_id: str,
        claim_id: str,
        document_id: str,
        status: str,
        error_code: str | None = None,
    ) -> bool:
        """Updates document processing status and optional error code with strict owner isolation."""
        now = datetime.now(UTC).isoformat()
        query = """
        MATCH (u:User {id: $owner_id})-[:OWNS]->(c:Claim {id: $claim_id, owner_id: $owner_id})-[:HAS_DOCUMENT]->(d:Document {id: $document_id, owner_id: $owner_id})
        SET d.status = $status,
            d.error_code = $error_code,
            d.updated_at = $now
        RETURN d.id
        """
        params = {
            "owner_id": owner_id,
            "claim_id": claim_id,
            "document_id": document_id,
            "status": status,
            "error_code": error_code,
            "now": now,
        }
        rows = self._execute(query, params)
        return bool(rows and rows[0])

    def update_extraction_metadata(
        self,
        owner_id: str,
        claim_id: str,
        document_id: str,
        extraction_json: str,
        document_type: str,
        summary: str,
        status: str = "COMPLETED",
        derived_text_key: str | None = None,
    ) -> bool:
        """Stores structured extraction results, derived artifact key, and marks document completed."""
        now = datetime.now(UTC).isoformat()
        query = """
        MATCH (u:User {id: $owner_id})-[:OWNS]->(c:Claim {id: $claim_id, owner_id: $owner_id})-[:HAS_DOCUMENT]->(d:Document {id: $document_id, owner_id: $owner_id})
        SET d.extraction_json = $extraction_json,
            d.document_type = $document_type,
            d.summary = $summary,
            d.status = $status,
            d.error_code = null,
            d.derived_text_key = $derived_text_key,
            d.updated_at = $now
        RETURN d.id
        """
        params = {
            "owner_id": owner_id,
            "claim_id": claim_id,
            "document_id": document_id,
            "extraction_json": extraction_json,
            "document_type": document_type,
            "summary": summary,
            "status": status,
            "derived_text_key": derived_text_key,
            "now": now,
        }
        rows = self._execute(query, params)
        return bool(rows and rows[0])
