# Memory Extension Stub (Phase 2+)

This module will manage:
- Agent working memory and conversation contexts
- Long-term claim episodic memory
- User-scoped knowledge retrieval

## Isolation Rule
Unrelated claims never share memory or data. Agent identities are reused across runs, but claim-level memory must always be strictly isolated.

## Phase 1 Scope
Out of scope in Phase 1. Clean architectural extension point only.
