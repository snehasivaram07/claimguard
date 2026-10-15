from unittest.mock import MagicMock

import pytest

from app.graph.entity_repo import EntityRepository


def test_upsert_person_cypher_isolation():
    mock_execute = MagicMock(return_value=[[{"id": "p-1", "name": "Dr. Sarah Connor", "role": "physician"}]])
    repo = EntityRepository()
    repo._execute = mock_execute

    result = repo.upsert_person(
        owner_id="owner-123",
        claim_id="claim-456",
        name="Dr. Sarah Connor",
        role="physician",
        document_id="doc-789",
    )

    assert result["id"] == "p-1"
    assert result["name"] == "Dr. Sarah Connor"
    query, params = mock_execute.call_args[0]
    assert "MATCH (u:User {id: $owner_id})-[:OWNS]->(c:Claim {id: $claim_id, owner_id: $owner_id})" in query
    assert "MERGE (p:Person {owner_id: $owner_id, claim_id: $claim_id, name: $name})" in query
    assert "MERGE (d)-[:MENTIONS]->(p)" in query
    assert params["owner_id"] == "owner-123"
    assert params["claim_id"] == "claim-456"
    assert params["document_id"] == "doc-789"


def test_upsert_organization_cypher_isolation():
    mock_execute = MagicMock(return_value=[[{"id": "org-1", "name": "General Hospital", "org_type": "hospital"}]])
    repo = EntityRepository()
    repo._execute = mock_execute

    result = repo.upsert_organization(
        owner_id="owner-123",
        claim_id="claim-456",
        name="General Hospital",
        org_type="hospital",
        document_id="doc-789",
    )

    assert result["id"] == "org-1"
    query, params = mock_execute.call_args[0]
    assert "MATCH (u:User {id: $owner_id})-[:OWNS]->(c:Claim {id: $claim_id, owner_id: $owner_id})" in query
    assert "MERGE (o:Organization {owner_id: $owner_id, claim_id: $claim_id, name: $name})" in query
    assert params["owner_id"] == "owner-123"
    assert params["org_type"] == "hospital"


def test_link_person_to_organization():
    mock_execute = MagicMock(return_value=[[{"created_at": "2026-10-15T00:00:00Z"}]])
    repo = EntityRepository()
    repo._execute = mock_execute

    linked = repo.link_person_to_organization(
        owner_id="owner-123",
        claim_id="claim-456",
        person_name="Dr. Sarah Connor",
        org_name="General Hospital",
    )

    assert linked is True
    query, params = mock_execute.call_args[0]
    assert "MATCH (u:User {id: $owner_id})-[:OWNS]->(c:Claim {id: $claim_id, owner_id: $owner_id})" in query
    assert "MATCH (p:Person {owner_id: $owner_id, claim_id: $claim_id, name: $person_name})" in query
    assert "MATCH (o:Organization {owner_id: $owner_id, claim_id: $claim_id, name: $org_name})" in query
    assert "MERGE (p)-[r:AFFILIATED_WITH]->(o)" in query


def test_get_claim_entities():
    repo = EntityRepository()
    # Mocking first call for persons, second call for organizations
    repo._execute = MagicMock(
        side_effect=[
            [[{"name": "Alice", "role": "claimant"}]],
            [[{"name": "Apex Repair", "org_type": "repairer"}]],
        ]
    )

    entities = repo.get_claim_entities(owner_id="owner-123", claim_id="claim-456")
    assert len(entities["persons"]) == 1
    assert entities["persons"][0]["name"] == "Alice"
    assert len(entities["organizations"]) == 1
    assert entities["organizations"][0]["name"] == "Apex Repair"


def test_upsert_person_claim_not_found_raises():
    mock_execute = MagicMock(return_value=[])
    repo = EntityRepository()
    repo._execute = mock_execute

    with pytest.raises(RuntimeError) as exc_info:
        repo.upsert_person(
            owner_id="owner-foreign",
            claim_id="claim-none",
            name="Ghost",
        )
    assert "not found for owner" in str(exc_info.value)
