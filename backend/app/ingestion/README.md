# Ingestion Extension Stub (Phase 2+)

This module will handle:
- Document format parsing (PDF text extraction, OCR, image parsing)
- Semantic text chunking
- Policy clause extraction & classification
- Embedding generation and vector index synchronization

## Status Lifecycle
Phase 1 marks stored documents as `STORED`. Future phases advance through:
`RECEIVED` -> `VALIDATING` -> `STORED` -> `EXTRACTING` -> `INDEXING` -> `MATCHING_CLAIM` -> `ANALYZING` -> `READY_FOR_REVIEW` -> `COMPLETED`.

## Phase 1 Scope
Out of scope in Phase 1. Clean architectural extension point only.
