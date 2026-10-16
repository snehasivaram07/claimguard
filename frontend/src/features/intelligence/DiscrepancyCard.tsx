import React from 'react';
import {
  AlertTriangle,
  Calendar,
  DollarSign,
  MapPin,
  Users,
  FileText,
  Lightbulb,
  Quote,
  ShieldAlert,
} from 'lucide-react';
import type { ClaimDiscrepancy, DiscrepancySeverity } from '../../types';

interface DiscrepancyCardProps {
  discrepancy: ClaimDiscrepancy;
  documentNameMap?: Record<string, string>;
}

export const DiscrepancyCard: React.FC<DiscrepancyCardProps> = ({
  discrepancy,
  documentNameMap = {},
}) => {
  // Category mapping
  const getCategoryMeta = (cat: string) => {
    switch (cat.toLowerCase()) {
      case 'date_inconsistency':
        return { label: 'Date Inconsistency', icon: Calendar, color: 'text-amber-500' };
      case 'amount_mismatch':
        return { label: 'Amount Mismatch', icon: DollarSign, color: 'text-emerald-500' };
      case 'damage_location_conflict':
        return { label: 'Damage Location Conflict', icon: MapPin, color: 'text-rose-500' };
      case 'party_involvement_conflict':
        return { label: 'Party Involvement Conflict', icon: Users, color: 'text-purple-500' };
      case 'factual_contradiction':
        return { label: 'Factual Contradiction', icon: AlertTriangle, color: 'text-rose-500' };
      default:
        return { label: cat.replace(/_/g, ' '), icon: FileText, color: 'text-slate-400' };
    }
  };

  // Severity styles
  const getSeverityStyle = (sev: DiscrepancySeverity) => {
    switch (sev) {
      case 'critical':
        return {
          cardBorder: 'border-l-4 border-l-rose-500',
          badge: 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/30',
        };
      case 'high':
        return {
          cardBorder: 'border-l-4 border-l-amber-500',
          badge: 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30',
        };
      case 'medium':
        return {
          cardBorder: 'border-l-4 border-l-yellow-500',
          badge: 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 border-yellow-500/30',
        };
      case 'low':
      default:
        return {
          cardBorder: 'border-l-4 border-l-blue-500',
          badge: 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/30',
        };
    }
  };

  const categoryMeta = getCategoryMeta(discrepancy.category);
  const CategoryIcon = categoryMeta.icon;
  const severityStyle = getSeverityStyle(discrepancy.severity);
  const confidencePercent = Math.round(discrepancy.confidence * 100);

  const getDocName = (docId: string, fallbackName?: string | null) => {
    if (fallbackName) return fallbackName;
    if (documentNameMap[docId]) return documentNameMap[docId];
    return `Document #${docId.slice(0, 8)}`;
  };

  return (
    <div
      className={`bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700/80 rounded-xl p-5 shadow-sm space-y-4 transition-all hover:shadow-md ${severityStyle.cardBorder}`}
    >
      {/* Card Header: Metadata Pills */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-100 dark:border-navy-800">
        <div className="flex items-center gap-2 flex-wrap">
          {/* Severity Badge */}
          <span
            className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider border ${severityStyle.badge}`}
          >
            <ShieldAlert className="h-3 w-3" />
            {discrepancy.severity}
          </span>

          {/* Category Pill */}
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 dark:bg-navy-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-navy-700">
            <CategoryIcon className={`h-3 w-3 ${categoryMeta.color}`} />
            {categoryMeta.label}
          </span>
        </div>

        {/* Confidence Meter Pill */}
        <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 font-medium bg-slate-50 dark:bg-navy-950/60 px-2 py-0.5 rounded border border-slate-200/80 dark:border-navy-800">
          <span>Confidence:</span>
          <span className="font-bold text-slate-800 dark:text-slate-200">
            {confidencePercent}%
          </span>
        </div>
      </div>

      {/* Discrepancy Title & Description */}
      <div className="space-y-1.5">
        <h4 className="text-base font-bold text-slate-900 dark:text-slate-100">
          {discrepancy.title}
        </h4>
        <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          {discrepancy.description}
        </p>
      </div>

      {/* Citations / Conflicting Statements Comparison */}
      {discrepancy.citations && discrepancy.citations.length > 0 && (
        <div className="space-y-2 pt-1">
          <div className="text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <Quote className="h-3 w-3 text-brand-500" />
            Conflicting Evidence Quotes
          </div>

          {/* If 2 citations, render a 2-column side-by-side comparison */}
          {discrepancy.citations.length === 2 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {discrepancy.citations.map((citation, index) => {
                const docName = getDocName(citation.document_id, citation.document_name);
                const isFirst = index === 0;

                return (
                  <div
                    key={`${citation.document_id}-${index}`}
                    className={`p-3 rounded-lg border text-xs space-y-2 ${
                      isFirst
                        ? 'bg-blue-500/5 dark:bg-blue-500/10 border-blue-500/20'
                        : 'bg-rose-500/5 dark:bg-rose-500/10 border-rose-500/20'
                    }`}
                  >
                    <div className="flex items-center justify-between text-[11px]">
                      <span
                        className={`font-semibold uppercase tracking-wider ${
                          isFirst
                            ? 'text-blue-700 dark:text-blue-400'
                            : 'text-rose-700 dark:text-rose-400'
                        }`}
                      >
                        Evidence Source {isFirst ? 'A' : 'B'}
                      </span>
                      {citation.page_number && (
                        <span className="text-slate-500 font-mono text-[10px] bg-white dark:bg-navy-900 px-1.5 py-0.5 rounded border border-slate-200 dark:border-navy-700">
                          Page {citation.page_number}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-1.5 text-slate-700 dark:text-slate-300 font-medium truncate">
                      <FileText className="h-3.5 w-3.5 shrink-0 text-slate-400" />
                      <span className="truncate" title={docName}>
                        {docName}
                      </span>
                    </div>

                    <blockquote className="italic text-slate-800 dark:text-slate-200 pl-2.5 border-l-2 border-slate-300 dark:border-navy-600 text-xs leading-relaxed">
                      "{citation.quoted_statement}"
                    </blockquote>
                  </div>
                );
              })}
            </div>
          ) : (
            /* If 1 or >2 citations, render stacked list */
            <div className="space-y-2">
              {discrepancy.citations.map((citation, index) => {
                const docName = getDocName(citation.document_id, citation.document_name);

                return (
                  <div
                    key={`${citation.document_id}-${index}`}
                    className="p-3 rounded-lg bg-slate-50 dark:bg-navy-950/70 border border-slate-200 dark:border-navy-800 text-xs space-y-1.5"
                  >
                    <div className="flex items-center justify-between text-[11px]">
                      <div className="flex items-center gap-1.5 font-medium text-slate-800 dark:text-slate-200 truncate">
                        <FileText className="h-3.5 w-3.5 shrink-0 text-brand-500" />
                        <span className="truncate font-semibold">{docName}</span>
                      </div>
                      {citation.page_number && (
                        <span className="text-slate-500 font-mono text-[10px] bg-white dark:bg-navy-900 px-1.5 py-0.5 rounded border border-slate-200 dark:border-navy-700">
                          Page {citation.page_number}
                        </span>
                      )}
                    </div>
                    <blockquote className="italic text-slate-700 dark:text-slate-300 pl-2.5 border-l-2 border-brand-500/50 text-xs leading-relaxed">
                      "{citation.quoted_statement}"
                    </blockquote>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Recommended Action */}
      {discrepancy.recommended_action && (
        <div className="p-3 rounded-lg bg-emerald-500/5 dark:bg-emerald-500/10 border border-emerald-500/20 text-xs space-y-1">
          <div className="flex items-center gap-1.5 font-bold text-emerald-800 dark:text-emerald-400">
            <Lightbulb className="h-3.5 w-3.5" />
            Recommended Investigator Next Step
          </div>
          <p className="text-slate-700 dark:text-slate-300 leading-relaxed pl-5">
            {discrepancy.recommended_action}
          </p>
        </div>
      )}
    </div>
  );
};
