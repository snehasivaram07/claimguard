import html
from datetime import UTC, datetime
from typing import Any

from app.core.errors import NotFoundError
from app.core.logging import logger
from app.graph.claim_repo import ClaimRepository
from app.graph.document_repo import DocumentRepository
from app.schemas.dossier import (
    DossierClaimMetadata,
    DossierDiscrepancyItem,
    DossierDocumentSummary,
    DossierExportFormat,
    DossierExportResponse,
    DossierFraudRingItem,
    DossierRecommendationItem,
    DossierTimelineEvent,
    ForensicDossierV1,
)
from app.services.claim_intelligence_service import (
    ClaimIntelligenceService,
)
from app.services.claim_intelligence_service import (
    claim_intelligence_service as default_intelligence_service,
)
from app.services.claim_service import ClaimService
from app.services.claim_service import claim_service as default_claim_service
from app.services.fraud_ring_service import (
    FraudRingService,
)
from app.services.fraud_ring_service import (
    fraud_ring_service as default_fraud_service,
)


class DossierService:
    """Orchestrates comprehensive multi-source SIU forensic dossier synthesis and export rendering."""

    def __init__(
        self,
        claim_srv: ClaimService | None = None,
        claim_repository: ClaimRepository | None = None,
        document_repository: DocumentRepository | None = None,
        intelligence_srv: ClaimIntelligenceService | None = None,
        fraud_srv: FraudRingService | None = None,
    ):
        self._claim_service = claim_srv
        self._claim_repo = claim_repository
        self._document_repo = document_repository
        self._intelligence_service = intelligence_srv
        self._fraud_service = fraud_srv

    @property
    def claim_service(self) -> ClaimService:
        if self._claim_service is None:
            self._claim_service = default_claim_service
        return self._claim_service

    @property
    def claim_repo(self) -> ClaimRepository:
        if self._claim_repo is None:
            self._claim_repo = ClaimRepository()
        return self._claim_repo

    @property
    def document_repo(self) -> DocumentRepository:
        if self._document_repo is None:
            self._document_repo = DocumentRepository()
        return self._document_repo

    @property
    def intelligence_service(self) -> ClaimIntelligenceService:
        if self._intelligence_service is None:
            self._intelligence_service = default_intelligence_service
        return self._intelligence_service

    @property
    def fraud_service(self) -> FraudRingService:
        if self._fraud_service is None:
            self._fraud_service = default_fraud_service
        return self._fraud_service

    async def generate_dossier(self, owner_id: str, claim_id: str) -> ForensicDossierV1:
        """Aggregates all forensic evidence, cross-document discrepancies, and collusion graphs for a claim.

        Strictly enforces multi-tenant boundary isolation and masks foreign claims with 404 NotFoundError.
        """
        now = datetime.now(UTC).isoformat()

        # 1. Ownership & existence verification (enforcing 404 existence masking)
        claim_resp = await self.claim_service.get_claim(owner_id=owner_id, claim_id=claim_id)
        if not claim_resp:
            raise NotFoundError("Claim not found")

        claim_metadata = DossierClaimMetadata(
            claim_id=claim_resp.id,
            title=claim_resp.title,
            claim_type=claim_resp.claim_type,
            claim_number=claim_resp.claim_number,
            policy_number=claim_resp.policy_number,
            description=claim_resp.description,
            status=claim_resp.status,
            created_at=claim_resp.created_at,
            updated_at=claim_resp.updated_at,
        )

        # 2. Retrieve attached evidentiary documents
        doc_records = self.document_repo.list_documents_for_claim(
            owner_id=owner_id,
            claim_id=claim_id,
            include_archived=False,
        )

        documents_summary: list[DossierDocumentSummary] = []
        for doc in doc_records:
            documents_summary.append(
                DossierDocumentSummary(
                    document_id=doc.get("id", ""),
                    original_filename=doc.get("original_filename", "unnamed"),
                    document_type=doc.get("document_type", "GENERAL_ATTACHMENT"),
                    status=doc.get("status", "UNKNOWN"),
                    size_bytes=int(doc.get("size_bytes", 0)),
                    uploaded_at=doc.get("uploaded_at") or doc.get("created_at"),
                    extracted_entities_count=int(doc.get("extracted_entities_count", 0)),
                    extracted_dates_count=int(doc.get("extracted_dates_count", 0)),
                )
            )

        # 3. Retrieve multi-document intelligence analysis (if available)
        intelligence = self.intelligence_service.get_claim_analysis(owner_id=owner_id, claim_id=claim_id)

        timeline_events: list[DossierTimelineEvent] = []
        discrepancies: list[DossierDiscrepancyItem] = []
        unresolved_questions: list[str] = []
        evidentiary_citations: list[dict[str, Any]] = []
        intelligence_risk = 0.0

        if intelligence:
            intelligence_risk = intelligence.overall_risk_score
            for event in intelligence.timeline:
                timeline_events.append(
                    DossierTimelineEvent(
                        date=event.date,
                        event_description=event.event_description,
                        document_id=event.document_id,
                        source_context=event.source_context,
                    )
                )

            for disc in intelligence.discrepancies:
                citations_data = [cit.model_dump() for cit in disc.citations]
                evidentiary_citations.extend(citations_data)
                discrepancies.append(
                    DossierDiscrepancyItem(
                        id=disc.id,
                        title=disc.title,
                        description=disc.description,
                        category=disc.category.value if hasattr(disc.category, "value") else str(disc.category),
                        severity=disc.severity.value if hasattr(disc.severity, "value") else str(disc.severity),
                        confidence=disc.confidence,
                        citations=citations_data,
                        recommended_action=disc.recommended_action,
                    )
                )

            unresolved_questions.extend(intelligence.unresolved_questions)

        # If no prior timeline exists, generate basic document ingestion timestamps
        if not timeline_events and documents_summary:
            for doc in documents_summary:
                if doc.uploaded_at:
                    timeline_events.append(
                        DossierTimelineEvent(
                            date=doc.uploaded_at[:10],
                            event_description=f"Document uploaded: {doc.original_filename} ({doc.document_type})",
                            document_id=doc.document_id,
                            document_name=doc.original_filename,
                        )
                    )

        # 4. Retrieve graph collusion network and fraud ring clusters
        network_response = await self.fraud_service.get_claim_network(
            owner_id=owner_id,
            claim_id=claim_id,
            max_hops=2,
        )

        associated_fraud_rings: list[DossierFraudRingItem] = []
        max_ring_risk = 0.0
        for ring in network_response.fraud_rings:
            if ring.risk_score > max_ring_risk:
                max_ring_risk = ring.risk_score
            associated_fraud_rings.append(
                DossierFraudRingItem(
                    ring_id=ring.ring_id,
                    pattern=ring.pattern.value if hasattr(ring.pattern, "value") else str(ring.pattern),
                    severity=ring.severity.value if hasattr(ring.severity, "value") else str(ring.severity),
                    risk_score=ring.risk_score,
                    title=ring.title,
                    summary=ring.summary,
                    claim_ids=ring.claim_ids,
                    shared_entities=[e.model_dump() for e in ring.shared_entities],
                    suspicious_indicators=ring.suspicious_indicators,
                    recommended_siu_actions=ring.recommended_siu_actions,
                )
            )

        subgraph_data = {
            "node_count": network_response.node_count,
            "edge_count": network_response.edge_count,
            "nodes": [n.model_dump() for n in network_response.nodes],
            "edges": [e.model_dump() for e in network_response.edges],
        }

        # 5. Compute synthesized overall risk score & fraud classification
        overall_risk_score = round(max(intelligence_risk, max_ring_risk), 2)
        if associated_fraud_rings:
            if overall_risk_score >= 0.8:
                fraud_classification = "CRITICAL_COLLUSION_RING"
            else:
                fraud_classification = "HIGH_RISK_COLLUSION"
        elif discrepancies:
            has_critical = any(d.severity in ("critical", "high") for d in discrepancies)
            fraud_classification = "DISCREPANCY_FLAGGED_HIGH" if has_critical else "DISCREPANCY_FLAGGED_MEDIUM"
        elif overall_risk_score >= 0.5:
            fraud_classification = "ELEVATED_RISK_REVIEW"
        else:
            fraud_classification = "LOW_RISK_STANDARD"

        # 6. Formulate prioritized SIU investigator recommendations
        recommendations: list[DossierRecommendationItem] = []

        # Ring-level high priority recommendations
        for ring in associated_fraud_rings:
            for action in ring.recommended_siu_actions:
                recommendations.append(
                    DossierRecommendationItem(
                        priority="HIGH",
                        category="COLLUSION_INVESTIGATION",
                        action=action,
                        rationale=f"Associated with fraud ring '{ring.title}' ({ring.pattern})",
                    )
                )

        # Discrepancy-level recommendations
        for disc in discrepancies:
            if disc.recommended_action:
                prio = "HIGH" if disc.severity in ("critical", "high") else "MEDIUM"
                recommendations.append(
                    DossierRecommendationItem(
                        priority=prio,
                        category="EVIDENCE_VERIFICATION",
                        action=disc.recommended_action,
                        rationale=f"Contradiction identified: {disc.title}",
                    )
                )

        # Standard baseline recommendation if list is empty
        if not recommendations:
            recommendations.append(
                DossierRecommendationItem(
                    priority="LOW",
                    category="STANDARD_VERIFICATION",
                    action="Verify coverage limits and identity of claimant against policy records.",
                    rationale="Routine SIU baseline validation.",
                )
            )

        # 7. Executive summary synthesis
        if intelligence and intelligence.executive_summary:
            summary_text = intelligence.executive_summary
            if associated_fraud_rings:
                summary_text += f" Network analysis flagged involvement in {len(associated_fraud_rings)} collusion ring(s)."
        elif associated_fraud_rings:
            summary_text = (
                f"Claim is linked to {len(associated_fraud_rings)} detected fraud collusion ring(s) "
                f"with a maximum ring risk score of {max_ring_risk:.2f}."
            )
        else:
            summary_text = (
                f"Forensic claim dossier generated with {len(documents_summary)} attached evidentiary documents. "
                f"Overall risk assessment: {fraud_classification}."
            )

        dossier = ForensicDossierV1(
            dossier_id=f"dossier-{claim_id}",
            claim_id=claim_id,
            owner_id=owner_id,
            generated_at=now,
            overall_risk_score=overall_risk_score,
            fraud_classification=fraud_classification,
            executive_summary=summary_text,
            claim_metadata=claim_metadata,
            documents_summary=documents_summary,
            chronological_timeline=timeline_events,
            contradictions_and_discrepancies=discrepancies,
            associated_fraud_rings=associated_fraud_rings,
            network_subgraph=subgraph_data,
            investigator_recommendations=recommendations,
            unresolved_questions=unresolved_questions,
            evidentiary_citations=evidentiary_citations,
        )

        logger.info(
            "Forensic dossier generated: claim_id=%s risk=%s class=%s docs=%d rings=%d",
            claim_id,
            overall_risk_score,
            fraud_classification,
            len(documents_summary),
            len(associated_fraud_rings),
        )
        return dossier

    def render_markdown(self, dossier: ForensicDossierV1) -> str:
        """Serializes the forensic dossier into a clean, human-readable SIU investigation Markdown document."""
        lines: list[str] = []

        lines.append("# FORENSIC SIU INVESTIGATION DOSSIER")
        lines.append("**Confidential – Insurance Special Investigation Unit (SIU)**\n")
        lines.append(f"- **Dossier ID:** `{dossier.dossier_id}`")
        lines.append(f"- **Claim ID:** `{dossier.claim_id}`")
        lines.append(f"- **Generated At:** {dossier.generated_at}")
        lines.append(f"- **Overall Risk Score:** **{dossier.overall_risk_score:.2f}** / 1.00")
        lines.append(f"- **Fraud Classification:** `{dossier.fraud_classification}`\n")

        lines.append("## 1. Executive Summary")
        lines.append(f"{dossier.executive_summary}\n")

        lines.append("## 2. Claim & Policy Metadata")
        meta = dossier.claim_metadata
        lines.append("| Property | Value |")
        lines.append("| :--- | :--- |")
        lines.append(f"| Title | {meta.title} |")
        lines.append(f"| Claim Number | {meta.claim_number or 'N/A'} |")
        lines.append(f"| Policy Number | {meta.policy_number or 'N/A'} |")
        lines.append(f"| Claim Type | {meta.claim_type} |")
        lines.append(f"| Status | {meta.status} |")
        lines.append(f"| Created Date | {meta.created_at or 'N/A'} |")
        if meta.description:
            lines.append(f"\n*Claim Description:* {meta.description}\n")

        lines.append("## 3. Evidentiary Documents Summary")
        if not dossier.documents_summary:
            lines.append("*No evidentiary documents attached to this claim.*\n")
        else:
            lines.append("| Document ID | Filename | Type | Status | Size | Uploaded |")
            lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for doc in dossier.documents_summary:
                size_kb = f"{doc.size_bytes / 1024:.1f} KB" if doc.size_bytes else "0 KB"
                lines.append(
                    f"| `{doc.document_id}` | {doc.original_filename} | {doc.document_type} | {doc.status} | {size_kb} | {doc.uploaded_at or 'N/A'} |"
                )
            lines.append("")

        lines.append("## 4. Chronological Incident & Claim Timeline")
        if not dossier.chronological_timeline:
            lines.append("*No timeline events reconstructed.*\n")
        else:
            for idx, ev in enumerate(dossier.chronological_timeline, 1):
                doc_note = f" *(Source: `{ev.document_id}`)*" if ev.document_id else ""
                lines.append(f"{idx}. **{ev.date}**: {ev.event_description}{doc_note}")
            lines.append("")

        lines.append("## 5. Cross-Document Contradictions & Discrepancies")
        if not dossier.contradictions_and_discrepancies:
            lines.append("*No cross-document factual contradictions identified.*\n")
        else:
            for disc in dossier.contradictions_and_discrepancies:
                lines.append(f"### Discrepancy: {disc.title}")
                lines.append(f"- **Severity:** `{disc.severity.upper()}` | **Category:** `{disc.category}` | **Confidence:** {disc.confidence * 100:.1f}%")
                lines.append(f"- **Details:** {disc.description}")
                if disc.citations:
                    lines.append("- **Evidentiary Citations:**")
                    for cit in disc.citations:
                        doc_ref = cit.get("document_name") or cit.get("document_id") or "Document"
                        quote = cit.get("quoted_statement") or cit.get("quote", "")
                        lines.append(f"  - *{doc_ref}*: \"{quote}\"")
                if disc.recommended_action:
                    lines.append(f"- **Action Plan:** {disc.recommended_action}")
                lines.append("")

        lines.append("## 6. Collusion & Fraud Ring Analysis")
        if not dossier.associated_fraud_rings:
            lines.append("*No organized fraud rings or collusion clusters detected for this claim.*\n")
        else:
            for ring in dossier.associated_fraud_rings:
                lines.append(f"### Ring: {ring.title} (`{ring.ring_id}`)")
                lines.append(f"- **Pattern:** `{ring.pattern}` | **Severity:** `{ring.severity.upper()}` | **Risk Score:** {ring.risk_score:.2f}")
                lines.append(f"- **Summary:** {ring.summary}")
                lines.append(f"- **Involved Claims:** {', '.join(f'`{cid}`' for cid in ring.claim_ids)}")
                if ring.suspicious_indicators:
                    lines.append("- **Indicators:**")
                    for ind in ring.suspicious_indicators:
                        lines.append(f"  - {ind}")
                lines.append("")

        lines.append("## 7. Actionable SIU Investigator Recommendations")
        for idx, rec in enumerate(dossier.investigator_recommendations, 1):
            lines.append(f"{idx}. `[{rec.priority}]` **{rec.action}** ({rec.category})")
            lines.append(f"   *Rationale:* {rec.rationale}")
        lines.append("")

        if dossier.unresolved_questions:
            lines.append("## 8. Unresolved Questions")
            for q in dossier.unresolved_questions:
                lines.append(f"- {q}")
            lines.append("")

        lines.append("---\n*End of SIU Forensic Dossier. Automated compilation by ClaimGuard Intelligence Engine.*")
        return "\n".join(lines)

    def render_html(self, dossier: ForensicDossierV1) -> str:
        """Serializes the forensic dossier into print-ready, styled HTML with embedded CSS typography."""
        e = html.escape
        meta = dossier.claim_metadata

        # Risk badge color
        if dossier.overall_risk_score >= 0.75:
            risk_color = "#dc2626"
            risk_bg = "#fef2f2"
        elif dossier.overall_risk_score >= 0.4:
            risk_color = "#d97706"
            risk_bg = "#fffbeb"
        else:
            risk_color = "#059669"
            risk_bg = "#ecfdf5"

        html_out = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>SIU Forensic Dossier - {e(dossier.claim_id)}</title>
  <style>
    :root {{
      --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      --text-main: #1e293b;
      --text-muted: #64748b;
      --border-color: #e2e8f0;
      --bg-card: #ffffff;
      --bg-page: #f8fafc;
    }}
    @page {{
      size: A4;
      margin: 1.5cm;
    }}
    body {{
      font-family: var(--font-family);
      color: var(--text-main);
      background-color: var(--bg-page);
      margin: 0;
      padding: 24px;
      line-height: 1.5;
    }}
    .dossier-container {{
      max-width: 900px;
      margin: 0 auto;
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 32px;
      box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    }}
    .header {{
      border-bottom: 2px solid var(--border-color);
      padding-bottom: 20px;
      margin-bottom: 24px;
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
    }}
    .title-block h1 {{
      margin: 0 0 6px 0;
      font-size: 24px;
      color: #0f172a;
      letter-spacing: -0.5px;
    }}
    .badge {{
      display: inline-block;
      padding: 4px 10px;
      border-radius: 9999px;
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .risk-badge {{
      background: {risk_bg};
      color: {risk_color};
      border: 1px solid {risk_color};
      font-size: 16px;
      padding: 8px 16px;
      text-align: right;
    }}
    h2 {{
      font-size: 16px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: #334155;
      border-bottom: 1px solid var(--border-color);
      padding-bottom: 6px;
      margin-top: 28px;
      margin-bottom: 14px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 16px;
      font-size: 14px;
    }}
    th, td {{
      padding: 10px 12px;
      text-align: left;
      border-bottom: 1px solid var(--border-color);
    }}
    th {{
      background-color: #f1f5f9;
      color: #475569;
      font-weight: 600;
    }}
    .timeline-item {{
      padding: 8px 0;
      border-left: 2px solid #cbd5e1;
      padding-left: 14px;
      margin-left: 8px;
      position: relative;
    }}
    .timeline-date {{
      font-weight: 600;
      color: #0f172a;
    }}
    .discrepancy-card, .ring-card {{
      background: #f8fafc;
      border: 1px solid var(--border-color);
      border-radius: 6px;
      padding: 14px;
      margin-bottom: 12px;
    }}
    .recommendation-list {{
      list-style-type: none;
      padding: 0;
    }}
    .recommendation-item {{
      background: #f8fafc;
      border-left: 4px solid #2563eb;
      padding: 10px 14px;
      margin-bottom: 8px;
      border-radius: 0 4px 4px 0;
    }}
    @media print {{
      body {{
        background: none;
        padding: 0;
      }}
      .dossier-container {{
        border: none;
        box-shadow: none;
        padding: 0;
        max-width: 100%;
      }}
      .page-break {{
        page-break-after: always;
      }}
    }}
  </style>
</head>
<body>
  <div class="dossier-container">
    <div class="header">
      <div class="title-block">
        <h1>Forensic SIU Investigation Dossier</h1>
        <div style="color: var(--text-muted); font-size: 13px;">
          Confidential Special Investigation Unit &bull; ClaimGuard Forensic Engine
        </div>
        <div style="margin-top: 8px; font-size: 13px;">
          <strong>Claim ID:</strong> {e(dossier.claim_id)} &bull;
          <strong>Dossier ID:</strong> {e(dossier.dossier_id)} &bull;
          <strong>Date:</strong> {e(dossier.generated_at[:10])}
        </div>
      </div>
      <div class="risk-badge">
        <div>Risk Score</div>
        <strong>{dossier.overall_risk_score:.2f} / 1.00</strong>
        <div style="font-size: 11px; margin-top: 4px;">{e(dossier.fraud_classification)}</div>
      </div>
    </div>

    <h2>1. Executive Summary</h2>
    <p style="font-size: 14px; line-height: 1.6;">{e(dossier.executive_summary)}</p>

    <h2>2. Claim &amp; Policy Metadata</h2>
    <table>
      <tbody>
        <tr><th style="width: 25%;">Title</th><td>{e(meta.title)}</td></tr>
        <tr><th>Claim Number</th><td>{e(meta.claim_number or 'N/A')}</td></tr>
        <tr><th>Policy Number</th><td>{e(meta.policy_number or 'N/A')}</td></tr>
        <tr><th>Claim Type</th><td>{e(meta.claim_type)}</td></tr>
        <tr><th>Status</th><td>{e(meta.status)}</td></tr>
        <tr><th>Description</th><td>{e(meta.description or 'No description provided.')}</td></tr>
      </tbody>
    </table>

    <h2>3. Evidentiary Documents ({len(dossier.documents_summary)})</h2>
"""
        if not dossier.documents_summary:
            html_out += "    <p><em>No documents attached to this claim.</em></p>\n"
        else:
            html_out += """    <table>
      <thead>
        <tr>
          <th>Document ID</th>
          <th>Original Filename</th>
          <th>Type</th>
          <th>Status</th>
          <th>Size</th>
        </tr>
      </thead>
      <tbody>
"""
            for doc in dossier.documents_summary:
                size_kb = f"{doc.size_bytes / 1024:.1f} KB" if doc.size_bytes else "0 KB"
                html_out += f"""        <tr>
          <td><code>{e(doc.document_id)}</code></td>
          <td>{e(doc.original_filename)}</td>
          <td>{e(doc.document_type)}</td>
          <td>{e(doc.status)}</td>
          <td>{size_kb}</td>
        </tr>
"""
            html_out += "      </tbody>\n    </table>\n"

        html_out += f"""    <h2>4. Chronological Incident Timeline ({len(dossier.chronological_timeline)})</h2>\n"""
        if not dossier.chronological_timeline:
            html_out += "    <p><em>No timeline events reconstructed.</em></p>\n"
        else:
            for ev in dossier.chronological_timeline:
                src = f"<span style='color: var(--text-muted); font-size: 12px;'> (Source: {e(ev.document_id or '')})</span>" if ev.document_id else ""
                html_out += f"""    <div class="timeline-item">
      <div class="timeline-date">{e(ev.date)}</div>
      <div>{e(ev.event_description)}{src}</div>
    </div>
"""

        html_out += f"""    <h2>5. Cross-Document Contradictions &amp; Discrepancies ({len(dossier.contradictions_and_discrepancies)})</h2>\n"""
        if not dossier.contradictions_and_discrepancies:
            html_out += "    <p><em>No cross-document contradictions detected.</em></p>\n"
        else:
            for disc in dossier.contradictions_and_discrepancies:
                html_out += f"""    <div class="discrepancy-card">
      <div style="display: flex; justify-content: space-between;">
        <strong>{e(disc.title)}</strong>
        <span class="badge" style="background: #fee2e2; color: #991b1b;">{e(disc.severity)}</span>
      </div>
      <p style="font-size: 13px; margin: 6px 0;">{e(disc.description)}</p>
"""
                if disc.citations:
                    html_out += "      <div style='font-size: 12px; color: var(--text-muted);'><strong>Citations:</strong><ul>"
                    for cit in disc.citations:
                        quote = cit.get("quoted_statement") or cit.get("quote", "")
                        html_out += f"<li>\"{e(quote)}\"</li>"
                    html_out += "</ul></div>"
                if disc.recommended_action:
                    html_out += f"      <div style='font-size: 12px; margin-top: 6px;'><strong>Action:</strong> {e(disc.recommended_action)}</div>"
                html_out += "    </div>\n"

        html_out += f"""    <h2>6. Collusion &amp; Fraud Ring Analysis ({len(dossier.associated_fraud_rings)})</h2>\n"""
        if not dossier.associated_fraud_rings:
            html_out += "    <p><em>No collusion clusters detected for this claim.</em></p>\n"
        else:
            for ring in dossier.associated_fraud_rings:
                html_out += f"""    <div class="ring-card">
      <div style="display: flex; justify-content: space-between;">
        <strong>{e(ring.title)}</strong>
        <span class="badge" style="background: #fef3c7; color: #92400e;">{e(ring.pattern)} &bull; Risk: {ring.risk_score:.2f}</span>
      </div>
      <p style="font-size: 13px; margin: 6px 0;">{e(ring.summary)}</p>
      <div style="font-size: 12px; color: var(--text-muted);"><strong>Involved Claims:</strong> {e(', '.join(ring.claim_ids))}</div>
    </div>
"""

        html_out += f"""    <h2>7. Actionable SIU Action Plan ({len(dossier.investigator_recommendations)})</h2>\n"""
        html_out += "    <ul class=\"recommendation-list\">\n"
        for rec in dossier.investigator_recommendations:
            html_out += f"""      <li class="recommendation-item">
        <div style="font-size: 11px; font-weight: 600; text-transform: uppercase; color: #2563eb;">[{e(rec.priority)}] {e(rec.category)}</div>
        <div style="font-size: 14px; font-weight: 500; margin: 2px 0;">{e(rec.action)}</div>
        <div style="font-size: 12px; color: var(--text-muted);">{e(rec.rationale)}</div>
      </li>
"""
        html_out += "    </ul>\n"

        html_out += """  </div>
</body>
</html>
"""
        return html_out

    async def export_dossier(
        self,
        owner_id: str,
        claim_id: str,
        format: DossierExportFormat,
    ) -> DossierExportResponse:
        """Synthesizes and exports the forensic dossier in the specified serialization format."""
        dossier = await self.generate_dossier(owner_id=owner_id, claim_id=claim_id)

        if format == DossierExportFormat.JSON:
            content = dossier.model_dump_json(indent=2)
            content_type = "application/json"
            filename = f"dossier_{claim_id}.json"
        elif format == DossierExportFormat.MARKDOWN:
            content = self.render_markdown(dossier)
            content_type = "text/markdown; charset=utf-8"
            filename = f"dossier_{claim_id}.md"
        elif format == DossierExportFormat.HTML:
            content = self.render_html(dossier)
            content_type = "text/html; charset=utf-8"
            filename = f"dossier_{claim_id}.html"
        else:
            raise ValueError(f"Unsupported export format: {format}")

        return DossierExportResponse(
            claim_id=claim_id,
            format=format,
            content_type=content_type,
            filename=filename,
            content=content,
        )


dossier_service = DossierService()
