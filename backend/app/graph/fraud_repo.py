import uuid
from typing import Any

from app.core.errors import NotFoundError
from app.graph.base_repo import BaseGraphRepository


class FraudRepository(BaseGraphRepository):
    """FalkorDB repository for fraud ring traversals, shared entity graph analytics, and collusion detection.

    Strictly enforces multi-tenant owner containment across all Cypher queries.
    """

    def get_claim_network(
        self,
        owner_id: str,
        claim_id: str,
        max_hops: int = 2,
    ) -> dict[str, Any]:
        """Retrieves 1-hop and 2-hop graph neighborhood around a claim.

        Returns nodes and edges formatted for visual network graphs and SIU investigation.
        """
        # 1. Verify target claim exists and belongs to requesting owner
        claim_check_query = """
        MATCH (u:User {id: $owner_id})-[:OWNS]->(c:Claim {id: $claim_id, owner_id: $owner_id})
        RETURN c
        """
        claim_rows = self._execute(claim_check_query, {"owner_id": owner_id, "claim_id": claim_id})
        if not claim_rows or not claim_rows[0]:
            raise NotFoundError(f"Claim {claim_id} not found")

        target_claim = self._node_to_dict(claim_rows[0][0])
        nodes: dict[str, dict[str, Any]] = {}
        edges: list[dict[str, Any]] = []

        # Target claim node
        nodes[claim_id] = {
            "id": claim_id,
            "label": target_claim.get("title", f"Claim {claim_id[:8]}"),
            "type": "claim",
            "is_target": True,
            "properties": {
                "claim_number": target_claim.get("claim_number"),
                "status": target_claim.get("status", "OPEN"),
                "risk_score": target_claim.get("risk_score", 0.0),
            },
        }

        # 2. Retrieve 1-hop Persons directly involved in the claim
        persons_query = """
        MATCH (u:User {id: $owner_id})-[:OWNS]->(c:Claim {id: $claim_id, owner_id: $owner_id})
        MATCH (c)-[:INVOLVES_PERSON]->(p:Person {owner_id: $owner_id})
        RETURN p
        """
        person_rows = self._execute(persons_query, {"owner_id": owner_id, "claim_id": claim_id})
        for r in person_rows:
            if not r or not r[0]:
                continue
            p = self._node_to_dict(r[0])
            p_id = p.get("id") or p.get("name")
            nodes[p_id] = {
                "id": p_id,
                "label": p.get("name", "Unknown Person"),
                "type": "person",
                "properties": {
                    "role": p.get("role", "other"),
                    "name": p.get("name"),
                },
            }
            edges.append({
                "source": claim_id,
                "target": p_id,
                "type": "INVOLVES_PERSON",
                "properties": {"role": p.get("role", "other")},
            })

        # 3. Retrieve 1-hop Organizations directly involved in the claim
        orgs_query = """
        MATCH (u:User {id: $owner_id})-[:OWNS]->(c:Claim {id: $claim_id, owner_id: $owner_id})
        MATCH (c)-[:INVOLVES_ORGANIZATION]->(o:Organization {owner_id: $owner_id})
        RETURN o
        """
        org_rows = self._execute(orgs_query, {"owner_id": owner_id, "claim_id": claim_id})
        for r in org_rows:
            if not r or not r[0]:
                continue
            o = self._node_to_dict(r[0])
            o_id = o.get("id") or o.get("name")
            nodes[o_id] = {
                "id": o_id,
                "label": o.get("name", "Unknown Organization"),
                "type": "organization",
                "properties": {
                    "org_type": o.get("org_type", "other"),
                    "name": o.get("name"),
                },
            }
            edges.append({
                "source": claim_id,
                "target": o_id,
                "type": "INVOLVES_ORGANIZATION",
                "properties": {"org_type": o.get("org_type", "other")},
            })

        # 4. If max_hops >= 2, traverse to other claims sharing the same entities
        if max_hops >= 2:
            # Other claims sharing Persons (matched by normalized name within same owner)
            shared_persons_query = """
            MATCH (u:User {id: $owner_id})-[:OWNS]->(c1:Claim {id: $claim_id, owner_id: $owner_id})
            MATCH (u)-[:OWNS]->(c2:Claim {owner_id: $owner_id})
            WHERE c2.id <> $claim_id
            MATCH (c1)-[:INVOLVES_PERSON]->(p1:Person {owner_id: $owner_id})
            MATCH (c2)-[:INVOLVES_PERSON]->(p2:Person {owner_id: $owner_id})
            WHERE toLower(trim(p1.name)) = toLower(trim(p2.name))
            RETURN DISTINCT c2, p1, p2
            """
            shared_p_rows = self._execute(shared_persons_query, {"owner_id": owner_id, "claim_id": claim_id})
            for r in shared_p_rows:
                if not r or len(r) < 3:
                    continue
                c2_dict = self._node_to_dict(r[0])
                p1_dict = self._node_to_dict(r[1])
                p2_dict = self._node_to_dict(r[2])
                c2_id = c2_dict["id"]
                p1_id = p1_dict.get("id") or p1_dict.get("name")

                if c2_id not in nodes:
                    nodes[c2_id] = {
                        "id": c2_id,
                        "label": c2_dict.get("title", f"Claim {c2_id[:8]}"),
                        "type": "claim",
                        "is_target": False,
                        "properties": {
                            "claim_number": c2_dict.get("claim_number"),
                            "status": c2_dict.get("status", "OPEN"),
                            "risk_score": c2_dict.get("risk_score", 0.0),
                        },
                    }

                edges.append({
                    "source": c2_id,
                    "target": p1_id,
                    "type": "INVOLVES_PERSON",
                    "properties": {"role": p2_dict.get("role", "other"), "is_shared": True},
                })

            # Other claims sharing Organizations
            shared_orgs_query = """
            MATCH (u:User {id: $owner_id})-[:OWNS]->(c1:Claim {id: $claim_id, owner_id: $owner_id})
            MATCH (u)-[:OWNS]->(c2:Claim {owner_id: $owner_id})
            WHERE c2.id <> $claim_id
            MATCH (c1)-[:INVOLVES_ORGANIZATION]->(o1:Organization {owner_id: $owner_id})
            MATCH (c2)-[:INVOLVES_ORGANIZATION]->(o2:Organization {owner_id: $owner_id})
            WHERE toLower(trim(o1.name)) = toLower(trim(o2.name))
            RETURN DISTINCT c2, o1, o2
            """
            shared_o_rows = self._execute(shared_orgs_query, {"owner_id": owner_id, "claim_id": claim_id})
            for r in shared_o_rows:
                if not r or len(r) < 3:
                    continue
                c2_dict = self._node_to_dict(r[0])
                o1_dict = self._node_to_dict(r[1])
                o2_dict = self._node_to_dict(r[2])
                c2_id = c2_dict["id"]
                o1_id = o1_dict.get("id") or o1_dict.get("name")

                if c2_id not in nodes:
                    nodes[c2_id] = {
                        "id": c2_id,
                        "label": c2_dict.get("title", f"Claim {c2_id[:8]}"),
                        "type": "claim",
                        "is_target": False,
                        "properties": {
                            "claim_number": c2_dict.get("claim_number"),
                            "status": c2_dict.get("status", "OPEN"),
                            "risk_score": c2_dict.get("risk_score", 0.0),
                        },
                    }

                edges.append({
                    "source": c2_id,
                    "target": o1_id,
                    "type": "INVOLVES_ORGANIZATION",
                    "properties": {"org_type": o2_dict.get("org_type", "other"), "is_shared": True},
                })

        return {
            "claim_id": claim_id,
            "nodes": list(nodes.values()),
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }

    def find_shared_entity_pairs(self, owner_id: str) -> list[dict[str, Any]]:
        """Finds pairs of distinct claims owned by the user that share entities."""
        shared_persons_query = """
        MATCH (u:User {id: $owner_id})-[:OWNS]->(c1:Claim {owner_id: $owner_id})
        MATCH (u)-[:OWNS]->(c2:Claim {owner_id: $owner_id})
        WHERE c1.id < c2.id
        MATCH (c1)-[:INVOLVES_PERSON]->(p1:Person {owner_id: $owner_id})
        MATCH (c2)-[:INVOLVES_PERSON]->(p2:Person {owner_id: $owner_id})
        WHERE toLower(trim(p1.name)) = toLower(trim(p2.name))
        RETURN c1.id, c2.id, p1.name, 'person' AS entity_type, p1.role, p2.role
        """
        rows = self._execute(shared_persons_query, {"owner_id": owner_id})
        results: list[dict[str, Any]] = []

        for r in rows:
            if not r or len(r) < 6:
                continue
            results.append({
                "claim_id_1": r[0],
                "claim_id_2": r[1],
                "entity_name": r[2],
                "entity_type": r[3],
                "role_1": r[4],
                "role_2": r[5],
            })

        shared_orgs_query = """
        MATCH (u:User {id: $owner_id})-[:OWNS]->(c1:Claim {owner_id: $owner_id})
        MATCH (u)-[:OWNS]->(c2:Claim {owner_id: $owner_id})
        WHERE c1.id < c2.id
        MATCH (c1)-[:INVOLVES_ORGANIZATION]->(o1:Organization {owner_id: $owner_id})
        MATCH (c2)-[:INVOLVES_ORGANIZATION]->(o2:Organization {owner_id: $owner_id})
        WHERE toLower(trim(o1.name)) = toLower(trim(o2.name))
        RETURN c1.id, c2.id, o1.name, 'organization' AS entity_type, o1.org_type, o2.org_type
        """
        org_rows = self._execute(shared_orgs_query, {"owner_id": owner_id})
        for r in org_rows:
            if not r or len(r) < 6:
                continue
            results.append({
                "claim_id_1": r[0],
                "claim_id_2": r[1],
                "entity_name": r[2],
                "entity_type": r[3],
                "role_1": r[4],
                "role_2": r[5],
            })

        return results

    def find_shared_entity_clusters(
        self,
        owner_id: str,
        min_shared: int = 2,
    ) -> list[dict[str, Any]]:
        """Groups interconnected claims sharing at least `min_shared` entities into fraud ring clusters."""
        pairs = self.find_shared_entity_pairs(owner_id)
        if not pairs:
            return []

        # Count shared entities between each pair of claims
        pair_shared: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for p in pairs:
            key = (p["claim_id_1"], p["claim_id_2"])
            if key not in pair_shared:
                pair_shared[key] = []
            pair_shared[key].append(p)

        # Filter pairs meeting min_shared threshold
        qualified_edges: list[tuple[str, str]] = []
        for (c1, c2), entities in pair_shared.items():
            # Distinct entity names
            unique_entities = {e["entity_name"].lower() for e in entities}
            if len(unique_entities) >= min_shared:
                qualified_edges.append((c1, c2))

        if not qualified_edges:
            return []

        # Build adjacency graph and compute connected components
        adj: dict[str, set[str]] = {}
        for c1, c2 in qualified_edges:
            adj.setdefault(c1, set()).add(c2)
            adj.setdefault(c2, set()).add(c1)

        visited: set[str] = set()
        clusters: list[dict[str, Any]] = []

        for node in adj:
            if node in visited:
                continue

            # BFS to find connected component
            component: list[str] = []
            queue = [node]
            visited.add(node)

            while queue:
                curr = queue.pop(0)
                component.append(curr)
                for neighbor in adj.get(curr, []):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)

            component_claims = sorted(component)
            # Collect all shared entities across the cluster
            component_claim_set = set(component_claims)
            cluster_entities: dict[str, dict[str, Any]] = {}

            for p in pairs:
                if p["claim_id_1"] in component_claim_set and p["claim_id_2"] in component_claim_set:
                    ename = p["entity_name"]
                    if ename not in cluster_entities:
                        cluster_entities[ename] = {
                            "name": ename,
                            "entity_type": p["entity_type"],
                            "claim_ids": set(),
                            "roles": set(),
                        }
                    cluster_entities[ename]["claim_ids"].add(p["claim_id_1"])
                    cluster_entities[ename]["claim_ids"].add(p["claim_id_2"])
                    cluster_entities[ename]["roles"].add(p["role_1"])
                    cluster_entities[ename]["roles"].add(p["role_2"])

            entities_summary = [
                {
                    "name": item["name"],
                    "entity_type": item["entity_type"],
                    "claim_count": len(item["claim_ids"]),
                    "roles": sorted(item["roles"]),
                }
                for item in cluster_entities.values()
            ]

            clusters.append({
                "cluster_id": f"ring-{str(uuid.uuid4())[:8]}",
                "claim_ids": component_claims,
                "claims_count": len(component_claims),
                "shared_entities": entities_summary,
                "shared_entity_count": len(entities_summary),
            })

        return clusters

    def detect_suspicious_patterns(self, owner_id: str) -> list[dict[str, Any]]:
        """Detects specific fraud topologies: role reversals and high-frequency hubs."""
        findings: list[dict[str, Any]] = []

        # 1. High-frequency entities (appearing in >= 3 distinct claims)
        high_freq_query = """
        MATCH (u:User {id: $owner_id})-[:OWNS]->(c:Claim {owner_id: $owner_id})-[:INVOLVES_PERSON]->(p:Person {owner_id: $owner_id})
        WITH p.name AS name, count(DISTINCT c.id) AS claim_count, collect(DISTINCT c.id) AS claims, collect(DISTINCT p.role) AS roles
        WHERE claim_count >= 3
        RETURN name, 'person' AS entity_type, claim_count, claims, roles
        UNION
        MATCH (u:User {id: $owner_id})-[:OWNS]->(c:Claim {owner_id: $owner_id})-[:INVOLVES_ORGANIZATION]->(o:Organization {owner_id: $owner_id})
        WITH o.name AS name, count(DISTINCT c.id) AS claim_count, collect(DISTINCT c.id) AS claims, collect(DISTINCT o.org_type) AS roles
        WHERE claim_count >= 3
        RETURN name, 'organization' AS entity_type, claim_count, claims, roles
        """
        freq_rows = self._execute(high_freq_query, {"owner_id": owner_id})
        for r in freq_rows:
            if not r or len(r) < 5:
                continue
            findings.append({
                "pattern_type": "HIGH_FREQUENCY_HUB",
                "entity_name": r[0],
                "entity_type": r[1],
                "claim_count": r[2],
                "claim_ids": r[3],
                "roles": r[4],
                "description": f"Entity '{r[0]}' appears in {r[2]} separate claims.",
            })

        # 2. Role reversal (person acting in different roles e.g. claimant in one, witness in another)
        role_shift_query = """
        MATCH (u:User {id: $owner_id})-[:OWNS]->(c:Claim {owner_id: $owner_id})-[:INVOLVES_PERSON]->(p:Person {owner_id: $owner_id})
        WITH p.name AS name, collect(DISTINCT p.role) AS roles, collect(DISTINCT c.id) AS claims
        WHERE size(roles) > 1 AND size(claims) > 1
        RETURN name, roles, claims
        """
        role_rows = self._execute(role_shift_query, {"owner_id": owner_id})
        for r in role_rows:
            if not r or len(r) < 3:
                continue
            findings.append({
                "pattern_type": "ROLE_REVERSAL",
                "entity_name": r[0],
                "entity_type": "person",
                "claim_count": len(r[2]),
                "claim_ids": r[2],
                "roles": r[1],
                "description": f"Individual '{r[0]}' shifts roles across claims: {', '.join(r[1])}.",
            })

        return findings


fraud_repo = FraudRepository()
