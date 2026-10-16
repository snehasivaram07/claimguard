from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.config import settings
from app.core.errors import NotFoundError
from app.graph.claim_repo import ClaimRepository
from app.graph.fraud_repo import FraudRepository
from app.inference.client import NebiusTokenFactoryClient
from app.inference.router import ModelRouter
from app.schemas.fraud_ring import (
    ClaimFraudNetworkResponse,
    FraudRingPattern,
    FraudRingSeverity,
)
from app.services.fraud_ring_service import FraudRingService


@pytest.fixture
def mock_fraud_repo():
    repo = MagicMock(spec=FraudRepository)
    return repo


@pytest.fixture
def mock_claim_repo():
    repo = MagicMock(spec=ClaimRepository)
    return repo


@pytest.fixture
def mock_inference_client():
    client = MagicMock(spec=NebiusTokenFactoryClient)
    client.chat_completion = AsyncMock()
    return client


@pytest.fixture
def mock_router():
    router = MagicMock(spec=ModelRouter)
    router.resolve_model.return_value = "nvidia/nemotron-3-ultra"
    return router


@pytest.mark.asyncio
async def test_get_claim_network_success(mock_fraud_repo, mock_claim_repo, mock_inference_client, mock_router):
    service = FraudRingService(
        fraud_repository=mock_fraud_repo,
        claim_repository=mock_claim_repo,
        client=mock_inference_client,
        router=mock_router,
    )

    mock_fraud_repo.get_claim_network.return_value = {
        "claim_id": "c-100",
        "nodes": [
            {"id": "c-100", "label": "Claim 100", "type": "claim", "is_target": True, "properties": {}},
            {"id": "p-1", "label": "Alice", "type": "person", "is_target": False, "properties": {}},
        ],
        "edges": [
            {"source": "c-100", "target": "p-1", "type": "INVOLVES_PERSON", "properties": {}},
        ],
    }
    mock_fraud_repo.find_shared_entity_clusters.return_value = []

    res = await service.get_claim_network(owner_id="user-1", claim_id="c-100")

    assert isinstance(res, ClaimFraudNetworkResponse)
    assert res.claim_id == "c-100"
    assert res.node_count == 2
    assert res.edge_count == 1
    assert len(res.nodes) == 2
    assert res.nodes[0].id == "c-100"
    assert res.nodes[0].is_target is True


@pytest.mark.asyncio
async def test_get_claim_network_not_found(mock_fraud_repo, mock_claim_repo):
    service = FraudRingService(
        fraud_repository=mock_fraud_repo,
        claim_repository=mock_claim_repo,
    )
    mock_fraud_repo.get_claim_network.side_effect = NotFoundError("Claim c-999 not found")

    with pytest.raises(NotFoundError):
        await service.get_claim_network(owner_id="user-1", claim_id="c-999")


@pytest.mark.asyncio
async def test_detect_fraud_rings_empty_when_no_clusters(mock_fraud_repo):
    service = FraudRingService(fraud_repository=mock_fraud_repo)
    mock_fraud_repo.find_shared_entity_clusters.return_value = []

    rings = await service.detect_fraud_rings(owner_id="user-1")
    assert rings == []


