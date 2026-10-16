// ==========================================
// ClaimGuard Core TypeScript Type Definitions
// ==========================================

export interface ApiError {
  code: string;
  message: string;
  details?: unknown;
  request_id?: string;
}

// --- Auth & Users ---
export interface User {
  id: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

// --- Claims ---
export type ClaimStatus = 'OPEN' | 'CLOSED' | 'ARCHIVED';

export interface Claim {
  id: string;
  owner_id: string;
  title: string;
  claim_type: string;
  claim_number: string | null;
  policy_number: string | null;
  description: string;
  status: ClaimStatus;
  created_at: string;
  updated_at: string;
  schema_version: number;
}

export interface ClaimCreateRequest {
  title: string;
  claim_type?: string;
  claim_number?: string | null;
  policy_number?: string | null;
  description?: string;
}

export interface ClaimUpdateRequest {
  title?: string;
  claim_type?: string;
  claim_number?: string | null;
  policy_number?: string | null;
  description?: string;
  status?: ClaimStatus;
}

export interface ClaimListResponse {
  items: Claim[];
  total: number;
  skip: number;
  limit: number;
}

// --- Documents ---
export type IngestionStatus =
  | 'RECEIVED'
  | 'VALIDATING'
  | 'STORED'
  | 'EXTRACTING'
  | 'INDEXING'
  | 'MATCHING_CLAIM'
  | 'ANALYZING'
  | 'READY_FOR_REVIEW'
  | 'COMPLETED'
  | 'FAILED_RETRYABLE'
  | 'RETRYING'
  | 'FAILED_FINAL'
  | 'ARCHIVED';

export interface DocumentItem {
  id: string;
  claim_id: string;
  owner_id: string;
  object_key: string;
  content_hash: string;
  document_type: string;
  original_filename: string;
  size_bytes: number;
  mime_type: string;
  uploaded_at: string;
  version: number;
  status: IngestionStatus;
  schema_version: number;
}

export interface DocumentListResponse {
  items: DocumentItem[];
  total: number;
}

export interface PresignedUrlResponse {
  document_id: string;
  download_url: string;
  expires_in_seconds: number;
}

export interface ExtractedDate {
  value: string;
  context: string;
  grounded: boolean;
  page_number?: number | null;
  char_start?: number | null;
  char_end?: number | null;
}

export interface ExtractedParty {
  name: string;
  role: string;
  role_description?: string | null;
  grounded: boolean;
  page_number?: number | null;
  char_start?: number | null;
  char_end?: number | null;
}

export interface ExtractedAmount {
  amount: number;
  currency: string;
  amount_type: string;
  context?: string | null;
  grounded: boolean;
  page_number?: number | null;
  char_start?: number | null;
  char_end?: number | null;
}

export interface DocumentExtraction {
  document_type: string;
  summary: string;
  dates: ExtractedDate[];
  parties: ExtractedParty[];
  amounts: ExtractedAmount[];
  key_facts: string[];
  confidence_score: number;
  all_entities_grounded: boolean;
}

// --- Intelligence & Cross-Document Analysis ---
export interface DocumentCitation {
  document_id: string;
  document_name?: string | null;
  quoted_statement: string;
  page_number?: number | null;
}

export type DiscrepancySeverity = 'low' | 'medium' | 'high' | 'critical';

export interface ClaimDiscrepancy {
  id: string;
  title: string;
  description: string;
  category: string;
  severity: DiscrepancySeverity;
  confidence: number;
  citations: DocumentCitation[];
  recommended_action?: string | null;
}

export interface TimelineEvent {
  date: string;
  event_description: string;
  document_id: string;
  source_context?: string | null;
}

export interface ClaimIntelligenceAnalysis {
  claim_id: string;
  overall_risk_score: number;
  executive_summary: string;
  timeline: TimelineEvent[];
  discrepancies: ClaimDiscrepancy[];
  unresolved_questions: string[];
  confidence_score: number;
  analyzed_at?: string | null;
}

// --- Fraud Rings & Knowledge Graph ---
export interface FraudRingNode {
  id: string;
  label: string;
  type: 'claim' | 'person' | 'organization';
  is_target?: boolean | null;
  properties: Record<string, unknown>;
}

export interface FraudRingEdge {
  source: string;
  target: string;
  type: string;
  properties: Record<string, unknown>;
}

export interface SharedEntitySummary {
  name: string;
  entity_type: string;
  claim_count: number;
  roles: string[];
}

export interface FraudRingAnalysis {
  ring_id: string;
  pattern: string;
  severity: DiscrepancySeverity;
  risk_score: number;
  title: string;
  summary: string;
  claim_ids: string[];
  shared_entities: SharedEntitySummary[];
  suspicious_indicators: string[];
  recommended_siu_actions: string[];
  detected_at?: string | null;
  network_subgraph?: Record<string, unknown> | null;
}

export interface ClaimFraudNetworkResponse {
  claim_id: string;
  nodes: FraudRingNode[];
  edges: FraudRingEdge[];
  fraud_rings: FraudRingAnalysis[];
  node_count: number;
  edge_count: number;
}

export interface FraudRingListResponse {
  rings: FraudRingAnalysis[];
  total: number;
}

// --- Forensic Dossier ---
export interface DossierClaimMetadata {
  claim_id: string;
  title: string;
  claim_type: string;
  claim_number?: string | null;
  policy_number?: string | null;
  description: string;
  status: string;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface DossierDocumentSummary {
  document_id: string;
  original_filename: string;
  document_type: string;
  status: string;
  size_bytes: number;
  uploaded_at?: string | null;
  extracted_entities_count: number;
  extracted_dates_count: number;
}

export interface DossierRecommendationItem {
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
  category: 'INTERVIEW' | 'EVIDENCE_COLLECTION' | 'FORENSIC_AUDIT' | 'LEGAL' | string;
  action: string;
  rationale: string;
}

export type DossierExportFormat = 'json' | 'markdown' | 'html';

export interface ForensicDossier {
  dossier_id: string;
  claim_id: string;
  owner_id: string;
  generated_at: string;
  overall_risk_score: number;
  fraud_classification: string;
  executive_summary: string;
  claim_metadata: DossierClaimMetadata;
  documents_summary: DossierDocumentSummary[];
  chronological_timeline: TimelineEvent[];
  contradictions_and_discrepancies: ClaimDiscrepancy[];
  associated_fraud_rings: FraudRingAnalysis[];
  network_subgraph?: Record<string, unknown> | null;
  investigator_recommendations: DossierRecommendationItem[];
  unresolved_questions: string[];
  evidentiary_citations: Record<string, unknown>[];
}

// --- Health ---
export interface SystemHealthResponse {
  status: 'ready' | 'unhealthy';
  services: {
    postgres: 'healthy' | 'unhealthy';
    falkordb: 'healthy' | 'unhealthy';
    s3: 'healthy' | 'unhealthy';
  };
}

// --- Audit ---
export interface AuditEventItem {
  id: string;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  ip?: string | null;
  request_id?: string | null;
  outcome: string;
  event_metadata: Record<string, unknown>;
  timestamp: string;
}

export interface AuditTrailResponse {
  total: number;
  items: AuditEventItem[];
}
