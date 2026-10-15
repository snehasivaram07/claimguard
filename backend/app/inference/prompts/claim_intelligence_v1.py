"""Claim Intelligence and Cross-Document Contradiction Analysis Prompt Template v1.0.0."""

import json
from typing import Any

CLAIM_INTELLIGENCE_VERSION = "v1.0.0"

CLAIM_INTELLIGENCE_SYSTEM_PROMPT = """You are ClaimGuard Senior Forensic Auditor, an expert AI evaluating multi-document insurance claim evidence for factual integrity, timeline coherence, and fraud indicators.

Your objective is to examine all provided document extractions for an insurance claim collectively:
1. Reconstruct a coherent, chronological timeline of key events (dates, filings, treatments, repairs).
2. Detect factual contradictions and discrepancies across documents (e.g. date inconsistencies, monetary mismatches, conflicting damage locations, contradictory statements).
3. Compute an overall risk score from 0.0 (completely consistent) to 1.0 (severe contradictions / suspected fraud).
4. Provide exact citations with document IDs for every detected contradiction.

REQUIRED JSON OUTPUT FORMAT:
Output ONLY a single valid JSON object matching the following structure:
{
  "claim_id": "string",
  "overall_risk_score": 0.35,
  "executive_summary": "Concise forensic overview comparing evidence across all documents.",
  "timeline": [
    {
      "date": "YYYY-MM-DD or string date",
      "event_description": "Description of event",
      "document_id": "doc-uuid-string",
      "source_context": "Context from document"
    }
  ],
  "discrepancies": [
    {
      "id": "disc-1",
      "title": "Short title of discrepancy",
      "description": "Detailed explanation of why these facts contradict each other.",
      "category": "date_inconsistency" | "amount_mismatch" | "damage_location_conflict" | "party_involvement_conflict" | "factual_contradiction" | "other",
      "severity": "low" | "medium" | "high" | "critical",
      "confidence": 0.90,
      "citations": [
        {
          "document_id": "doc-id-1",
          "document_name": "police_report.pdf",
          "quoted_statement": "exact quoted text from first doc",
          "page_number": 1
        },
        {
          "document_id": "doc-id-2",
          "document_name": "medical_record.pdf",
          "quoted_statement": "exact quoted text from second doc",
          "page_number": 1
        }
      ],
      "recommended_action": "Suggested follow-up investigation for adjuster"
    }
  ],
  "unresolved_questions": [
    "Key questions an adjuster or investigator should ask the claimant or providers"
  ],
  "confidence_score": 0.95
}

DO NOT output markdown code blocks (such as ```json). Output raw, parseable JSON only.
"""


def build_claim_intelligence_user_prompt(
    claim_id: str,
    claim_metadata: dict[str, Any],
    extractions: list[dict[str, Any]],
) -> str:
    """Prepares structured evidence dossier from all claim documents for Nemotron Super analysis."""
    formatted_extractions = []
    for idx, ext in enumerate(extractions, 1):
        formatted_extractions.append(
            f"--- Document #{idx} (ID: {ext.get('id', 'unknown')}, Filename: {ext.get('original_filename', 'unnamed')}) ---\n"
            f"Type: {ext.get('document_type', 'other')}\n"
            f"Summary: {ext.get('summary', 'none')}\n"
            f"Dates: {json.dumps(ext.get('dates', []))}\n"
            f"Parties: {json.dumps(ext.get('parties', []))}\n"
            f"Amounts: {json.dumps(ext.get('amounts', []))}\n"
            f"Key Facts: {json.dumps(ext.get('key_facts', []))}\n"
        )

    evidence_text = "\n".join(formatted_extractions)

    return (
        f"Perform multi-document cross-validation and timeline reconciliation for Claim ID: {claim_id}\n\n"
        f"Claim Details:\n"
        f"- Title: {claim_metadata.get('title', 'Untitled')}\n"
        f"- Policy Number: {claim_metadata.get('policy_number', 'None')}\n"
        f"- Claim Status: {claim_metadata.get('status', 'OPEN')}\n\n"
        f"Available Document Evidence ({len(extractions)} documents):\n\n"
        f"{evidence_text}\n\n"
        "Analyze all evidence collectively. Return strictly valid JSON matching the requested schema."
    )
