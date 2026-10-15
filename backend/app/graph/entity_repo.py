import uuid
from datetime import UTC, datetime
from typing import Any

from app.graph.base_repo import BaseGraphRepository


class EntityRepository(BaseGraphRepository):
    """FalkorDB repository for Person, Organization, and Vehicle entity nodes and relationships.

    Guarantees strict multi-tenant boundary isolation scoped by owner_id and claim_id.
    """

    def upsert_person(
        self,
        owner_id: str,
        claim_id: str,
        name: str,
        role: str = "other",
        document_id: str | None = None,
    ) -> dict[str, Any]:
        """Creates or updates a Person node linked to the claim and optionally to the source document."""
        clean_name = name.strip()
        now = datetime.now(UTC).isoformat()
        person_id = str(uuid.uuid4())

        query = """
        MATCH (u:User {id: $owner_id})-[:OWNS]->(c:Claim {id: $claim_id, owner_id: $owner_id})
        MERGE (p:Person {owner_id: $owner_id, claim_id: $claim_id, name: $name})
        ON CREATE SET
            p.id = $person_id,
            p.role = $role,
            p.created_at = $now,
            p.updated_at = $now,
            p.schema_version = $schema_version
        ON MATCH SET
            p.role = CASE WHEN p.role = 'other' THEN $role ELSE p.role END,
            p.updated_at = $now
        MERGE (c)-[:INVOLVES_PERSON]->(p)
        WITH p, c
        OPTIONAL MATCH (d:Document {id: $document_id, owner_id: $owner_id, claim_id: $claim_id})
        FOREACH (_ IN CASE WHEN d IS NOT NULL THEN [1] ELSE [] END |
            MERGE (d)-[:MENTIONS]->(p)
        )
        RETURN p
        """
        params = {
            "owner_id": owner_id,
            "claim_id": claim_id,
            "name": clean_name,
            "role": role,
            "person_id": person_id,
            "document_id": document_id,
            "now": now,
            "schema_version": self.SCHEMA_VERSION,
        }
        rows = self._execute(query, params)
        if not rows or not rows[0]:
            raise RuntimeError(f"Claim {claim_id} not found for owner or Person creation failed")
        return self._node_to_dict(rows[0][0])

    def upsert_organization(
        self,
        owner_id: str,
        claim_id: str,
        name: str,
        org_type: str = "other",
        document_id: str | None = None,
    ) -> dict[str, Any]:
        """Creates or updates an Organization node linked to the claim and optionally to the source document."""
        clean_name = name.strip()
        now = datetime.now(UTC).isoformat()
        org_id = str(uuid.uuid4())

        query = """
        MATCH (u:User {id: $owner_id})-[:OWNS]->(c:Claim {id: $claim_id, owner_id: $owner_id})
        MERGE (o:Organization {owner_id: $owner_id, claim_id: $claim_id, name: $name})
        ON CREATE SET
            o.id = $org_id,
            o.org_type = $org_type,
            o.created_at = $now,
            o.updated_at = $now,
            o.schema_version = $schema_version
        ON MATCH SET
            o.org_type = CASE WHEN o.org_type = 'other' THEN $org_type ELSE o.org_type END,
            o.updated_at = $now
        MERGE (c)-[:INVOLVES_ORGANIZATION]->(o)
        WITH o, c
        OPTIONAL MATCH (d:Document {id: $document_id, owner_id: $owner_id, claim_id: $claim_id})
        FOREACH (_ IN CASE WHEN d IS NOT NULL THEN [1] ELSE [] END |
            MERGE (d)-[:MENTIONS]->(o)
        )
        RETURN o
        """
        params = {
            "owner_id": owner_id,
            "claim_id": claim_id,
            "name": clean_name,
            "org_type": org_type,
            "org_id": org_id,
            "document_id": document_id,
            "now": now,
            "schema_version": self.SCHEMA_VERSION,
        }
        rows = self._execute(query, params)
        if not rows or not rows[0]:
            raise RuntimeError(f"Claim {claim_id} not found for owner or Organization creation failed")
        return self._node_to_dict(rows[0][0])

    def link_person_to_organization(
        self,
        owner_id: str,
        claim_id: str,
        person_name: str,
        org_name: str,
    ) -> bool:
        """Links a Person to an Organization via an AFFILIATED_WITH edge with strict owner containment."""
        now = datetime.now(UTC).isoformat()
        query = """
        MATCH (u:User {id: $owner_id})-[:OWNS]->(c:Claim {id: $claim_id, owner_id: $owner_id})
        MATCH (p:Person {owner_id: $owner_id, claim_id: $claim_id, name: $person_name})
        MATCH (o:Organization {owner_id: $owner_id, claim_id: $claim_id, name: $org_name})
        MERGE (p)-[r:AFFILIATED_WITH]->(o)
        ON CREATE SET r.created_at = $now
        RETURN r
        """
        params = {
            "owner_id": owner_id,
            "claim_id": claim_id,
            "person_name": person_name.strip(),
            "org_name": org_name.strip(),
            "now": now,
        }
        rows = self._execute(query, params)
        return bool(rows and rows[0])

    def get_claim_entities(
        self,
        owner_id: str,
        claim_id: str,
    ) -> dict[str, list[dict[str, Any]]]:
        """Retrieves all domain entities linked to a specific claim owned by the user."""
        persons_query = """
        MATCH (u:User {id: $owner_id})-[:OWNS]->(c:Claim {id: $claim_id, owner_id: $owner_id})-[:INVOLVES_PERSON]->(p:Person {owner_id: $owner_id})
        RETURN p
        ORDER BY p.name ASC
        """
        params = {"owner_id": owner_id, "claim_id": claim_id}
        person_rows = self._execute(persons_query, params)
        persons = [self._node_to_dict(r[0]) for r in person_rows if r and r[0]]

        orgs_query = """
        MATCH (u:User {id: $owner_id})-[:OWNS]->(c:Claim {id: $claim_id, owner_id: $owner_id})-[:INVOLVES_ORGANIZATION]->(o:Organization {owner_id: $owner_id})
        RETURN o
        ORDER BY o.name ASC
        """
        org_rows = self._execute(orgs_query, params)
        organizations = [self._node_to_dict(r[0]) for r in org_rows if r and r[0]]

        return {
            "persons": persons,
            "organizations": organizations,
        }


entity_repo = EntityRepository()
