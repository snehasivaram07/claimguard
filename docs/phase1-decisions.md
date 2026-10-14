# ClaimGuard Phase 1 Architecture Decisions & Verification Log

This document records the architectural decisions, design rationales, security invariants, empirical verification logs, and Phase 2 extension boundaries for the ClaimGuard Phase 1 Backend Foundation.

---

## 1. Multi-Tenant Graph Modeling in FalkorDB

### Graph Architecture
- **Single Graph Namespace:** `claimguard`
- All users, claims, and documents reside within this graph structure.
- **Strict Tenant Isolation Invariant:** FalkorDB lacks native row-level security. Tenant boundaries are strictly enforced via Cypher repositories in `backend/app/graph/`.
- Every repository Cypher query takes an authenticated `$owner_id` parameter and enforces explicit graph traversal:
  ```cypher
  MATCH (u:User {id: $owner_id})-[:OWNS]->(c:Claim {id: $claim_id})
  RETURN c
  ```
- **Cypher Confinement:** Route handlers never interact with the graph client or query language directly. All Cypher queries reside exclusively in `backend/app/graph/` repositories.
- **Node Labels & Schema:**
  - `(:User {id, email, role, is_active, created_at, schema_version})`
  - `(:Claim {id, owner_id, title, claim_type, claim_number, policy_number, description, status, created_at, updated_at, schema_version})`
  - `(:Document {id, claim_id, owner_id, object_key, content_hash, document_type, original_filename, size_bytes, mime_type, uploaded_at, version, status, created_at, updated_at, schema_version})`
- **Relationships:**
  - `(:User)-[:OWNS]->(:Claim)`
  - `(:Claim)-[:HAS_DOCUMENT]->(:Document)`

### Verified Index & Constraint Syntax
- FalkorDB index creation:
  ```cypher
  CREATE INDEX FOR (u:User) ON (u.id)
  CREATE INDEX FOR (c:Claim) ON (c.id)
  CREATE INDEX FOR (d:Document) ON (d.id)
  ```
- Idempotently executed on application startup and via `scripts/bootstrap_graph.py`.

---

## 2. Object Storage & Streaming Ingestion

### Storage Architecture
- **Storage Backend:** MinIO (locally / development) and AWS S3 (production).
- **Object Key Layout:** `{owner_id}/{claim_id}/{document_id}/{sanitized_filename}`.
- Original client-provided filenames are treated as untrusted and stored only in graph node metadata. Filenames in object storage keys are strictly sanitized (removing non-alphanumeric characters, paths, and control bytes).

### Untrusted File Defense & Ingestion
- Uploaded file bytes are streamed directly into object storage via `ChainedPrefixStream` without buffering entire payloads into server RAM.
- SHA-256 hash is computed incrementally on the fly over the stream.
- **Magic Bytes Validation:** First chunk (up to 2,048 bytes) is inspected against genuine binary file signatures:
  - **PDF:** `%PDF-` (`0x25 0x50 0x44 0x46 0x2D`)
  - **PNG:** `\x89PNG\r\n\x1a\n` (`0x89 0x50 0x4E 0x47 0x0D 0x0A 0x1A 0x0A`)
  - **JPEG:** `\xFF\xD8\xFF`
  - **Plain Text:** Valid UTF-8 / ASCII byte sequences without null or control bytes
  - **EML (RFC 822):** Standard email header patterns (e.g., `From:`, `To:`, `Subject:`, `Date:`)
- Client-supplied `Content-Type` header and file extension are never trusted.

### Deduplication Policy
- **Claim-Scoped Deduplication:** If an identical file (same SHA-256 hash) is uploaded to the same claim and is not marked `ARCHIVED`, the upload is rejected with `409 Conflict` (unless `allow_duplicate=true`).
- **Cross-Tenant Duplicate Acceptance:** Uploading the exact same document bytes by different tenants to their own distinct claims succeeds with `201 Created`. Deduplication state never leaks or collides across tenant boundaries.

### Storage-to-Graph Two-Phase Compensation
- If FalkorDB node creation fails after bytes are written to object storage:
  1. The uploaded object is immediately purged from MinIO/S3 via compensatory `delete_object(object_key)`.
  2. The failure is logged with structured error context.
  3. An `AppException` with HTTP 500 (`GRAPH_PERSISTENCE_FAILED`) is returned to the client.
  4. Extension point for future periodic reconciliation worker is documented in `backend/app/workers/`.

