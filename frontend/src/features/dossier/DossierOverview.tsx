import React, { useState } from 'react';
import {
  FileCheck2,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Calendar,
  Copy,
  Check,
  Scale,
} from 'lucide-react';
import type { ForensicDossier } from '../../types';

interface DossierOverviewProps {
  dossier: ForensicDossier;
}

export const DossierOverview: React.FC<DossierOverviewProps> = ({ dossier }) => {
  const [copiedId, setCopiedId] = useState<boolean>(false);

  const riskPct = Math.round(dossier.overall_risk_score * 100);
  const classification = dossier.fraud_classification || 'LOW_RISK';

  // Classification styling
  let badgeStyle = 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20';
  let Icon = ShieldCheck;

  if (classification.includes('CRITICAL')) {
    badgeStyle = 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/30';
    Icon = ShieldAlert;
  } else if (classification.includes('HIGH')) {
    badgeStyle = 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30';
    Icon = AlertTriangle;
  } else if (classification.includes('MODERATE')) {
    badgeStyle = 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 border-yellow-500/30';
    Icon = AlertTriangle;
  }

  const copyDossierId = () => {
    navigator.clipboard.writeText(dossier.dossier_id);
    setCopiedId(true);
    setTimeout(() => setCopiedId(false), 2000);
  };

  const formattedDate = new Date(dossier.generated_at).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700/80 rounded-xl p-5 shadow-sm space-y-5">
      {/* Top Meta Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100 dark:border-navy-800">
        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex items-center gap-1.5 bg-slate-100 dark:bg-navy-950 px-2.5 py-1 rounded-lg border border-slate-200 dark:border-navy-800 text-xs font-mono text-slate-600 dark:text-slate-300">
            <span className="font-bold">Dossier ID:</span>
            <span className="truncate max-w-[140px] sm:max-w-[200px]" title={dossier.dossier_id}>
              {dossier.dossier_id}
            </span>
            <button
              onClick={copyDossierId}
              className="p-1 hover:text-brand-500 transition-colors ml-1"
              title="Copy Dossier ID"
            >
              {copiedId ? <Check className="h-3 w-3 text-emerald-500" /> : <Copy className="h-3 w-3 text-slate-400" />}
            </button>
          </div>

          <span className="text-xs text-slate-400 flex items-center gap-1">
            <Calendar className="h-3.5 w-3.5" />
            Generated {formattedDate}
          </span>
        </div>

        {/* Risk Classification Badge */}
        <div className="flex items-center gap-2">
          <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-extrabold uppercase tracking-wider border ${badgeStyle}`}>
            <Icon className="h-3.5 w-3.5" />
            {classification.replace(/_/g, ' ')}
          </span>
          <div className="px-2.5 py-1 rounded-full text-xs font-bold font-mono bg-slate-100 dark:bg-navy-800 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-navy-700">
            Risk: {riskPct}%
          </div>
        </div>
      </div>

      {/* Claim Context Header */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
        <div className="p-3 rounded-lg bg-slate-50 dark:bg-navy-950/70 border border-slate-200 dark:border-navy-800 space-y-0.5">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Claim Title</span>
          <div className="font-bold text-slate-900 dark:text-slate-100 truncate" title={dossier.claim_metadata.title}>
            {dossier.claim_metadata.title}
          </div>
        </div>

        <div className="p-3 rounded-lg bg-slate-50 dark:bg-navy-950/70 border border-slate-200 dark:border-navy-800 space-y-0.5">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Claim Number</span>
          <div className="font-bold text-slate-900 dark:text-slate-100 font-mono">
            {dossier.claim_metadata.claim_number || 'N/A'}
          </div>
        </div>

        <div className="p-3 rounded-lg bg-slate-50 dark:bg-navy-950/70 border border-slate-200 dark:border-navy-800 space-y-0.5">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Policy Number</span>
          <div className="font-bold text-slate-900 dark:text-slate-100 font-mono">
            {dossier.claim_metadata.policy_number || 'N/A'}
          </div>
        </div>

        <div className="p-3 rounded-lg bg-slate-50 dark:bg-navy-950/70 border border-slate-200 dark:border-navy-800 space-y-0.5">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Claim Type / Status</span>
          <div className="font-bold text-slate-900 dark:text-slate-100 uppercase">
            {dossier.claim_metadata.claim_type} • {dossier.claim_metadata.status}
          </div>
        </div>
      </div>

      {/* Executive Brief Narrative */}
      <div className="space-y-2">
        <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider flex items-center gap-1.5">
          <FileCheck2 className="h-4 w-4 text-brand-500" />
          Forensic Executive Briefing
        </h4>
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-navy-950/80 border border-slate-200/80 dark:border-navy-800 text-xs sm:text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-normal">
          {dossier.executive_summary}
        </div>
      </div>

      {/* Evidentiary Metrics Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5 pt-1 text-center">
        <div className="p-2.5 rounded-lg bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-800 shadow-xs">
          <div className="text-[10px] uppercase font-bold text-slate-400">Documents</div>
          <div className="text-base font-extrabold text-slate-800 dark:text-slate-200 mt-0.5">
            {dossier.documents_summary.length}
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-800 shadow-xs">
          <div className="text-[10px] uppercase font-bold text-slate-400">Timeline Events</div>
          <div className="text-base font-extrabold text-slate-800 dark:text-slate-200 mt-0.5">
            {dossier.chronological_timeline.length}
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-800 shadow-xs">
          <div className="text-[10px] uppercase font-bold text-slate-400">Contradictions</div>
          <div className="text-base font-extrabold text-rose-600 dark:text-rose-400 mt-0.5">
            {dossier.contradictions_and_discrepancies.length}
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-800 shadow-xs">
          <div className="text-[10px] uppercase font-bold text-slate-400">Fraud Rings</div>
          <div className="text-base font-extrabold text-purple-600 dark:text-purple-400 mt-0.5">
            {dossier.associated_fraud_rings.length}
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-800 shadow-xs col-span-2 sm:col-span-1">
          <div className="text-[10px] uppercase font-bold text-slate-400">SIU Actions</div>
          <div className="text-base font-extrabold text-emerald-600 dark:text-emerald-400 mt-0.5">
            {dossier.investigator_recommendations.length}
          </div>
        </div>
      </div>

      {/* Legal & Subrogation Note */}
      <div className="flex items-start gap-2.5 p-3 rounded-lg bg-slate-50 dark:bg-navy-950/60 border border-slate-200 dark:border-navy-800 text-xs text-slate-600 dark:text-slate-400">
        <Scale className="h-4 w-4 text-brand-500 shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <span className="font-semibold text-slate-800 dark:text-slate-200">Legal Admissibility Protocol: </span>
          All citations and timestamps are recorded in immutable audit logs with SHA-256 content hashes for chain-of-custody verification during subrogation or litigation.
        </p>
      </div>
    </div>
  );
};
