from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class FraudRingSeverity(StrEnum):
    """Risk severity classification for detected fraud rings and collusion clusters."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FraudRingPattern(StrEnum):
    """Categorization of organized insurance fraud topologies."""

    STAGED_COLLISION_RING = "staged_collision_ring"
    PROVIDER_FRAUD_COLLUSION = "provider_fraud_collusion"
    REPEAT_CLAIMANT_SYNDICATE = "repeat_claimant_syndicate"
    ROLE_REVERSAL_NETWORK = "role_reversal_network"
    IDENTITY_SHARING_CLUSTER = "identity_sharing_cluster"
    OTHER = "other"


class FraudRingNode(BaseModel):
    """Graph node representation formatted for visual UI rendering (Cytoscape / D3)."""

    id: str
    label: str
    type: str  # "claim", "person", "organization"
    is_target: bool | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class FraudRingEdge(BaseModel):
    """Graph edge representation connecting claims and entities."""

    source: str
    target: str
    type: str  # "INVOLVES_PERSON", "INVOLVES_ORGANIZATION", "AFFILIATED_WITH"
    properties: dict[str, Any] = Field(default_factory=dict)


class SharedEntitySummary(BaseModel):
    """Summary of an entity participating across multiple claims."""

    name: str
    entity_type: str
    claim_count: int
    roles: list[str] = Field(default_factory=list)


class FraudRingAnalysisV1(BaseModel):
    """Detailed forensic analysis and SIU action plan for an identified fraud ring."""

    ring_id: str
    pattern: FraudRingPattern
    severity: FraudRingSeverity
    risk_score: float = Field(..., ge=0.0, le=1.0)
    title: str
    summary: str
    claim_ids: list[str] = Field(default_factory=list)
    shared_entities: list[SharedEntitySummary] = Field(default_factory=list)
    suspicious_indicators: list[str] = Field(default_factory=list)
    recommended_siu_actions: list[str] = Field(default_factory=list)
    detected_at: str | None = None
    network_subgraph: dict[str, Any] | None = None


class ClaimFraudNetworkResponse(BaseModel):
    """Visual network graph and fraud ring findings for a specific claim."""

    claim_id: str
    nodes: list[FraudRingNode] = Field(default_factory=list)
    edges: list[FraudRingEdge] = Field(default_factory=list)
    fraud_rings: list[FraudRingAnalysisV1] = Field(default_factory=list)
    node_count: int = 0
    edge_count: int = 0


class FraudRingListResponse(BaseModel):
    """Paginated list of all fraud rings detected in the tenant graph."""

    rings: list[FraudRingAnalysisV1] = Field(default_factory=list)
    total: int = 0
