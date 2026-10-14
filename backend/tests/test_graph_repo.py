from unittest.mock import MagicMock

import pytest
from falkordb import Node

from app.graph.claim_repo import ClaimRepository
from app.graph.document_repo import DocumentRepository


class MockQueryResult:
    def __init__(self, result_set):
        self.result_set = result_set


@pytest.fixture
def mock_graph():
    graph = MagicMock()
    return graph


def test_claim_repo_enforces_owner_scope(mock_graph):
    # Setup mock node return
    claim_node = Node(
        node_id=1,
        labels=["Claim"],
        properties={
            "id": "claim-101",
            "owner_id": "owner-user-a",
            "title": "Legitimate Claim Title",
            "status": "OPEN",
        },
    )
    mock_graph.query.return_value = MockQueryResult([[claim_node]])

    repo = ClaimRepository(graph=mock_graph)
    claim = repo.get_claim(owner_id="owner-user-a", claim_id="claim-101")

    assert claim is not None
    assert claim["id"] == "claim-101"
    assert claim["owner_id"] == "owner-user-a"

    # Verify query was called with strict parameterized owner_id
    call_args = mock_graph.query.call_args
    query_str, params = call_args[0]
    assert "$owner_id" in query_str
    assert "$claim_id" in query_str
    assert params["owner_id"] == "owner-user-a"
    assert params["claim_id"] == "claim-101"


def test_cypher_injection_attempt_is_safely_parameterized(mock_graph):
    injection_title = "'); MATCH (n) DETACH DELETE n; //"
    claim_node = Node(
        node_id=2,
        labels=["Claim"],
        properties={
            "id": "claim-injection-test",
            "owner_id": "owner-123",
            "title": injection_title,
            "status": "OPEN",
        },
    )
    mock_graph.query.return_value = MockQueryResult([[claim_node]])

    repo = ClaimRepository(graph=mock_graph)
    created = repo.create_claim(
        owner_id="owner-123",
        claim_data={
            "id": "claim-injection-test",
            "title": injection_title,
            "description": "Test injection defense",
        },
    )

    assert created["title"] == injection_title

    # Crucial assertion: injection string is strictly a dictionary param, NOT string-interpolated into Cypher
    call_args = mock_graph.query.call_args
    query_str, params = call_args[0]
    assert injection_title not in query_str
    assert params["title"] == injection_title
    assert params["owner_id"] == "owner-123"


def test_document_repo_duplicate_detection_enforces_owner_and_claim_scope(mock_graph):
    doc_node = Node(
        node_id=3,
        labels=["Document"],
        properties={
            "id": "doc-uuid-1",
            "claim_id": "claim-1",
            "owner_id": "owner-user-a",
            "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "status": "STORED",
        },
    )
    mock_graph.query.return_value = MockQueryResult([[doc_node]])

    repo = DocumentRepository(graph=mock_graph)
    duplicate = repo.find_document_by_content_hash(
        owner_id="owner-user-a",
        claim_id="claim-1",
        content_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    )

    assert duplicate is not None
    assert duplicate["content_hash"] == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    call_args = mock_graph.query.call_args
    query_str, params = call_args[0]
    # Enforces owner, claim containment, and content_hash inside query
    assert "$owner_id" in query_str
    assert "$claim_id" in query_str
    assert "$content_hash" in query_str
    assert params["owner_id"] == "owner-user-a"
    assert params["claim_id"] == "claim-1"


def test_document_repo_soft_delete(mock_graph):
    mock_graph.query.return_value = MockQueryResult([["doc-uuid-1"]])

    repo = DocumentRepository(graph=mock_graph)
    success = repo.soft_delete_document(
        owner_id="owner-user-a",
        claim_id="claim-1",
        document_id="doc-uuid-1",
    )

    assert success is True
    call_args = mock_graph.query.call_args
    query_str, params = call_args[0]
    assert "SET d.status = 'ARCHIVED'" in query_str
    assert params["owner_id"] == "owner-user-a"
    assert params["claim_id"] == "claim-1"
    assert params["document_id"] == "doc-uuid-1"
