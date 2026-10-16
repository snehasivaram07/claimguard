# Phase 4 Architectural Decisions & Design Rationale

This document records the foundational technical and architectural decisions established during **Phase 4 (Graph Fraud Ring Detection & Network Analysis)** of ClaimGuard.

---

## Decision 1: Model Routing for Fraud Ring Analysis (Nemotron Ultra Tier)

### Context
Detecting coordinated insurance fraud syndicates requires analyzing complex, multi-claim subgraphs comprising dozens of individuals, businesses, loss locations, and timeline intersections. Synthesizing these graph structures into actionable Special Investigations Unit (SIU) dossiers requires high-capacity reasoning, syndicate pattern recognition, and strategic legal recommendation capabilities.

### Decision
Graph-level fraud ring analysis is routed through `ModelRouter` to the **Ultra Tier (`nvidia/nemotron-3-ultra`)**:
- `TaskType.FRAUD_RING_ANALYSIS -> Tier.ULTRA -> settings.NEMOTRON_ULTRA_MODEL`

Single-document text extraction remains on the lightweight **Nano** tier, and cross-document reconciliation within a single claim remains on the **Super** tier.

---

## Decision 2: Graph Traversal & Connected Component Clustering

### Context
Insurance fraud rings rarely operate within a single claim. Fraudulent actors (e.g. staged collision organizers, dishonest repair shops, corrupt clinics, repeat claimants) connect multiple distinct claims together through shared identities.

### Decision
We implemented graph traversal in `FraudRepository` (`backend/app/graph/fraud_repo.py`):
1. **Shared Entity Pairs**: Cypher queries match claims sharing `:Person` or `:Organization` nodes based on case-insensitive normalized names within the same tenant `owner_id`.
2. **Threshold Filtering**: Pairs are qualified only if they share at least `settings.FRAUD_RING_MIN_SHARED_ENTITIES` (default: 2) distinct entities, suppressing random coincidences.
3. **Connected Components**: An adjacency graph is constructed from qualified pairs, and Breadth-First Search (BFS) is executed to isolate discrete collusion clusters (rings).

---

## Decision 3: Topological Fraud Pattern Detection

### Context
Experienced SIU investigators look for specific behavioral red flags that distinguish organized fraud from ordinary high-frequency customers.

### Decision
`FraudRingService` and `FraudRepository` evaluate graph topology to identify known fraud archetypes:
1. **`ROLE_REVERSAL_NETWORK`**: An individual who shifts roles across claims (e.g., driver/claimant in one collision, passenger or witness in another).
2. **`PROVIDER_FRAUD_COLLUSION`**: Multiple distinct claimants tied to the exact same auto body repair shop, clinic, or physician.
3. **`REPEAT_CLAIMANT_SYNDICATE`**: The same core group of claimants filing multiple losses across different vehicles or policies.
4. **`STAGED_COLLISION_RING`**: Tightly clustered vehicles and passengers involved in suspicious loss mechanics.

---

## Decision 4: Cytoscape/D3 Visual Graph Schema Representation

### Context
Investigators need an interactive visual representation of the network surrounding a claim rather than raw tabular data.

### Decision
The `ClaimFraudNetworkResponse` schema in `backend/app/schemas/fraud_ring.py` defines:
- **`nodes`**: Standardized node dictionaries containing `id`, `label`, `type` (`"claim"`, `"person"`, `"organization"`), `is_target` (boolean highlighting the claim under review), and metadata properties (`risk_score`, `role`, `org_type`).
- **`edges`**: Standardized edge dictionaries containing `source`, `target`, `type` (`"INVOLVES_PERSON"`, `"INVOLVES_ORGANIZATION"`, `"AFFILIATED_WITH"`), and property flags (`is_shared`).
- This structure directly maps to standard frontend graph visualization libraries including Cytoscape.js, D3.js, and Vis.js.

---

## Decision 5: Multi-Tenant Containment & Zero-Leak Audit Trail

### Context
Exposing graph networks must never leak cross-tenant entities or breach data privacy boundaries. Audit records must provide compliance visibility without recording raw investigative notes or model prompts.

### Decision
1. **Strict Cypher Scoping**: All Cypher queries in `FraudRepository` filter strictly by `owner_id: $owner_id` at both node and relationship levels.
2. **404 Masking**: Non-existent claims and claims owned by other users return `404 Not Found` rather than `403 Forbidden`.
3. **Audit Records**:
   - `CLAIM_FRAUD_NETWORK_VIEWED`: Records `claim_id`, `node_count`, `edge_count`, and `fraud_rings_count`.
   - `FRAUD_RINGS_DETECTED`: Records `min_shared` threshold and `rings_count`.
   - Strictly zero sensitive names, prompts, or model reasoning are recorded in audit metadata.
