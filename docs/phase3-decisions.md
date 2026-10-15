# Phase 3 Architectural Decisions & Design Rationale

This document records the foundational technical and architectural decisions established during **Phase 3 (Multi-Document Claim Intelligence & Cross-Validation)** of ClaimGuard.

---

## Decision 1: Tiered LLM Routing for Multi-Document Cross-Validation (Nemotron Super)

### Context
Phase 2 utilized the **Nano Tier (`nvidia/nemotron-mini-4b-instruct`)** for fast, cost-efficient entity extraction from single documents. However, comparing multiple disparate documents (e.g., initial loss notices, police collision reports, hospital triage notes, and repair body shop estimates) requires:
1. Significant context window capacity to process multiple document extractions simultaneously.
2. Complex multi-hop logical reasoning to detect factual and temporal inconsistencies.
3. Strict citation synthesis ensuring every flagged discrepancy is backed by verbatim text quotes.

### Decision
Cross-document analysis and timeline reconstruction tasks are routed through `ModelRouter` to the **Super Tier (`nvidia/nemotron-3-super`)**:
- `TaskType.CROSS_DOCUMENT_ANALYSIS -> Tier.SUPER -> settings.NEMOTRON_SUPER_MODEL`
- `TaskType.TIMELINE_RECONSTRUCTION -> Tier.SUPER -> settings.NEMOTRON_SUPER_MODEL`

Single-document text extraction remains on the lightweight Nano tier, preserving low latency and cost efficiency.

---

## Decision 2: Schema Representation & Evidentiary Citations

### Context
Insurance Special Investigation Units (SIU) and fraud examiners cannot act on ungrounded or speculative model assertions. Every discrepancy, contradiction, or timeline milestone must be directly auditable back to source documents.

### Decision
We defined structured Pydantic schemas in `backend/app/inference/claim_analysis_schemas.py`:
- **`ClaimIntelligenceAnalysisV1`**: Central analysis schema containing overall risk score, executive summary, chronological timeline, discrepancy findings, and unresolved investigation questions.
- **`TimelineEvent`**: ISO-8601 date, event description, source document ID, and verbatim source context.
- **`ClaimDiscrepancy`**: Categorized (`date_inconsistency`, `amount_mismatch`, `damage_location_conflict`, `party_involvement_conflict`, `factual_contradiction`), classified by severity (`low`, `medium`, `high`, `critical`), and bound to `DocumentCitation` objects.
- **`DocumentCitation`**: Contains `document_id`, optional `page_number`, and `quoted_statement`.

---

## Decision 3: FalkorDB Knowledge Graph Entity Linking

### Context
While LLMs perform cross-document textual comparison, detecting organized fraud rings requires representing the underlying social and organizational network as a graph.

### Decision
We introduced `EntityRepository` (`backend/app/graph/entity_repo.py`) to map extracted parties into FalkorDB graph nodes during claim analysis:
1. **Node Classification**:
   - Human roles (`claimant`, `insured`, `driver`, `passenger`, `witness`, `officer`, `physician`) instantiate `(:Person)` nodes.
   - Institutional entities (`body_shop`, `repairer`, `hospital`, `clinic`, `insurer`, `law_firm`) instantiate `(:Organization)` nodes.
2. **Relationship Graph**:
   - `(:Claim)-[:INVOLVES {role, document_id, confidence, updated_at}]->(:Person|:Organization)`
   - `(:Person)-[:AFFILIATED_WITH {title, role, document_id}]->(:Organization)`
3. **Graph Indexes**:
   - Bootstrap schema adds composite range indexes on `(:Person(owner_id, name))` and `(:Organization(owner_id, name))` to guarantee tenant isolation and sub-millisecond entity resolution.

---

## Decision 4: FalkorDB Property Storage & Dual-Store Strategy

### Context
FalkorDB graph nodes enforce strict typing: node properties only support scalar primitives (strings, booleans, integers, floats) and primitive arrays. Arbitrary nested dictionaries and complex JSON models cannot be saved as native properties.

### Decision
We implement a dual-store persistence pattern:
1. **FalkorDB `(:Claim)` Node**:
   - Stores `risk_score` as a native float for fast Cypher querying.
   - Stores the full serialized schema as an `analysis_json` string property on the node.
   - Updated via `ClaimRepository.update_claim_analysis(owner_id, claim_id, analysis_json, risk_score)`.
2. **Postgres Audit Trail**:
   - Logs `CLAIM_ANALYSIS_REQUESTED`, `CLAIM_ANALYSIS_COMPLETED`, and `CLAIM_ANALYSIS_FAILED` audit events.
   - Strict privacy boundary: Audit metadata records counts and classification enums only (e.g. `discrepancies_count`, `timeline_events_count`, `overall_risk_score`). No raw text, prompt instructions, or model reasoning are ever written to Postgres logs.

---

## Decision 5: Hermetic CLI Worker Architecture (`analyze_claim_job.py`)

### Context
Batch claim reprocessing, scheduled backfills, and asynchronous queue workers need a standalone CLI entrypoint that does not require starting the FastAPI web server.

### Decision
We created `backend/app/workers/analyze_claim_job.py`:
- Invoked via: `python -m app.workers.analyze_claim_job <owner_id> <claim_id> [--json] [--quiet]`
- Standardized exit codes:
  - `0`: `EXIT_SUCCESS` (analysis complete, outputs JSON if `--json` supplied)
  - `1`: `EXIT_GENERAL_ERROR` (unexpected internal error)
  - `2`: `EXIT_NOT_FOUND` (claim does not exist or owner ID unauthorized - 404 masked)
  - `3`: `EXIT_UNPROCESSABLE` (insufficient or zero extracted documents)
- Fully unit tested in `backend/tests/test_workers.py`.
