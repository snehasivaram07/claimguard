import React, { useState } from 'react';
import {
  ShieldAlert,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Users,
  CheckCircle2,
} from 'lucide-react';
import type { FraudRingAnalysis } from '../../types';

interface FraudRingAlertBannerProps {
  fraudRings: FraudRingAnalysis[];
}

export const FraudRingAlertBanner: React.FC<FraudRingAlertBannerProps> = ({ fraudRings }) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(false);
  const [activeRingIndex, setActiveRingIndex] = useState<number>(0);

  if (!fraudRings || fraudRings.length === 0) {
    return null;
  }

  const activeRing = fraudRings[activeRingIndex] || fraudRings[0];
  const severity = activeRing.severity || 'high';
  const riskPct = Math.round((activeRing.risk_score || 0.85) * 100);

  // Severity styling
  const isCritical = severity.toLowerCase() === 'critical';
  const borderBg = isCritical
    ? 'border-rose-500/40 bg-rose-500/10 text-rose-700 dark:text-rose-300'
    : 'border-amber-500/40 bg-amber-500/10 text-amber-700 dark:text-amber-300';

  const badgeBg = isCritical
    ? 'bg-rose-500 text-white shadow-xs shadow-rose-500/30'
    : 'bg-amber-500 text-white shadow-xs shadow-amber-500/30';

  const formatPattern = (pattern: string) => {
    return pattern
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (char) => char.toUpperCase());
  };

  return (
    <div className={`rounded-xl border p-4 transition-all shadow-sm ${borderBg}`}>
      {/* Banner Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-white/20 dark:bg-black/20 shrink-0 mt-0.5">
            <ShieldAlert className="h-5 w-5" />
          </div>

          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className={`text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full ${badgeBg}`}>
                {severity} Severity
              </span>
              <span className="text-xs font-bold font-mono px-2 py-0.5 rounded bg-black/10 dark:bg-white/10">
                {formatPattern(activeRing.pattern)}
              </span>
              <span className="text-xs font-semibold">
                Risk Score: <strong className="underline">{riskPct}%</strong>
              </span>
            </div>

            <h4 className="text-sm font-bold tracking-tight text-slate-900 dark:text-slate-100">
              {activeRing.title}
            </h4>
            <p className="text-xs opacity-90 leading-relaxed max-w-2xl">
              {activeRing.summary}
            </p>
          </div>
        </div>

        {/* Expand / Multi-ring Selector */}
        <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
          {fraudRings.length > 1 && (
            <div className="flex items-center gap-1 bg-black/10 dark:bg-white/10 px-2 py-1 rounded text-xs">
              <span className="text-[11px] font-medium">Ring:</span>
              <select
                value={activeRingIndex}
                onChange={(e) => setActiveRingIndex(Number(e.target.value))}
                className="bg-transparent text-xs font-bold focus:outline-none cursor-pointer"
              >
                {fraudRings.map((r, i) => (
                  <option key={r.ring_id} value={i} className="text-slate-900 bg-white dark:bg-navy-900 dark:text-slate-100">
                    Ring {i + 1} ({r.severity})
                  </option>
                ))}
              </select>
            </div>
          )}

          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-white/80 dark:bg-navy-900/80 hover:bg-white dark:hover:bg-navy-900 text-slate-800 dark:text-slate-200 border border-black/10 dark:border-white/10 transition-all shadow-xs"
          >
            <span>{isExpanded ? 'Hide Forensics' : 'View Collusion Details'}</span>
            {isExpanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          </button>
        </div>
      </div>

      {/* Expanded Forensic Dossier Information */}
      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-black/10 dark:border-white/10 grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          {/* Col 1: Shared Entities & Claims */}
          <div className="space-y-2 p-3 rounded-lg bg-white/60 dark:bg-navy-950/60 border border-black/5 dark:border-white/5">
            <div className="font-bold uppercase tracking-wider flex items-center gap-1.5 text-slate-800 dark:text-slate-200">
              <Users className="h-3.5 w-3.5 text-brand-500" />
              Shared Collusion Entities ({activeRing.shared_entities?.length || 0})
            </div>
            <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
              {activeRing.shared_entities?.map((e, idx) => (
                <div
                  key={idx}
                  className="p-1.5 rounded bg-white dark:bg-navy-900 border border-slate-200/60 dark:border-navy-800 text-[11px] flex items-center justify-between"
                >
                  <div>
                    <span className="font-bold text-slate-900 dark:text-slate-100">{e.name}</span>
                    <span className="text-slate-400 text-[10px] ml-1.5">({e.entity_type})</span>
                  </div>
                  <span className="font-mono text-[10px] font-bold px-1.5 py-0.2 rounded bg-brand-500/10 text-brand-500 border border-brand-500/20">
                    {e.claim_count} claims
                  </span>
                </div>
              ))}
            </div>

            <div className="pt-1 text-[11px] text-slate-500 dark:text-slate-400">
              <span className="font-semibold text-slate-700 dark:text-slate-300">Connected Claims: </span>
              {activeRing.claim_ids?.join(', ') || 'N/A'}
            </div>
          </div>

          {/* Col 2: Suspicious Indicators */}
          <div className="space-y-2 p-3 rounded-lg bg-white/60 dark:bg-navy-950/60 border border-black/5 dark:border-white/5">
            <div className="font-bold uppercase tracking-wider flex items-center gap-1.5 text-slate-800 dark:text-slate-200">
              <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
              Suspicious Topologies
            </div>
            <ul className="space-y-1.5 text-[11px] leading-relaxed max-h-40 overflow-y-auto pr-1">
              {activeRing.suspicious_indicators?.map((indicator, idx) => (
                <li key={idx} className="flex items-start gap-1.5 text-slate-700 dark:text-slate-300">
                  <span className="text-amber-500 font-bold shrink-0 mt-0.5">•</span>
                  <span>{indicator}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Col 3: Recommended SIU Actions */}
          <div className="space-y-2 p-3 rounded-lg bg-white/60 dark:bg-navy-950/60 border border-black/5 dark:border-white/5">
            <div className="font-bold uppercase tracking-wider flex items-center gap-1.5 text-slate-800 dark:text-slate-200">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
              Recommended SIU Protocol
            </div>
            <ul className="space-y-1.5 text-[11px] leading-relaxed max-h-40 overflow-y-auto pr-1">
              {activeRing.recommended_siu_actions?.map((action, idx) => (
                <li key={idx} className="flex items-start gap-1.5 text-slate-700 dark:text-slate-300">
                  <span className="text-emerald-500 font-bold shrink-0 mt-0.5">✓</span>
                  <span>{action}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};
