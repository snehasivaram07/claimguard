# ClaimGuard — AI Claim Intelligence Platform

ClaimGuard is an AI-augmented insurance claim intelligence platform that maps claims, policies, evidence, and actions into an interconnected knowledge graph to detect fraud, verify facts, and streamline adjudication.

- **Phase 1 (Complete):** Secure multi-tenant foundation, PostgreSQL, FalkorDB graph layer, S3/MinIO streaming storage with magic-byte verification, and audit trails.
- **Phase 2 (Complete):** NVIDIA Nemotron AI inference via Nebius Token Factory, hostile document text extraction (PDF, TXT, EML), prompt injection defenses, structured schema parsing with 1-shot repair, exact character-offset entity grounding, and standalone batch worker jobs.

---

## Architecture Overview

```
[ Client Application / Web UI ]
         │
    (HTTPS / JWT)
         ▼
[ FastAPI Backend (Port 8000) ]
         ├── Auth, Claims, Documents, Health Routers
         ├── Security Headers, Request-ID, Structured Logging
         │
         ├──► PostgreSQL 16 (Port 5432)
         │      └── Users, Refresh Tokens, Audit Events
         │
         ├──► FalkorDB (Port 6379, Graph: "claimguard")
         │      └── (:User)-[:OWNS]->(:Claim)-[:HAS_DOCUMENT]->(:Document)
         │            (With grounded extraction metadata stored on :Document node)
         │
         ├──► MinIO / S3 Object Storage (Port 9000)
         │      ├── Original untrusted files at {owner_id}/{claim_id}/{doc_id}/{filename}
         │      └── Derived plain-text artifacts at {owner_id}/{claim_id}/{doc_id}/derived/text.txt
         │
         └──► Nebius Token Factory (External AI Inference)
                └── NVIDIA Nemotron Nano (4B) for structured document entity extraction
```

---

## Tech Stack

- **Runtime & Framework:** Python 3.12 / 3.11, FastAPI, Pydantic v2, pydantic-settings
- **AI & Inference:** Nebius Token Factory, NVIDIA Nemotron Mini (4B Instruct)
- **Document Ingestion:** PyPDF (BSD-3-Clause), RFC 822 email parser, safe text decoder
- **Graph Database:** FalkorDB (graph name `claimguard`, official `falkordb` Python client)
- **Relational Storage:** PostgreSQL 16 via SQLAlchemy 2.0 (asyncpg) + Alembic
- **Object Storage:** MinIO (AWS S3-compatible) via boto3
- **Security:** Argon2 (argon2-cffi), PyJWT, SlowAPI rate limiting, XML prompt guard
- **Testing & Tooling:** pytest, httpx, pytest-asyncio, ruff
- **Orchestration:** Docker Compose

---

## Getting Started

### 1. Prerequisites
- Docker Engine & Docker Compose
- Python 3.11+ (if running locally without Docker)
- Git

### 2. Environment Setup
Copy the sample environment file:
```bash
cp .env.example .env
```
Configure your `.env` file. For live AI extraction via Nebius Token Factory, set:
```bash
INFERENCE_ENABLED=true
NEBIUS_API_KEY=your_nebius_api_key_here
```

### 3. Launching with Docker Compose
Start all backing services (PostgreSQL, FalkorDB, MinIO) and the API backend:
```bash
docker compose up -d --build
```
This automatically:
1. Boots PostgreSQL, FalkorDB, and MinIO.
2. Initializes the default MinIO storage bucket (`claimguard-documents`).
3. Runs database migrations (`alembic upgrade head`).
4. Bootstraps FalkorDB indexes for `User`, `Claim`, and `Document`.
5. Starts the FastAPI server on `http://localhost:8000`.

### 4. Interactive API Documentation
When running in `development` mode (`ENVIRONMENT=development`), Swagger UI is available at:
`http://localhost:8000/docs`

---