@pytest.mark.asyncio
async def test_detect_fraud_rings_heuristic_synthesis_role_reversal(mock_fraud_repo):
    service = FraudRingService(fraud_repository=mock_fraud_repo)

    mock_fraud_repo.find_shared_entity_clusters.return_value = [
        {
            "cluster_id": "ring-1234",
            "claim_ids": ["c-1", "c-2", "c-3"],
            "claims_count": 3,
            "shared_entities": [
                {"name": "John Doe", "entity_type": "person", "claim_count": 3, "roles": ["claimant", "witness"]},
                {"name": "Apex Collision", "entity_type": "organization", "claim_count": 2, "roles": ["body_shop"]},
            ],
            "shared_entity_count": 2,
        }
    ]
    mock_fraud_repo.detect_suspicious_patterns.return_value = [
        {
            "pattern_type": "ROLE_REVERSAL",
            "entity_name": "John Doe",
            "claim_ids": ["c-1", "c-2"],
            "description": "John Doe shifts from claimant to witness across claims.",
        }
    ]

    rings = await service.detect_fraud_rings(owner_id="user-1")
    assert len(rings) == 1
    ring = rings[0]
    assert ring.ring_id == "ring-1234"
    assert ring.pattern == FraudRingPattern.ROLE_REVERSAL_NETWORK
    assert ring.severity in (FraudRingSeverity.CRITICAL, FraudRingSeverity.HIGH)
    assert ring.risk_score >= 0.7
    assert len(ring.claim_ids) == 3
    assert len(ring.shared_entities) == 2
    assert len(ring.recommended_siu_actions) >= 1


@pytest.mark.asyncio
async def test_detect_fraud_rings_heuristic_synthesis_provider_fraud(mock_fraud_repo):
    service = FraudRingService(fraud_repository=mock_fraud_repo)

    mock_fraud_repo.find_shared_entity_clusters.return_value = [
        {
            "cluster_id": "ring-5678",
            "claim_ids": ["c-10", "c-11"],
            "claims_count": 2,
            "shared_entities": [
                {"name": "Metro Urgent Care", "entity_type": "organization", "claim_count": 2, "roles": ["clinic"]},
                {"name": "Quick Fix Auto", "entity_type": "organization", "claim_count": 2, "roles": ["body_shop"]},
            ],
            "shared_entity_count": 2,
        }
    ]
    mock_fraud_repo.detect_suspicious_patterns.return_value = []

    rings = await service.detect_fraud_rings(owner_id="user-1")
    assert len(rings) == 1
    ring = rings[0]
    assert ring.pattern == FraudRingPattern.PROVIDER_FRAUD_COLLUSION
    assert "Provider" in ring.title


@pytest.mark.asyncio
async def test_detect_fraud_rings_nemotron_synthesis(
    mock_fraud_repo,
    mock_inference_client,
    mock_router,
    monkeypatch,
):
    monkeypatch.setattr(settings, "INFERENCE_ENABLED", True)

    service = FraudRingService(
        fraud_repository=mock_fraud_repo,
        client=mock_inference_client,
        router=mock_router,
    )

    mock_fraud_repo.find_shared_entity_clusters.return_value = [
        {
            "cluster_id": "ring-9999",
            "claim_ids": ["c-5", "c-6"],
            "claims_count": 2,
            "shared_entities": [
                {"name": "Syndicate Lead", "entity_type": "person", "claim_count": 2, "roles": ["claimant"]},
            ],
            "shared_entity_count": 1,
        }
    ]
    mock_fraud_repo.detect_suspicious_patterns.return_value = []

    mock_inference_client.chat_completion.return_value = {
        "choices": [
            {
                "message": {
                    "content": """{
                        "pattern": "staged_collision_ring",
                        "severity": "critical",
                        "risk_score": 0.95,
                        "title": "Coordinated Staged Collisions in Queens",
                        "summary": "Multiple claims orchestrated by the same syndicate leader.",
                        "suspicious_indicators": ["Identical loss mechanics", "Single lead organizer"],
                        "recommended_siu_actions": ["Issue subpoenas", "Schedule EUO"]
                    }"""
                }
            }
        ]
    }

    rings = await service.detect_fraud_rings(owner_id="user-1")
    assert len(rings) == 1
    ring = rings[0]
    assert ring.ring_id == "ring-9999"
    assert ring.pattern == FraudRingPattern.STAGED_COLLISION_RING
    assert ring.risk_score == 0.95
    assert ring.severity == FraudRingSeverity.CRITICAL
    assert ring.title == "Coordinated Staged Collisions in Queens"
