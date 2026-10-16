import React from 'react';
import { Badge } from '../../components/ui/Badge';
import { CheckCircle2, Calendar, Users, DollarSign } from 'lucide-react';
import type { DocumentExtraction } from '../../types';

interface GroundedFactViewerProps {
  extraction: DocumentExtraction;
}

export const GroundedFactViewer: React.FC<GroundedFactViewerProps> = ({
  extraction,
}) => {
  return (
    <div className="space-y-6">
      {/* Executive Summary */}
      <div className="p-4 rounded-xl bg-slate-50 dark:bg-navy-850 border border-slate-200 dark:border-navy-800 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Document Summary
          </span>
          <Badge
            variant={extraction.confidence_score >= 0.8 ? 'success' : 'warning'}
            size="sm"
          >
            {Math.round(extraction.confidence_score * 100)}% Confidence
          </Badge>
        </div>
        <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
          {extraction.summary}
        </p>
      </div>

      {/* Extracted Dates */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
          <Calendar className="h-4 w-4 text-brand-500" />
          <span>Extracted Dates ({extraction.dates.length})</span>
        </div>

        {extraction.dates.length === 0 ? (
          <p className="text-xs text-slate-400 italic">No specific dates detected in text.</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {extraction.dates.map((d, idx) => (
              <div
                key={idx}
                className="p-3 rounded-xl border border-slate-200 dark:border-navy-800 bg-white dark:bg-navy-900 text-xs space-y-1"
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-900 dark:text-slate-100">
                    {d.value}
                  </span>
                  <Badge variant={d.grounded ? 'success' : 'neutral'} size="sm">
                    {d.grounded ? 'Grounded' : 'Inferred'}
                  </Badge>
                </div>
                <p className="text-[11px] text-slate-500">{d.context}</p>
                {d.page_number && (
                  <span className="text-[10px] text-slate-400 font-mono">
                    Page {d.page_number}
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Extracted Parties & Roles */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
          <Users className="h-4 w-4 text-purple-500" />
          <span>Involved Parties & Roles ({extraction.parties.length})</span>
        </div>

        {extraction.parties.length === 0 ? (
          <p className="text-xs text-slate-400 italic">No individual or organizational entities found.</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {extraction.parties.map((p, idx) => (
              <div
                key={idx}
                className="p-3 rounded-xl border border-slate-200 dark:border-navy-800 bg-white dark:bg-navy-900 text-xs space-y-1"
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-900 dark:text-slate-100 truncate">
                    {p.name}
                  </span>
                  <Badge variant="neutral" size="sm" className="uppercase font-mono text-[10px]">
                    {p.role}
                  </Badge>
                </div>
                {p.role_description && (
                  <p className="text-[11px] text-slate-500">{p.role_description}</p>
                )}
                {p.grounded && (
                  <div className="flex items-center gap-1 text-[10px] text-emerald-600 dark:text-emerald-400 font-medium">
                    <CheckCircle2 className="h-3 w-3" />
                    <span>Verified in source text</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Monetary Figures */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
          <DollarSign className="h-4 w-4 text-emerald-500" />
          <span>Financial Amounts ({extraction.amounts.length})</span>
        </div>

        {extraction.amounts.length === 0 ? (
          <p className="text-xs text-slate-400 italic">No monetary figures extracted.</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {extraction.amounts.map((a, idx) => (
              <div
                key={idx}
                className="p-3 rounded-xl border border-slate-200 dark:border-navy-800 bg-white dark:bg-navy-900 text-xs space-y-1"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-900 dark:text-slate-100">
                    ${a.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })} {a.currency}
                  </span>
                  <Badge variant="neutral" size="sm" className="uppercase font-mono text-[10px]">
                    {a.amount_type.replace(/_/g, ' ')}
                  </Badge>
                </div>
                {a.context && <p className="text-[11px] text-slate-500">{a.context}</p>}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Key Facts Observation List */}
      {extraction.key_facts.length > 0 && (
        <div className="space-y-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Factual Observations
          </span>
          <ul className="space-y-1.5 list-disc list-inside text-xs text-slate-700 dark:text-slate-300">
            {extraction.key_facts.map((fact, idx) => (
              <li key={idx} className="leading-relaxed">
                {fact}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
