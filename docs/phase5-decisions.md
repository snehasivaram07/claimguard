# Phase 5 Architectural Decisions & Design Rationale

This document records the foundational technical and architectural decisions established during **Phase 5 (Forensic SIU Dossier Export & Report Generation)** of ClaimGuard.

---

## Decision 1: Unified Forensic Dossier Schema (`ForensicDossierV1`)

### Context
Special Investigation Unit (SIU) investigators, fraud analysts, and defense attorneys require a single, authoritative evidentiary document that synthesizes every analytical facet of a suspicious insurance claim. Previously, evidence was partitioned across multiple microservices and storage tiers:
- Relational metadata in PostgreSQL (claim status, policy numbers, dates)
- Multimodal extractions in MinIO & FalkorDB (dates, entities, summaries)
- Cross-document timeline and discrepancy intelligence (Nemotron Super analysis)
- Graph collusion networks and multi-claim fraud rings (Nemotron Ultra analysis)

### Decision
We defined `ForensicDossierV1` in `backend/app/schemas/dossier.py` as the canonical structured representation:
- **`dossier_id` & `claim_id`**: Deterministic unique identifiers.
- **`overall_risk_score`**: Synthesized risk score evaluating both document inconsistencies and network collusion severity.
- **`fraud_classification`**: Clear risk tiering (`CRITICAL_COLLUSION_RING`, `HIGH_RISK_COLLUSION`, `DISCREPANCY_FLAGGED_HIGH`, `DISCREPANCY_FLAGGED_MEDIUM`, `LOW_RISK_STANDARD`).
- **`executive_summary`**: High-level SIU executive narrative.
- **`claim_metadata`**: Insured, policy, and loss mechanics overview.
- **`documents_summary`**: Catalog of attached evidence files with extraction status and entity statistics.
- **`chronological_timeline`**: Reconstructed incident chronology attributing each event to specific source evidence.
- **`contradictions_and_discrepancies`**: Cross-document contradictions with quoted evidentiary citations.
- **`associated_fraud_rings`**: Collusion syndicates, shared providers, and topology indicators.
- **`network_subgraph`**: Serialized nodes and edges for visual rendering.
- **`investigator_recommendations`**: Prioritized SIU action plan (subpoenas, examinations under oath, field audits).

---

## Decision 2: Multi-Format Serialization Architecture (JSON, Markdown, Print-Ready HTML)

### Context
Different consumers require different dossier formats:
- Automated SIU triage and downstream claim engines require machine-readable JSON.
- Adjusters and investigators reviewing notes in IDEs, text editors, or ticket systems prefer clean Markdown.
- Legal teams and external counsel require print-ready, styled documents suitable for direct printing or headless PDF conversion without external network dependencies.

### Decision
`DossierService` (`backend/app/services/dossier_service.py`) provides first-class serialization into three formats:
1. **JSON (`DossierExportFormat.JSON`)**: Formatted with 2-space indentation and MIME type `application/json`.
2. **Markdown (`DossierExportFormat.MARKDOWN`)**: Styled with clean GitHub-flavored markdown tables, badges, and bulleted checklists (`text/markdown; charset=utf-8`).
3. **Print-Ready Styled HTML (`DossierExportFormat.HTML`)**:
   - Zero external CDN dependencies (uses system font stacks: `-apple-system, BlinkMacSystemFont, Segoe UI, Roboto`).
   - Clean card-based CSS layouts with color-coded risk badges (Red for $\ge 0.75$, Amber for $0.40 - 0.74$, Green for $< 0.40$).
   - Standard `@media print` rules (`size: A4`, `page-break-inside: avoid`) ensuring clean PDF conversion via headless Chromium or browser print dialogs.

---

## Decision 3: Multi-Tenant Boundary Isolation & 404 Existence Masking

### Context
In multi-tenant SaaS deployments, allowing an unauthorized user to discover whether a foreign claim ID or dossier exists is an unacceptable information leak.

### Decision
- All dossier generation and export operations require strict `owner_id` scoping.
- If a claim ID does not exist or belongs to another tenant, the API and service raise `NotFoundError("Claim not found")`, returning HTTP `404 Not Found` rather than `403 Forbidden`.
- The system never confirms the existence of foreign claims, preventing enumeration attacks.

---

## Decision 4: SIU Audit Trail Integrity & Safe Metadata Logging

### Context
Insurance regulations (e.g. NAIC model laws, state insurance department standards) mandate detailed audit logging of all SIU investigative queries. However, privacy laws forbid storing unmasked sensitive PII or full LLM reasoning prompts in relational audit logs.

### Decision
Every dossier view and export creates an immutable `AuditEvent` in PostgreSQL:
1. **`DOSSIER_GENERATED`**:
   - Metadata recorded: `claim_id`, `dossier_id`, `overall_risk_score`, `fraud_classification`, `documents_count`, `discrepancies_count`, `fraud_rings_count`.
2. **`DOSSIER_EXPORTED`**:
   - Metadata recorded: `claim_id`, `format`, `filename`, `size_bytes`.
3. **Privacy Guarantee**: Zero raw document text, prompt templates, claimant identities, or model reasoning are persisted in PostgreSQL audit trails.

---

## Decision 5: Headless Batch CLI Export Worker (`export_dossier_job.py`)

### Context
Enterprise claims departments routinely batch-process hundreds of suspicious claims nightly or export closed SIU files for archival and litigation prep.

### Decision
We created `backend/app/workers/export_dossier_job.py`:
- Command-line syntax:
  ```bash
  python -m app.workers.export_dossier_job <owner_id> <claim_id> [--format json|markdown|html] [--output <path>] [--stdout] [--quiet]
  ```
- Standardized UNIX exit codes:
  - `0` (`EXIT_SUCCESS`): Dossier generated and written/streamed successfully.
  - `1` (`EXIT_GENERAL_ERROR`): Database or internal system error.
  - `2` (`EXIT_NOT_FOUND`): Claim not found or unauthorized (404 masking).
  - `3` (`EXIT_UNPROCESSABLE`): Unsupported format or invalid argument.
- Seamlessly integrates with Kubernetes CronJobs, Airflow DAGs, and shell scripts.
