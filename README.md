# ClaimGuard — Backend Foundation (Phase 1)

ClaimGuard is an AI-augmented insurance claim intelligence platform that maps claims, policies, evidence, and actions into an interconnected knowledge graph.

Phase 1 provides the secure multi-tenant backend foundation:
- **Authentication & Authorization:** User registration, login, Argon2 password hashing, short-lived JWT access tokens, rotating refresh tokens, and owner-scoped access control.
- **FalkorDB Graph Layer:** Graph-native data modeling (`:User`, `:Claim`, `:Document`) using parameterized Cypher queries strictly confined to repositories with enforced owner scoping.
- **Secure Object Storage:** Streaming integration with MinIO/S3, chunked SHA-256 calculation, magic-byte inspection, non-guessable object keys, and 5-minute presigned download URLs.
- **Audit Logging:** Append-only PostgreSQL audit trail capturing all authentication, authorization, and data modification events.
- **Defense in Depth:** Foreign resource enumeration mitigation (404 instead of 403), security response headers, rate limiting, and fail-fast startup on insecure secrets.

---

## Architecture Overview

```
[ Client Application ]
        │
   (HTTPS / JWT)
        ▼
[ FastAPI Backend (Port 8000) ]
        ├── Auth, Claims, Documents, Health Routers
        ├── Security Headers, Request-ID, Structured Logging
        │
        ├──► PostgreSQL (Port 5432)
        │      └── Users, Refresh Tokens, Audit Events
        │
        ├──► FalkorDB (Port 6379, Graph: "claimguard")
        │      └── (:User)-[:OWNS]->(:Claim)-[:HAS_DOCUMENT]->(:Document)
        │
        └──► MinIO / S3 Object Storage (Port 9000)
               └── Uploaded original files at {owner_id}/{claim_id}/{doc_id}/{filename}
```

---

## Tech Stack

- **Runtime & Framework:** Python 3.12, FastAPI, Pydantic v2, pydantic-settings
- **Graph Database:** FalkorDB (graph name `claimguard`, official `falkordb` Python client)
- **Relational Storage:** PostgreSQL 16 via SQLAlchemy 2.0 (asyncpg) + Alembic
- **Object Storage:** MinIO (AWS S3-compatible) via boto3
- **Security:** Argon2 (argon2-cffi), PyJWT
- **Testing & Tooling:** pytest, httpx, pytest-asyncio, ruff
- **Orchestration:** Docker Compose

---

## Getting Started

### 1. Prerequisites
- Docker Engine & Docker Compose
- Python 3.12 (if running locally without Docker)
- Git

### 2. Environment Setup
Copy the sample environment file:
```bash
cp .env.example .env
```
Inspect `.env` and configure appropriate values if deploying to production. For local development, defaults are pre-configured.

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
| `GET` | `/health/ready` | Backing services readiness check | No |
| `POST` | `/auth/register` | Register new user account | No |
| `POST` | `/auth/login` | Authenticate and obtain JWT access + refresh token | No |
| `POST` | `/auth/refresh` | Rotate refresh token and obtain new access token | No |
| `POST` | `/auth/logout` | Revoke refresh token | Yes |
| `GET` | `/auth/me` | Retrieve profile of currently authenticated user | Yes |
| `POST` | `/claims` | Create a new claim | Yes |
| `GET` | `/claims` | List claims owned by current user (paginated) | Yes |
| `GET` | `/claims/{id}` | Get claim details (404 if foreign) | Yes |
| `PATCH` | `/claims/{id}` | Update claim details | Yes |
| `DELETE`| `/claims/{id}` | Soft delete claim (status ARCHIVED) | Yes |
| `POST` | `/claims/{id}/documents` | Upload untrusted document (magic-byte check, SHA-256) | Yes |
| `GET` | `/claims/{id}/documents` | List documents attached to a claim | Yes |
| `GET` | `/claims/{id}/documents/{doc_id}` | Get document metadata | Yes |
| `GET` | `/claims/{id}/documents/{doc_id}/download-url` | Generate short-lived presigned download URL | Yes |
| `DELETE`| `/claims/{id}/documents/{doc_id}` | Soft delete document | Yes |

---

## Testing & Quality Assurance

To execute tests and linting:
```bash
# Run linter
ruff check backend

# Run test suite
pytest backend/tests
```

---

## Phase 2 Extension Points

The codebase provides clean architectural extension points for Phase 2 without premature complexity:
- `backend/app/agents/`: Reserved for policy compliance and coverage analysis agents.
- `backend/app/memory/`: Reserved for episodic claim memory (strictly claim-isolated).
- `backend/app/ingestion/`: Reserved for OCR, PDF parsing, text chunking, and embedding generation.
- `backend/app/inference/`: Reserved for Nebius LLM prompting and semantic scoring.
- `backend/app/workers/`: Reserved for background jobs and S3-to-graph reconciliation.
