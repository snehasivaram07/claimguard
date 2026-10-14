import uuid
from datetime import UTC, datetime
from typing import Any

from app.graph.base_repo import BaseGraphRepository


class ClaimRepository(BaseGraphRepository):
    """FalkorDB repository for Claim nodes and (:User)-[:OWNS]->(:Claim) relationships.

    All Cypher queries are strictly parameterized and owner-scoped.
    """

    def create_claim(self, owner_id: str, claim_data: dict[str, Any]) -> dict[str, Any]:
        """Creates a Claim node and links it to the authenticated User."""
        now = datetime.now(UTC).isoformat()
        claim_id = claim_data.get("id") or str(uuid.uuid4())

        query = """
        MERGE (u:User {id: $owner_id})
        ON CREATE SET
            u.owner_id = $owner_id,
            u.created_at = $now,
            u.updated_at = $now,
            u.status = 'ACTIVE',
            u.schema_version = $schema_version
        CREATE (c:Claim {
            id: $claim_id,
            owner_id: $owner_id,
            title: $title,
            claim_type: $claim_type,
            claim_number: $claim_number,
            policy_number: $policy_number,
            description: $description,
            status: $status,
            created_at: $now,
            updated_at: $now,
            schema_version: $schema_version
        })
        CREATE (u)-[:OWNS]->(c)
        RETURN c
        """

        params = {
            "owner_id": owner_id,
            "claim_id": claim_id,
            "title": claim_data.get("title", ""),
            "claim_type": claim_data.get("claim_type", "GENERAL"),
            "claim_number": claim_data.get("claim_number"),
            "policy_number": claim_data.get("policy_number"),
            "description": claim_data.get("description", ""),
            "status": claim_data.get("status", "OPEN"),
            "now": now,
            "schema_version": self.SCHEMA_VERSION,
        }

        rows = self._execute(query, params)
        if not rows or not rows[0]:
            raise RuntimeError("Failed to create Claim node in graph")

        return self._node_to_dict(rows[0][0])

    def get_claim(self, owner_id: str, claim_id: str) -> dict[str, Any] | None:
        """Retrieves a single claim by ID, strictly enforcing owner isolation."""
        query = """
        MATCH (u:User {id: $owner_id})-[:OWNS]->(c:Claim {id: $claim_id, owner_id: $owner_id})
        RETURN c
        """
        params = {"owner_id": owner_id, "claim_id": claim_id}
        rows = self._execute(query, params)
        if not rows or not rows[0]:
            return None
        return self._node_to_dict(rows[0][0])

    def list_claims(
        self,
        owner_id: str,
        skip: int = 0,
        limit: int = 50,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        """Lists claims belonging exclusively to the owner, excluding archived by default."""
        query = """
        MATCH (u:User {id: $owner_id})-[:OWNS]->(c:Claim {owner_id: $owner_id})
        WHERE ($include_archived = true OR c.status <> 'ARCHIVED')
        RETURN c
        ORDER BY c.created_at DESC
        SKIP $skip
        LIMIT $limit
        """
        params = {
            "owner_id": owner_id,
            "include_archived": include_archived,
            "skip": skip,
            "limit": limit,
        }
        rows = self._execute(query, params)
        return [self._node_to_dict(row[0]) for row in rows if row and row[0]]

    def count_claims(self, owner_id: str, include_archived: bool = False) -> int:
        """Returns the total number of claims for pagination metadata."""
        query = """
        MATCH (u:User {id: $owner_id})-[:OWNS]->(c:Claim {owner_id: $owner_id})
        WHERE ($include_archived = true OR c.status <> 'ARCHIVED')
        RETURN count(c) AS total
        """
        params = {
            "owner_id": owner_id,
            "include_archived": include_archived,
        }
        rows = self._execute(query, params)
        if rows and rows[0]:
            return int(rows[0][0])
        return 0

    def update_claim(
        self,
        owner_id: str,
        claim_id: str,
        updates: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Updates editable claim fields while maintaining owner scoping."""
        # Sanitize updates to prevent overwriting immutable tenant/system properties
        disallowed = {"id", "owner_id", "created_at", "schema_version"}
        sanitized_updates = {k: v for k, v in updates.items() if k not in disallowed and v is not None}

        if not sanitized_updates:
            return self.get_claim(owner_id, claim_id)

        now = datetime.now(UTC).isoformat()
        query = """
        MATCH (u:User {id: $owner_id})-[:OWNS]->(c:Claim {id: $claim_id, owner_id: $owner_id})
        SET c += $updates, c.updated_at = $now
        RETURN c
        """
        params = {
            "owner_id": owner_id,
            "claim_id": claim_id,
            "updates": sanitized_updates,
            "now": now,
        }
        rows = self._execute(query, params)
        if not rows or not rows[0]:
            return None
        return self._node_to_dict(rows[0][0])

    def soft_delete_claim(self, owner_id: str, claim_id: str) -> bool:
        """Marks a claim as ARCHIVED (soft delete), never removing nodes destructively."""
        now = datetime.now(UTC).isoformat()
        query = """
        MATCH (u:User {id: $owner_id})-[:OWNS]->(c:Claim {id: $claim_id, owner_id: $owner_id})
        SET c.status = 'ARCHIVED', c.updated_at = $now
        RETURN c.id
        """
        params = {
            "owner_id": owner_id,
            "claim_id": claim_id,
            "now": now,
        }
        rows = self._execute(query, params)
        return bool(rows and rows[0])
