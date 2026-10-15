# ClaimGuard Phase 2 Architecture Decisions & Verification Log

This document records the architectural decisions, verified external facts, security invariants, and empirical findings for **Phase 2: Nemotron Inference & First Extraction Workflow**.

---

## 1. Verified External Facts

### 1.1 Nebius Token Factory API
- **Base URL:** `https://api.tokenfactory.nebius.com/v1/` (alias `https://api.studio.nebius.ai/v1/`).
- **Protocol:** Standard OpenAI-compatible REST API.
- **Authentication:** `Authorization: Bearer <NEBIUS_API_KEY>`.
- **Model Discovery:** Programmatic discovery via `GET https://api.tokenfactory.nebius.com/v1/models`.

### 1.2 NVIDIA Nemotron Model Family & Tiers
- **Tier 1 (Nano):** Fast, high-volume extraction, low latency (default model ID configured via `NEMOTRON_NANO_MODEL`, e.g. `nvidia/nemotron-3-nano`).
- **Tier 2 (Super):** Balanced reasoning and synthesis (configured via `NEMOTRON_SUPER_MODEL`, e.g. `nvidia/nemotron-3-super`).
- **Tier 3 (Ultra):** Deep reasoning and complex cross-document deduction (configured via `NEMOTRON_ULTRA_MODEL`, e.g. `nvidia/nemotron-3-ultra`).
- **Phase 2 Scope:** Only `DOCUMENT_EXTRACTION -> NANO` is wired into active workflows. Super and Ultra are reachable through the router and smoke-tested.

### 1.3 Structured Output & Reasoning Stripping
- **JSON Mode:** Supported via `response_format={"type": "json_object"}`.
- **Reasoning Handling:** Reasoning models emit chain-of-thought tokens inside `<think>...</think>` tags. The inference layer strips reasoning blocks using multiline regex:
  ```python
  re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
  ```
- **Defensive Parsing:** Clean markdown code fences (```json ... ```), validate against Pydantic schema, and permit exactly ONE repair retry upon syntax failure before raising a typed error.

### 1.4 FalkorDB Property Storage Constraints
- **FalkorDB Invariant:** Node properties in FalkorDB strictly accept scalar primitives (strings, integers, floats, booleans) or arrays of primitives. Nested dictionaries or maps cannot be stored as property values directly.
- **Decision:** Extracted structured data is serialized as a size-capped JSON string stored under the `extraction_json` property on the `(:Document)` node.

### 1.5 Nebius Serverless Endpoints & Jobs
- **Serverless Endpoint:** HTTP service listening on port 8000.
- **Serverless Job:** Batch workload container invoked via:
  ```bash
  python -m app.workers.extract_job <owner_id> <claim_id> <document_id>
  ```
- **Secret Injection:** Injected via `--env-secret` or plaintext `--env`.

---

## 2. Phase 2 Architectural Decisions

1. **PDF Text Extraction Library:**
   - Selected `pypdf` (BSD-3-Clause license, pure Python, zero native C vulnerabilities, lightweight ~6 MB).
   - Only text-layer extraction is performed. Documents with zero text layer are flagged `FAILED_FINAL` (`NO_TEXT_LAYER`).
2. **Derived Text Storage:**
   - Extracted document text is saved as a derived artifact in object storage at:
     `{owner_id}/{claim_id}/{document_id}/derived/text.txt`
   - Document text is **never** stored in FalkorDB, PostgreSQL, or application logs.
3. **Guard Layer & Prompt Injection Defense:**
   - Lightweight, zero-dependency `Guard` implementation wrapping untrusted input in rigid XML boundaries (`<untrusted_document_content>`).
   - Scans for heuristic prompt injection attempts (e.g. "ignore previous instructions") and logs an audit security flag without echoing the input text.
4. **Grounding Validator:**
   - Every extracted entity (dates, amounts, parties, claim/policy numbers) must be strictly located within the derived source text.
   - For grounded values, character offsets and page references are captured. Unlocated values are dropped or flagged `ungrounded`.
5. **Multi-Tenant Protection & 404 Masking:**
   - `POST /claims/{claim_id}/documents/{document_id}/extract` verifies claim ownership first. Unauthorized access attempts return `404 Not Found` immediately, and the inference client is **never** invoked.
