# ClaimGuard Phase 1 Architecture Decisions & Verification Log

This document records architectural decisions, assumptions, and empirical findings for the ClaimGuard Phase 1 Backend Foundation.

---

## 1. Multi-Tenant Graph Modeling in FalkorDB

### Graph Architecture
- **Single Graph Namespace:** `claimguard`
- All users, claims, and documents reside within this graph.
- **Strict Isolation Constraint:** FalkorDB does not have native row-level security. Tenant boundaries are enforced via Cypher repositories in `backend/app/graph/`.
- Every repository Cypher query takes an authenticated `owner_id` parameter and enforces it in the query:
  ```cypher
  MATCH (u:User {id: $owner_id})-[:OWNS]->(c:Claim {id: $claim_id})
  RETURN c
  ```
- **Cypher Confinement:** Route handlers never interact with the graph client or query language directly. All Cypher queries reside exclusively in `backend/app/graph/` repositories.

### Verified Index & Constraint Syntax
- FalkorDB index creation:
  ```cypher
  CREATE INDEX FOR (u:User) ON (u.id)
  CREATE INDEX FOR (c:Claim) ON (c.id)
  CREATE INDEX FOR (d:Document) ON (d.id)
  ```
- To be idempotently executed on system boot and via `scripts/bootstrap_graph.py`.

---

## 2. Object Storage & Streaming Uploads

### Storage Layer
- Storage backend: MinIO (locally) / AWS S3 (production).
- Object Key Layout: `{owner_id}/{claim_id}/{document_id}/{sanitized_filename}`.
- Original client-provided filenames are treated as untrusted and stored only in node metadata.

### Untrusted File Defense & Ingestion
- Uploaded file bytes are streamed in 64 KB chunks directly to MinIO.
- SHA-256 hash is computed incrementally over the chunk stream.
- **Magic Bytes Validation:** First chunk is inspected against file signatures:
  - PDF: `%PDF-` (`0x25 0x50 0x44 0x46 0x2D`)
  - PNG: `\x89PNG\r\n\x1a\n` (`0x89 0x50 0x4E 0x47 0x0D 0x0A 0x1A 0x0A`)
  - JPEG: `\xFF\xD8\xFF`
  - Plain Text: Valid UTF-8 / ASCII byte sequences
  - EML (RFC 822): Common email headers (e.g. `From:`, `To:`, `Subject:`, `Date:`)
- Client-supplied `Content-Type` header and file extension are never trusted.

### Storage-to-Graph Compensation
- If FalkorDB node creation fails after bytes are written to MinIO:
  1. The uploaded object is immediately purged from MinIO via compensatory `delete_object`.
  2. The failure is logged with structured error context.
  3. Clean extension point for future reconciliation worker is documented.

---

## 3. Database & Relational Storage (PostgreSQL)

- In Phase 1, PostgreSQL is strictly used for:
  1. Users (credentials, roles, status)
  2. Rotating refresh tokens (hashed with Argon2/SHA-256, family revocation)
  3. Security audit log (tamper-resistant append-only log)
- Claim relationships, metadata, and document linkages remain exclusively inside FalkorDB.

---

## 4. Security Principles

- **Existence Masking:** 404 Not Found (instead of 403 Forbidden) is returned whenever an authenticated user queries a claim or document belonging to another tenant. This prevents resource enumeration attacks.
- **Fail-Fast Configuration:** If `ENVIRONMENT` is set to `production` and placeholder/default secrets are detected, the FastAPI application immediately aborts startup with an informative validation error.
- **Zero Raw Secrets Logging:** Passwords, refresh tokens, JWT secrets, and document bytes are strictly excluded from structured logs and audit records.
