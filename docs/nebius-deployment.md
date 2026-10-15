# ClaimGuard — Nebius Token Factory & NVIDIA Nemotron Deployment Guide

This document details the production architecture, configuration, security guardrails, and operational runbooks for running ClaimGuard AI inference on **Nebius Token Factory** using **NVIDIA Nemotron** foundation models.

---

## 1. Architecture & Model Tiers

ClaimGuard delegates high-stakes insurance document forensic analysis to tiered NVIDIA Nemotron models hosted on Nebius Token Factory:

| Tier | Default Model | Primary Responsibilities | Phase Introduced |
| :--- | :--- | :--- | :--- |
| **Nano** | `nvidia/nemotron-mini-4b-instruct` | High-throughput single-document text extraction, structured JSON parsing, date/party/amount extraction. | **Phase 2 (Active)** |
| **Super** | `nvidia/nemotron-3-super` | Multi-document claim intelligence, cross-document timeline reconciliation, contradiction detection. | **Phase 3** |
| **Ultra** | `nvidia/nemotron-3-ultra` | Complex fraud ring collusion analysis, forensic audit narrative synthesis, SIU evidence dossiers. | **Phase 4 & 5** |

### Client Design
- **Base Endpoint:** `https://api.tokenfactory.nebius.com/v1/`
- **Protocol:** Standard OpenAI-compatible Chat Completions API (`POST /chat/completions`).
- **Resilience:** Asynchronous non-blocking HTTP (`httpx.AsyncClient`) with exponential backoff, randomized jitter, concurrency semaphore gating (`LLM_MAX_CONCURRENCY`), and automated parsing repair.

---

## 2. Configuration & Secrets

All inference configurations are managed through Pydantic `BaseSettings` reading from environment variables or a local `.env` file.

### Required Environment Variables

```bash
# Enable AI inference features in the platform
INFERENCE_ENABLED=true

# Nebius Token Factory API Key (SecretStr: never logged or leaked in exception traces)
NEBIUS_API_KEY=your_nebius_api_key_here

# Nebius Token Factory Base URL
NEBIUS_BASE_URL=https://api.tokenfactory.nebius.com/v1/

# Model Tier Identifiers
NEMOTRON_NANO_MODEL=nvidia/nemotron-mini-4b-instruct
NEMOTRON_SUPER_MODEL=nvidia/nemotron-3-super
NEMOTRON_ULTRA_MODEL=nvidia/nemotron-3-ultra

# Reliability & Concurrency Tuning
LLM_TIMEOUT_SECONDS=60.0
LLM_MAX_RETRIES=3
LLM_MAX_CONCURRENCY=5
LLM_MAX_INPUT_CHARS=32000
```

---

## 3. Operational Workflows

### A. Real-Time API Extraction
For interactive user sessions, clients invoke the REST endpoint:
```http
POST /claims/{claim_id}/documents/{document_id}/extract
Authorization: Bearer <jwt_access_token>
```
- Protected by SlowAPI rate limiting (`10/minute` per IP).
- Audited to PostgreSQL table `audit_events` with actions:
  - `DOCUMENT_EXTRACTION_REQUESTED`
  - `DOCUMENT_EXTRACTION_COMPLETED`
  - `DOCUMENT_EXTRACTION_FAILED`

### B. Batch Execution via Nebius Serverless Jobs
For high-volume asynchronous batch ingestion, use the standalone worker entrypoint:

```bash
# General invocation
python -m app.workers.extract_job <owner_id> <claim_id> <document_id>

# Emit grounded JSON payload to stdout (for pipeline piping)
python -m app.workers.extract_job <owner_id> <claim_id> <document_id> --json

# Quiet mode (suppresses informational logs)
python -m app.workers.extract_job <owner_id> <claim_id> <document_id> --quiet
```

#### Exit Codes for Orchestrators
- `0`: Extraction completed successfully and graph was updated.
- `1`: General or temporary failure (retryable by job runner).
- `2`: Document not found or foreign owner access (404 isolation, do not retry).
- `3`: Unprocessable document (unsupported media type or no text layer, do not retry).

---

## 4. Security & Safety Guardrails

1. **Hostile Document Isolation (`DefaultGuard`)**:
   - Untrusted text extracted from PDFs or emails is encapsulated in rigid `<untrusted_document_content>` XML boundaries.
   - The extraction prompt explicitly instructs the LLM that commands within these boundaries are passive data and must never be obeyed.
   - Text is scanned for heuristic injection patterns (`ignore previous instructions`, `system prompt override`, etc.) and flagged for security monitoring.

2. **Zero Raw Text or Secret Leaks in Logs**:
   - Prompts, raw document text, and LLM reasoning steps (`<think>` tags) are **never** logged to stdout/stderr, written to Postgres audit tables, or stored in plaintext database columns.
   - Audit event metadata contains strictly operational counters (`dates_count`, `amounts_count`, `all_entities_grounded`, `confidence_score`).

3. **Grounding & Anti-Hallucination**:
   - Every entity (`ExtractedDate`, `ExtractedParty`, `ExtractedAmount`) is validated by `GroundingValidator` against the exact character offsets and page numbers of the original extracted text.
   - Ungrounded entities are marked `grounded: false`.

4. **Compensatory Rollback**:
   - Derived text artifacts stored in S3 (`{owner_id}/{claim_id}/{document_id}/derived/text.txt`) are automatically deleted if subsequent inference or parsing steps fail, preventing orphaned storage artifacts.

---

## 5. Health & Readiness Decoupling

ClaimGuard implements strict health decoupling in `backend/app/api/health.py`:
- `/health/live`: Basic process liveness probe.
- `/health/ready`: Verifies internal dependencies (PostgreSQL, FalkorDB, MinIO/S3).
- **Nebius Token Factory is intentionally excluded from `/health/ready`:**
  - An external LLM outage, network blip, or rate limit must **never** mark the backend service unready or trigger Kubernetes pod restarts.
  - Core platform operations (user authentication, claim filing, document uploads, report downloads) remain fully operational even if inference is temporarily degraded.
