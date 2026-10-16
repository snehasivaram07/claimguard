from unittest.mock import MagicMock

import pytest

from app.core.errors import NotFoundError
from app.graph.fraud_repo import FraudRepository


def test_get_claim_network_success():
    repo = FraudRepository()

    # Sequence of returns for the queries in get_claim_network:
    # 1. Target claim lookup
    # 2. Persons query
    # 3. Organizations query
    # 4. Shared persons query
    # 5. Shared organizations query
    target_claim = {"id": "claim-101", "title": "Kitchen Leak", "claim_number": "CLM-1", "risk_score": 0.5}
    person_1 = {"id": "p-1", "name": "John Doe", "role": "claimant"}
    org_1 = {"id": "o-1", "name": "Rapid Repair", "org_type": "body_shop"}
    c2 = {"id": "claim-102", "title": "Staged Collision", "claim_number": "CLM-2", "risk_score": 0.9}
    person_2 = {"id": "p-2", "name": "John Doe", "role": "witness"}

    def side_effect(query: str, params: dict):
        assert params["owner_id"] == "owner-abc"
        if "INVOLVES_PERSON" in query and "c1" not in query:
            return [[person_1]]
        if "INVOLVES_ORGANIZATION" in query and "c1" not in query:
            return [[org_1]]
        if "WHERE toLower(trim(p1.name)) = toLower(trim(p2.name))" in query:
            return [[c2, person_1, person_2]]
        if "WHERE toLower(trim(o1.name)) = toLower(trim(o2.name))" in query:
            return []
        if "RETURN c" in query:
            return [[target_claim]]
        return []

    repo._execute = MagicMock(side_effect=side_effect)

    network = repo.get_claim_network(owner_id="owner-abc", claim_id="claim-101", max_hops=2)

    assert network["claim_id"] == "claim-101"
    assert network["node_count"] >= 3
    node_ids = {n["id"] for n in network["nodes"]}
    assert "claim-101" in node_ids
    assert "p-1" in node_ids
    assert "o-1" in node_ids
    assert "claim-102" in node_ids

    # Check edges
    edge_types = [e["type"] for e in network["edges"]]
    assert "INVOLVES_PERSON" in edge_types
    assert "INVOLVES_ORGANIZATION" in edge_types


def test_get_claim_network_not_found():
    repo = FraudRepository()
    repo._execute = MagicMock(return_value=[])

    with pytest.raises(NotFoundError):
        repo.get_claim_network(owner_id="owner-abc", claim_id="claim-nonexistent")


def test_find_shared_entity_pairs():
    repo = FraudRepository()

    def side_effect(query: str, params: dict):
        assert params["owner_id"] == "owner-abc"
        if "INVOLVES_PERSON" in query:
            return [["claim-1", "claim-2", "Dr. Robert", "person", "physician", "physician"]]
        if "INVOLVES_ORGANIZATION" in query:
            return [["claim-1", "claim-2", "Apex Collision", "organization", "body_shop", "body_shop"]]
        return []

    repo._execute = MagicMock(side_effect=side_effect)

    pairs = repo.find_shared_entity_pairs(owner_id="owner-abc")
    assert len(pairs) == 2
    assert pairs[0]["entity_name"] == "Dr. Robert"
    assert pairs[0]["entity_type"] == "person"
    assert pairs[1]["entity_name"] == "Apex Collision"
    assert pairs[1]["entity_type"] == "organization"


def test_find_shared_entity_clusters_min_threshold():
    repo = FraudRepository()

    # Mock find_shared_entity_pairs to return 2 shared entities between claim-1 and claim-2,
    # and 2 shared entities between claim-2 and claim-3
    mock_pairs = [
        {"claim_id_1": "claim-1", "claim_id_2": "claim-2", "entity_name": "Dr. Smith", "entity_type": "person", "role_1": "physician", "role_2": "physician"},
        {"claim_id_1": "claim-1", "claim_id_2": "claim-2", "entity_name": "Apex Shop", "entity_type": "organization", "role_1": "body_shop", "role_2": "body_shop"},
        {"claim_id_1": "claim-2", "claim_id_2": "claim-3", "entity_name": "Dr. Smith", "entity_type": "person", "role_1": "physician", "role_2": "physician"},
        {"claim_id_1": "claim-2", "claim_id_2": "claim-3", "entity_name": "Apex Shop", "entity_type": "organization", "role_1": "body_shop", "role_2": "body_shop"},
    ]
    repo.find_shared_entity_pairs = MagicMock(return_value=mock_pairs)

    clusters = repo.find_shared_entity_clusters(owner_id="owner-abc", min_shared=2)
    assert len(clusters) == 1
    cluster = clusters[0]
    assert cluster["claims_count"] == 3
    assert set(cluster["claim_ids"]) == {"claim-1", "claim-2", "claim-3"}
    assert cluster["shared_entity_count"] == 2


def test_detect_suspicious_patterns():
    repo = FraudRepository()

    def side_effect(query: str, params: dict):
        assert params["owner_id"] == "owner-abc"
        if "HIGH_FREQUENCY_HUB" in query or "claim_count >= 3" in query:
            return [["Apex Auto", "organization", 4, ["c1", "c2", "c3", "c4"], ["body_shop"]]]
        if "ROLE_REVERSAL" in query or "size(roles) > 1" in query:
            return [["John Doe", ["claimant", "witness"], ["c1", "c2"]]]
        return []

    repo._execute = MagicMock(side_effect=side_effect)

    findings = repo.detect_suspicious_patterns(owner_id="owner-abc")
    assert len(findings) == 2
    types = [f["pattern_type"] for f in findings]
    assert "HIGH_FREQUENCY_HUB" in types
    assert "ROLE_REVERSAL" in types
