import json
from datetime import UTC, datetime
from typing import Any

from app.core.config import settings
from app.core.logging import logger
from app.graph.claim_repo import ClaimRepository
from app.graph.fraud_repo import FraudRepository, fraud_repo
from app.inference.client import NebiusTokenFactoryClient, inference_client
from app.inference.output_parser import clean_json_text
from app.inference.prompts.fraud_ring_v1 import (
    FRAUD_RING_SYSTEM_PROMPT,
    build_fraud_ring_user_prompt,
)
from app.inference.router import ModelRouter, TaskType, model_router
from app.schemas.fraud_ring import (
    ClaimFraudNetworkResponse,
    FraudRingAnalysisV1,
    FraudRingEdge,
    FraudRingNode,
    FraudRingPattern,
    FraudRingSeverity,
    SharedEntitySummary,
)


class FraudRingService:
    """Orchestrates graph network extraction, topological collusion detection, and Nemotron Ultra synthesis."""

    def __init__(
        self,
        fraud_repository: FraudRepository | None = None,
        claim_repository: ClaimRepository | None = None,
        client: NebiusTokenFactoryClient | None = None,
        router: ModelRouter | None = None,
    ):
        self._fraud_repo = fraud_repository
        self._claim_repo = claim_repository
        self._client = client
        self._router = router

    @property
    def fraud_repo(self) -> FraudRepository:
        if self._fraud_repo is None:
            self._fraud_repo = fraud_repo
        return self._fraud_repo

    @property
    def claim_repo(self) -> ClaimRepository:
        if self._claim_repo is None:
            self._claim_repo = ClaimRepository()
        return self._claim_repo

    @property
    def client(self) -> NebiusTokenFactoryClient:
        if self._client is None:
            return inference_client
        return self._client

    @property
    def router(self) -> ModelRouter:
        if self._router is None:
            return model_router
        return self._router

    async def get_claim_network(
        self,
        owner_id: str,
        claim_id: str,
        max_hops: int | None = None,
    ) -> ClaimFraudNetworkResponse:
        """Retrieves visual network graph of a claim and any associated fraud rings."""
        hops = max_hops or settings.FRAUD_RING_MAX_HOPS
        network_data = self.fraud_repo.get_claim_network(
            owner_id=owner_id,
            claim_id=claim_id,
            max_hops=hops,
        )

        nodes = [FraudRingNode.model_validate(n) for n in network_data.get("nodes", [])]
        edges = [FraudRingEdge.model_validate(e) for e in network_data.get("edges", [])]

        # Check if this claim participates in any detected rings
        all_rings = await self.detect_fraud_rings(owner_id=owner_id)
        matching_rings = [ring for ring in all_rings if claim_id in ring.claim_ids]

        return ClaimFraudNetworkResponse(
            claim_id=claim_id,
            nodes=nodes,
            edges=edges,
            fraud_rings=matching_rings,
            node_count=len(nodes),
            edge_count=len(edges),
        )

    async def detect_fraud_rings(
        self,
        owner_id: str,
        min_shared: int | None = None,
    ) -> list[FraudRingAnalysisV1]:
        """Identifies and evaluates all suspicious multi-claim collusion clusters for a tenant."""
        threshold = min_shared or settings.FRAUD_RING_MIN_SHARED_ENTITIES
        clusters = self.fraud_repo.find_shared_entity_clusters(owner_id=owner_id, min_shared=threshold)
        if not clusters:
            return []

        patterns = self.fraud_repo.detect_suspicious_patterns(owner_id=owner_id)
        now = datetime.now(UTC).isoformat()
        results: list[FraudRingAnalysisV1] = []

        for cluster in clusters:
            ring_id = cluster["cluster_id"]
            shared_entities_raw = cluster.get("shared_entities", [])
            claim_ids = cluster.get("claim_ids", [])

            # Match any patterns relevant to claims in this cluster
            cluster_patterns = [
                p for p in patterns if any(cid in claim_ids for cid in p.get("claim_ids", []))
            ]

            shared_summary = [
                SharedEntitySummary(
                    name=e["name"],
                    entity_type=e["entity_type"],
                    claim_count=e["claim_count"],
                    roles=e.get("roles", []),
                )
                for e in shared_entities_raw
            ]

            if settings.INFERENCE_ENABLED:
                try:
                    ring_analysis = await self._synthesize_with_nemotron(
                        ring_id=ring_id,
                        claim_ids=claim_ids,
                        shared_summary=shared_summary,
                        cluster_patterns=cluster_patterns,
                        now=now,
                    )
                    results.append(ring_analysis)
                    continue
                except Exception as exc:
                    logger.warning(
                        "Nemotron Ultra fraud ring synthesis failed, falling back to heuristic: %s",
                        exc,
                    )

            # Heuristic synthesis fallback
            heuristic_analysis = self._heuristic_synthesis(
                ring_id=ring_id,
                claim_ids=claim_ids,
                shared_summary=shared_summary,
                cluster_patterns=cluster_patterns,
                now=now,
            )
            results.append(heuristic_analysis)

        # Sort by risk score descending
        results.sort(key=lambda r: r.risk_score, reverse=True)
        return results

    async def _synthesize_with_nemotron(
        self,
        ring_id: str,
        claim_ids: list[str],
        shared_summary: list[SharedEntitySummary],
        cluster_patterns: list[dict[str, Any]],
        now: str,
    ) -> FraudRingAnalysisV1:
        """Invokes Nemotron Ultra via Nebius Token Factory for deep forensic syndicate reasoning."""
        model_name = self.router.resolve_model(TaskType.FRAUD_RING_ANALYSIS)
        user_prompt = build_fraud_ring_user_prompt(
            ring_id=ring_id,
            claims=[{"id": cid} for cid in claim_ids],
            shared_entities=[e.model_dump() for e in shared_summary],
            suspicious_patterns=cluster_patterns,
        )

        messages = [
            {"role": "system", "content": FRAUD_RING_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        response = await self.client.chat_completion(
            messages=messages,
            model=model_name,
            temperature=0.0,
        )

        raw_output = response["choices"][0]["message"]["content"]
        cleaned_json = clean_json_text(raw_output)
        data = json.loads(cleaned_json)

        data["ring_id"] = ring_id
        data["claim_ids"] = claim_ids
        data["shared_entities"] = [e.model_dump() for e in shared_summary]
        data["detected_at"] = now

        return FraudRingAnalysisV1.model_validate(data)

    def _heuristic_synthesis(
        self,
        ring_id: str,
        claim_ids: list[str],
        shared_summary: list[SharedEntitySummary],
        cluster_patterns: list[dict[str, Any]],
        now: str,
    ) -> FraudRingAnalysisV1:
        """Deterministic heuristic evaluation when LLM inference is disabled or during tests."""
        num_shared = len(shared_summary)
        num_claims = len(claim_ids)

        has_role_reversal = any(p["pattern_type"] == "ROLE_REVERSAL" for p in cluster_patterns)
        has_provider = any(
            e.entity_type == "organization" or any(r in ("physician", "repairer", "body_shop") for r in e.roles)
            for e in shared_summary
        )

        if has_role_reversal:
            pattern = FraudRingPattern.ROLE_REVERSAL_NETWORK
            title = f"Role-Reversal Network across {num_claims} claims"
        elif has_provider:
            pattern = FraudRingPattern.PROVIDER_FRAUD_COLLUSION
            title = f"Collusive Provider Ring involving {num_claims} claims"
        elif num_claims >= 4:
            pattern = FraudRingPattern.REPEAT_CLAIMANT_SYNDICATE
            title = f"Repeat Claimant Syndicate across {num_claims} claims"
        else:
            pattern = FraudRingPattern.STAGED_COLLISION_RING
            title = f"Staged Collision Cluster across {num_claims} claims"

        # Risk score calculation
        risk_score = min(0.98, 0.45 + (num_shared * 0.12) + (num_claims * 0.08))
        if has_role_reversal:
            risk_score = min(0.99, risk_score + 0.15)

        # Severity mapping
        if risk_score >= 0.80:
            severity = FraudRingSeverity.CRITICAL
        elif risk_score >= 0.65:
            severity = FraudRingSeverity.HIGH
        elif risk_score >= 0.50:
            severity = FraudRingSeverity.MEDIUM
        else:
            severity = FraudRingSeverity.LOW

        indicators = [
            f"{num_claims} claims share {num_shared} common entities across multiple losses.",
        ]
        for p in cluster_patterns:
            indicators.append(p.get("description", "Suspicious topological pattern detected."))

        actions = [
            "Issue comprehensive Examination Under Oath (EUO) for all overlapping claimants.",
            "Cross-subpoena repair invoices, medical treatment dates, and bank disbursement records.",
            "Place administrative hold on pending payouts across all connected claim files.",
        ]

        summary = (
            f"Forensic cluster analysis identified {num_claims} interconnected claims sharing {num_shared} "
            f"identities/organizations ({', '.join(e.name for e in shared_summary[:3])}). "
            f"The dense network topology indicates deliberate coordination consistent with a {pattern.value}."
        )

        return FraudRingAnalysisV1(
            ring_id=ring_id,
            pattern=pattern,
            severity=severity,
            risk_score=round(risk_score, 2),
            title=title,
            summary=summary,
            claim_ids=claim_ids,
            shared_entities=shared_summary,
            suspicious_indicators=indicators,
            recommended_siu_actions=actions,
            detected_at=now,
        )


fraud_ring_service = FraudRingService()
