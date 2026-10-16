"""ClaimGuard Services Package."""

from app.services.audit_service import AuditService, audit_service
from app.services.auth_service import AuthService, auth_service
from app.services.claim_intelligence_service import (
    ClaimIntelligenceService,
    claim_intelligence_service,
)
from app.services.claim_service import ClaimService, claim_service
from app.services.document_service import DocumentService, document_service
from app.services.dossier_service import DossierService, dossier_service
from app.services.extraction_service import DocumentExtractionService, extraction_service
from app.services.fraud_ring_service import FraudRingService, fraud_ring_service

__all__ = [
    "AuthService",
    "auth_service",
    "AuditService",
    "audit_service",
    "ClaimService",
    "claim_service",
    "DocumentService",
    "document_service",
    "DocumentExtractionService",
    "extraction_service",
    "ClaimIntelligenceService",
    "claim_intelligence_service",
    "FraudRingService",
    "fraud_ring_service",
    "DossierService",
    "dossier_service",
]

