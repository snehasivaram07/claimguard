# ClaimGuard — AI-Powered Insurance Claim Forensics Platform (Frontend)

ClaimGuard is an enterprise-grade, responsive Special Investigation Unit (SIU) frontend web application. It connects human claims adjusters and fraud investigators to real-time AI intelligence, cross-document factual contradiction detection, and FalkorDB knowledge graph collusion forensics.

---

## 🚀 Key Technologies & Stack

- **Framework**: [React 19](https://react.dev/) + [Vite 8](https://vite.dev/)
- **Language**: [TypeScript](https://www.typescriptlang.org/) (Strict mode, `verbatimModuleSyntax`)
- **Styling**: [Tailwind CSS v3](https://tailwindcss.com/) with a custom Dark Navy design system and Clean Light theme
- **Data Fetching & Cache**: [TanStack Query v5](https://tanstack.com/query/latest)
- **Graph Visualization**: [Cytoscape.js](https://js.cytoscape.org/) (Force-directed, concentric, circular, and hierarchical layouts)
- **HTTP Client**: [Axios](https://axios-http.com/) (Centralized single-flight refresh on `401`, Bearer JWT injection, `X-Request-ID` correlation)
- **Icons**: [Lucide React](https://lucide.dev/)
- **Routing**: [React Router v7](https://reactrouter.com/)

---

## 🎨 Design System & Palette

ClaimGuard defaults to a **Dark Navy** forensic aesthetic with full support for a daylight **Clean Light** mode:

| Token | Dark Navy | Clean Light | Usage |
|---|---|---|---|
| `--bg-main` | `#070c18` | `#f8fafc` | Application canvas backdrop |
| `--bg-card` | `#0b1324` | `#ffffff` | Primary container cards, modals, headers |
| `--bg-card-subtle` | `#101a30` | `#f1f5f9` | Nested panels, tables, code blocks |
| `--border-color` | `#1d2c4e` | `#e2e8f0` | Card borders, dividers, table rules |
| `--text-primary` | `#f8fafc` | `#0f172a` | High-contrast headings and body text |
| `--text-secondary`| `#cbd5e1` | `#475569` | Metadata, subtitles, helper text |
| `--primary` | `#38bdf8` | `#0284c7` | Brand cyan accents, buttons, active tabs |
| `--accent` | `#0284c7` | `#38bdf8` | Secondary interactive highlights |

> **Investigative Safeguard Standard:**
> AI-generated anomaly scores, contradictory statements, and graph clusters are presented as **investigative leads** to assist certified human examiners, never as definitive legal proof of guilt.

---

## 🗺 Application Architecture & Features

### 1. Authentication & Session Management
- **Routes**: `/login`, `/register`
- **Guards**: `AuthGuard` (protects internal routes) and `GuestGuard` (redirects authenticated users)
- **Session Lifecycle**: Auto-refresh on 401 via single-flight mutex queue; proactive token storage in `localStorage`.
- **Tenant Isolation**: Claims access is cryptographically partitioned per owner ID with zero-leakage 404 policies.

### 2. Executive Caseload Dashboard (`/`)
- **Live Health Telemetry**: Real-time status for PostgreSQL, FalkorDB, and MinIO/S3.
- **KPI Metrics Strip**: Active claims count, critical fraud alerts, documents ingested, and average cycle times.
- **Priority Action Center**: High-risk claims flagged for urgent examination under oath (EUO) or field appraisal.
- **Recent Caseload Feed**: Quick-access stream of recently updated claims.

### 3. Claims Caseload Directory (`/claims`)
- **Server Pagination**: Skip/limit pagination with customizable page size (10, 25, 50).
- **Faceted Filtering**: Filter by Claim Status (`OPEN`, `INVESTIGATING`, `CLOSED`, `ARCHIVED`) and Claim Type (`AUTO_ACCIDENT`, `PROPERTY_DAMAGE`, `WORKERS_COMP`, `MEDICAL_MALPRACTICE`).
- **Full-Text Search**: Search across Title, Claim Number, Policy Number, and Claim ID.
- **CRUD Operations**: Create Claim modal, Edit Metadata modal, and soft-delete Archive dialog.

### 4. Claim 360 Investigation Workspace (`/claims/:claimId`)
Tabbed unified investigative environment featuring 5 forensic modules:
- **Tab 1: Overview & Case Narrative**:
  - Narrative description, financial reserves, claim metadata.
  - Claim-specific audit trail tracking all actions on this claim with IP and Request ID.
- **Tab 2: Document Hub & Entity Grounding**:
  - Drag-and-drop file uploader supporting up to 25 MB (`.pdf`, `.png`, `.jpg`, `.txt`, `.eml`).
  - Document status tracking (`EXTRACTING`, `INDEXING`, `READY_FOR_REVIEW`, `COMPLETED`).
  - Presigned URL download generator (S3 download links expire safely in 300 seconds).
  - Grounded Fact Viewer drawer showing AI-extracted dates, parties, and amounts with exact page numbers.
- **Tab 3: Reconstructed Incident Timeline & Contradiction Board**:
  - AI Composite Fraud Risk Score gauge (`0–100%`) with severity tiers (Low, Moderate, High, Critical).
  - Chronological vertical timeline connecting events extracted across all attached documents.
  - Side-by-side factual contradiction cards comparing conflicting verbatim statements (Source A vs Source B) with page citations.
  - Targeted investigator interview & deposition questions with one-click copy.
- **Tab 4: Interactive Fraud Network Graph**:
  - Cytoscape.js canvas visualizing 1-hop and 2-hop graph neighborhood.
  - Nodes: Focal Target Claim (diamond), Connected Claims (round rectangle), Persons (circle), Organizations (hexagon).
  - Edges: Directed arrows labeled with relationship types (`INVOLVES_PERSON`, `INVOLVES_ORGANIZATION`).
  - Layout switchers: Force-Directed (`cose`), Concentric Rings (`concentric`), Circular, and Hierarchical.
  - Real-time search highlighting and slide-over Node Inspector panel with multi-claim bridge.
- **Tab 5: Forensic SIU Dossier & Multi-Format Export Center**:
  - Forensic case briefing narrative.
  - Prioritized SIU action checklist with interactive task completion tracking and priority badges.
  - Multi-Format Export Center providing one-click file downloads:
    - **Print-Ready HTML (`.html`)**: Formatted for browser printing (Ctrl+P to PDF) and legal counsel binders.
    - **Standard Markdown (`.md`)**: Structured Markdown tables and cited verbatim quotes.
    - **Forensic JSON (`.json`)**: Raw structured JSON schema for case management systems.

### 5. Global Fraud Rings Explorer (`/fraud-rings`)
- Tenant-wide graph analytics scanning multi-claim collusion networks.
- Minimum shared entities threshold selector (`2+`, `3+`, `4+`).
- Topologies: Staged Collisions, Provider Fraud, Repeat Claimants, Role Reversals, Identity Sharing.
- Shared entities matrix and direct links to all involved claims.

### 6. Security & Audit Activity Trail (`/audit`)
- Immutable, tamper-proof audit log tracking logins, document uploads, and dossier exports.
- Request trace correlation (`X-Request-ID`) and client IP logging.
- Interactive modal displaying raw syntax-highlighted event metadata JSON.
- Server-side pagination with page size controls.

### 7. Settings & Cluster Telemetry (`/settings`)
- Investigator profile credentials and assigned role.
- Interface theme toggle (Dark Navy vs Clean Light).
- Live cluster heartbeat check (PostgreSQL, FalkorDB, MinIO S3).
- Session lifecycle policies and Sign Out action.

---

## 🛠 Getting Started & Local Development

### Prerequisites
- Node.js `v20+` or `v22+`
- npm `v10+`
- Backend API running on `http://localhost:8000` (FastAPI + PostgreSQL + FalkorDB + MinIO)

### Installation
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
```

### Environment Configuration
Create a `.env` file in `frontend/` (or copy from `.env.example`):
```env
VITE_API_URL=http://localhost:8000
```

### Running Locally
```bash
# Start Vite development server with HMR
npm run dev

# App runs at: http://localhost:5173
```

### Building for Production
```bash
# Type check and build production bundle
npm run build

# Output generated in frontend/dist/
# Preview production build locally:
npm run preview
```

### Linting
```bash
# Run oxlint across all source files
npm run lint
```

---

## 📦 Production Bundle Structure

Optimized chunking configuration separates heavy dependencies into dedicated vendor chunks for fast load times:

```
dist/index.html                           1.24 kB │ gzip:   0.59 kB
dist/assets/index.css                    50.08 kB │ gzip:   8.98 kB
dist/assets/rolldown-runtime.js           0.72 kB │ gzip:   0.42 kB
dist/assets/icons.js                     31.79 kB │ gzip:  10.71 kB
dist/assets/index.js                    232.01 kB │ gzip:  43.88 kB
dist/assets/vendor.js                   363.89 kB │ gzip: 116.31 kB
dist/assets/cytoscape.js                434.75 kB │ gzip: 137.75 kB
✓ built in ~1.30s
```

---

## 🔒 Security & Compliance Standards

- **Multi-Tenant Boundary**: All API requests pass through the current user's authenticated session. Queries enforce `owner_id` scoping in PostgreSQL and Cypher graph queries.
- **Presigned URLs**: S3 download links expire automatically after 300 seconds; URLs are never stored in browser storage.
- **Audit Logging**: Every sensitive action (`CLAIM_VIEWED`, `CLAIM_ANALYSIS_COMPLETED`, `DOSSIER_EXPORTED`) records an immutable audit event with client IP and request trace ID.