## API Summary

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/health/live` | Process liveness probe | No |
| `GET` | `/health/ready` | Backing services readiness check (Postgres, FalkorDB, S3) | No |
| `POST` | `/auth/register` | Register new user account | No |
| `POST` | `/auth/login` | Authenticate and obtain JWT access + refresh token | No |
| `POST` | `/auth/refresh` | Rotate refresh token and obtain new access token | No |
| `POST` | `/auth/logout` | Revoke refresh token | Yes |
| `GET` | `/auth/me` | Retrieve profile of currently authenticated user | Yes |
| `GET` | `/auth/me/audit` | Retrieve personal security audit events | Yes |
| `POST` | `/claims` | Create a new claim | Yes |
| `GET` | `/claims` | List claims owned by current user (paginated) | Yes |
| `GET` | `/claims/{id}` | Get claim details (404 if foreign) | Yes |
| `PATCH` | `/claims/{id}` | Update claim details | Yes |
| `DELETE`| `/claims/{id}` | Soft delete claim (status ARCHIVED) | Yes |
| `GET` | `/claims/{id}/audit` | Retrieve audit trail for a claim (404 if foreign) | Yes |
| `POST` | `/claims/{id}/documents` | Upload untrusted document (magic-byte check, SHA-256) | Yes |
| `GET` | `/claims/{id}/documents` | List documents attached to a claim | Yes |
| `GET` | `/claims/{id}/documents/{doc_id}` | Get document metadata | Yes |
| `GET` | `/claims/{id}/documents/{doc_id}/download-url` | Generate short-lived presigned download URL | Yes |
| `DELETE`| `/claims/{id}/documents/{doc_id}` | Soft delete document | Yes |
| `POST` | `/claims/{id}/documents/{doc_id}/extract` | **(Phase 2)** Trigger text extraction, guarded Nemotron inference, and entity grounding | Yes |
| `POST` | `/claims/{id}/analyze` | **(Phase 3)** Trigger multi-document cross-validation, timeline reconstruction, and contradiction detection | Yes |
| `GET` | `/claims/{id}/intelligence` | **(Phase 3)** Retrieve cached claim intelligence report and discrepancy analysis | Yes |
| `GET` | `/claims/{id}/fraud-network` | **(Phase 4)** Retrieve 1-hop and 2-hop graph neighborhood and detected fraud rings for a claim | Yes |
| `GET` | `/fraud-rings` | **(Phase 4)** Detect and list all multi-claim fraud rings and collusion syndicates | Yes |

---

## Background & Batch Worker CLI

For asynchronous batch processing or execution on **Nebius Serverless Jobs**:

### Document Extraction Worker (Phase 2)
```bash
# General invocation
python -m app.workers.extract_job <owner_id> <claim_id> <document_id>

# Emit grounded JSON payload to stdout
python -m app.workers.extract_job <owner_id> <claim_id> <document_id> --json

# Quiet mode (suppress informational logs)
python -m app.workers.extract_job <owner_id> <claim_id> <document_id> --quiet
```

### Claim Intelligence & Reconciliation Worker (Phase 3)
```bash
# Cross-document intelligence analysis
python -m app.workers.analyze_claim_job <owner_id> <claim_id>

# Emit structured intelligence JSON payload to stdout
python -m app.workers.analyze_claim_job <owner_id> <claim_id> --json

# Quiet mode
python -m app.workers.analyze_claim_job <owner_id> <claim_id> --quiet
```

### Fraud Ring Detection Worker (Phase 4)
```bash
# Detect collusion clusters and syndicates across claims
python -m app.workers.detect_fraud_rings_job <owner_id> [--min-shared <N>]

# Emit detected fraud rings JSON payload to stdout
python -m app.workers.detect_fraud_rings_job <owner_id> --json

# Quiet mode
python -m app.workers.detect_fraud_rings_job <owner_id> --quiet
```

### Exit Codes:
- `0`: Success (extraction/analysis/detection completed, graph updated).
- `1`: General failure (retryable by job orchestrator).
- `2`: Document, claim, or owner not found, or foreign owner access (404 masking, non-retryable).
- `3`: Unprocessable document or invalid parameters (non-retryable).

---

## Testing & Quality Assurance

To execute the hermetic automated tests (zero spend on cloud credits) and lint checks:
```bash
# Run linter
ruff check backend scripts

# Run full test suite
pytest backend/tests
```

---

## Documentation

- [`docs/phase1-decisions.md`](docs/phase1-decisions.md): Architecture decisions for Phase 1 foundational services.
- [`docs/phase2-decisions.md`](docs/phase2-decisions.md): Technical decision records for model tiering, prompt guard, grounding, and FalkorDB schema.
- [`docs/phase3-decisions.md`](docs/phase3-decisions.md): Architectural decision record for cross-document intelligence, timeline reconstruction, and graph entity linking.
- [`docs/phase4-decisions.md`](docs/phase4-decisions.md): Architectural decision record for graph fraud ring detection, connected components, and collusion topology classification.
- [`docs/nebius-deployment.md`](docs/nebius-deployment.md): Operational guide for Nebius Token Factory, concurrency management, and Serverless Jobs.

---

## Next Steps (Phase 5 - Final Backend Phase)

- **Phase 5:** Automated forensic audit report generation and SIU evidence dossiers using **Nemotron Ultra**.