---

## 3. Relational Storage & Security Audit Trail

### PostgreSQL Database Layer
- In Phase 1, PostgreSQL (SQLAlchemy 2.0 async + Alembic) is strictly used for:
  1. **Users:** Credentials (Argon2id), roles, and account status.
  2. **Refresh Tokens:** Hashed with SHA-256 (`token_hash`), family revocation, and expiration timestamps.
  3. **Audit Events:** Append-only tamper-resistant log table capturing security and data modification events.
- Claim relationships, graph edges, and document metadata remain exclusively inside FalkorDB.

### Append-Only Audit Logging
- Every authentication attempt, claim mutation, and document upload records an append-only event in `audit_events`:
  - `event_id`: UUID
  - `timestamp`: UTC datetime
  - `user_id`: UUID of acting user
  - `action`: `REGISTER`, `LOGIN`, `CLAIM_CREATE`, `CLAIM_UPDATE`, `CLAIM_DELETE`, `DOCUMENT_UPLOAD`, etc.
  - `resource_type`: `user`, `claim`, `document`
  - `resource_id`: Target identifier
  - `ip`: Client IP address
  - `request_id`: X-Request-ID trace identifier
  - `outcome`: `SUCCESS` / `FAILURE`
  - `metadata`: JSON payload (excluding all passwords, raw tokens, or document content)

---

## 4. Multi-Tenant Security & Defense in Depth

### Existence Masking (404 vs 403)
- **Zero Resource Enumeration:** Any authenticated user attempting to query, update, delete, upload to, or view audit logs for a claim or document belonging to another tenant receives **`404 Not Found`** (never `403 Forbidden`).
- This masks whether the foreign resource ID exists in the system, eliminating resource scanning attacks.

### Fail-Fast Configuration
- If `ENVIRONMENT` is set to `production` and placeholder/default secrets (e.g. `change-this-jwt-secret`, `falkordb`, `postgres`) are detected, the FastAPI application immediately aborts startup with a validation error.

### Deep Health Checks
- `/health/live`: Fast liveness probe confirming the process is executing.
- `/health/ready`: Deep readiness probe checking:
  1. PostgreSQL (`SELECT 1`)
  2. FalkorDB (Cypher ping query)
  3. Object Storage (bucket connectivity check)
- Returns `200 OK` when all services are healthy; returns `503 Service Unavailable` with granular status if any dependency is degraded.

---

## 5. Architectural Boundaries & Phase 2 Extension Stubs

To avoid premature complexity, Phase 1 strictly excludes Phase 2 features and reserves clean extension points:

| Directory | Phase 1 Status | Phase 2 Extension Scope |
| :--- | :--- | :--- |
| `backend/app/agents/` | Documented README stub | Policy compliance and contradiction detection agents |
| `backend/app/memory/` | Documented README stub | Episodic claim memory (strictly claim-isolated) |
| `backend/app/ingestion/` | Documented README stub | Asynchronous OCR, PDF parsing, text chunking, and embedding generation |
| `backend/app/inference/` | Documented README stub | Nebius LLM prompting and semantic scoring |
| `backend/app/workers/` | Documented README stub | Celery / Redis background jobs and orphaned S3 sweep worker |

---

## 6. Empirical Verification & Test Suite Summary

The entire Phase 1 test suite consists of **42 hermetic automated tests** executing locally without external service dependencies (using in-memory SQLite and mock graph/storage adapters):

```
backend/tests/test_audit.py .................. 3 passed
backend/tests/test_auth.py ................... 7 passed
backend/tests/test_claims.py ................. 3 passed
backend/tests/test_db_models.py .............. 3 passed
backend/tests/test_documents.py .............. 7 passed
backend/tests/test_graph_repo.py ............. 4 passed
backend/tests/test_health.py ................. 5 passed
backend/tests/test_isolation_e2e.py .......... 3 passed
backend/tests/test_storage.py ................ 7 passed
-------------------------------------------------------
Total: 42 passed in 21.15s, 0 failures, 0 lint warnings
```
