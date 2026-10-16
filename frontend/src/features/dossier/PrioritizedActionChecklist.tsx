import React, { useState } from 'react';
import {
  CheckSquare,
  Square,
  MessageSquare,
  FileSearch,
  ShieldCheck,
  Scale,
  Sparkles,
  Layers,
} from 'lucide-react';
import type { DossierRecommendationItem } from '../../types';

interface PrioritizedActionChecklistProps {
  recommendations: DossierRecommendationItem[];
}

export const PrioritizedActionChecklist: React.FC<PrioritizedActionChecklistProps> = ({
  recommendations,
}) => {
  const [completedIndices, setCompletedIndices] = useState<Set<number>>(new Set());
  const [filterPriority, setFilterPriority] = useState<string>('all');

  const toggleComplete = (idx: number) => {
    setCompletedIndices((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) {
        next.delete(idx);
      } else {
        next.add(idx);
      }
      return next;
    });
  };

  const getCategoryMeta = (cat: string) => {
    switch (cat.toUpperCase()) {
      case 'INTERVIEW':
        return { label: 'Examination / Deposition', icon: MessageSquare, color: 'text-brand-500' };
      case 'EVIDENCE_COLLECTION':
        return { label: 'Evidence Collection', icon: FileSearch, color: 'text-amber-500' };
      case 'FORENSIC_AUDIT':
        return { label: 'Forensic Financial Audit', icon: ShieldCheck, color: 'text-purple-500' };
      case 'LEGAL':
        return { label: 'Legal / Subrogation Counsel', icon: Scale, color: 'text-emerald-500' };
      default:
        return { label: cat.replace(/_/g, ' '), icon: Layers, color: 'text-slate-400' };
    }
  };

  const getPriorityStyle = (priority: string) => {
    switch (priority.toUpperCase()) {
      case 'HIGH':
        return 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/30';
      case 'MEDIUM':
        return 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30';
      case 'LOW':
      default:
        return 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/30';
    }
  };

  const filteredRecommendations = recommendations.filter((rec, idx) => {
    if (filterPriority === 'completed') return completedIndices.has(idx);
    if (filterPriority === 'pending') return !completedIndices.has(idx);
    if (filterPriority === 'HIGH') return rec.priority.toUpperCase() === 'HIGH';
    return true;
  });

  const completedCount = completedIndices.size;
  const totalCount = recommendations.length;
  const progressPct = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700/80 rounded-xl p-5 shadow-sm text-center py-8">
        <Sparkles className="h-6 w-6 text-emerald-500 mx-auto mb-2" />
        <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider">
          No Pending SIU Action Items
        </h4>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-sm mx-auto">
          No prioritized investigative tasks generated. Submitted claim facts meet baseline underwriting compliance.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700/80 rounded-xl p-5 shadow-sm space-y-4">
      {/* Header and Progress */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100 dark:border-navy-800">
        <div>
          <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider flex items-center gap-2">
            <CheckSquare className="h-4 w-4 text-brand-500" />
            Prioritized SIU Action Checklist ({totalCount})
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Targeted field tasks, examination directives, and evidence acquisition steps
          </p>
        </div>

        {/* Progress Metric */}
        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="text-xs font-bold text-slate-800 dark:text-slate-200">
              {completedCount} of {totalCount} completed
            </div>
            <div className="text-[10px] text-slate-400">{progressPct}% checklist progress</div>
          </div>
          <div className="w-16 h-2 rounded-full bg-slate-100 dark:bg-navy-800 overflow-hidden border border-slate-200 dark:border-navy-700">
            <div
              className="h-full bg-emerald-500 transition-all duration-300"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>
      </div>

      {/* Filter Chips */}
      <div className="flex flex-wrap items-center gap-1.5 text-xs">
        <button
          onClick={() => setFilterPriority('all')}
          className={`px-2.5 py-1 rounded-lg font-medium transition-all ${
            filterPriority === 'all'
              ? 'bg-brand-500 text-white shadow-xs'
              : 'bg-slate-100 dark:bg-navy-950 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-navy-800'
          }`}
        >
          All Actions ({totalCount})
        </button>

        <button
          onClick={() => setFilterPriority('HIGH')}
          className={`px-2.5 py-1 rounded-lg font-medium transition-all ${
            filterPriority === 'HIGH'
              ? 'bg-rose-500 text-white shadow-xs'
              : 'bg-slate-100 dark:bg-navy-950 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-navy-800'
          }`}
        >
          High Priority ({recommendations.filter((r) => r.priority.toUpperCase() === 'HIGH').length})
        </button>

        <button
          onClick={() => setFilterPriority('pending')}
          className={`px-2.5 py-1 rounded-lg font-medium transition-all ${
            filterPriority === 'pending'
              ? 'bg-brand-500 text-white shadow-xs'
              : 'bg-slate-100 dark:bg-navy-950 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-navy-800'
          }`}
        >
          Pending ({totalCount - completedCount})
        </button>

        <button
          onClick={() => setFilterPriority('completed')}
          className={`px-2.5 py-1 rounded-lg font-medium transition-all ${
            filterPriority === 'completed'
              ? 'bg-emerald-600 text-white shadow-xs'
              : 'bg-slate-100 dark:bg-navy-950 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-navy-800'
          }`}
        >
          Completed ({completedCount})
        </button>
      </div>

      {/* Action Items List */}
      <div className="space-y-2.5">
        {filteredRecommendations.map((rec, originalIndex) => {
          const isDone = completedIndices.has(originalIndex);
          const catMeta = getCategoryMeta(rec.category);
          const CatIcon = catMeta.icon;
          const priorityBadge = getPriorityStyle(rec.priority);

          return (
            <div
              key={originalIndex}
              onClick={() => toggleComplete(originalIndex)}
              className={`flex items-start gap-3 p-3.5 rounded-xl border transition-all cursor-pointer select-none group ${
                isDone
                  ? 'bg-emerald-500/5 dark:bg-emerald-500/10 border-emerald-500/20 opacity-75'
                  : 'bg-slate-50/70 dark:bg-navy-950/60 hover:bg-slate-50 dark:hover:bg-navy-950 border-slate-200/80 dark:border-navy-800'
              }`}
            >
              {/* Checkbox Icon */}
              <div className="mt-0.5 shrink-0">
                {isDone ? (
                  <CheckSquare className="h-4 w-4 text-emerald-500" />
                ) : (
                  <Square className="h-4 w-4 text-slate-400 group-hover:text-brand-500 transition-colors" />
                )}
              </div>

              {/* Action Content */}
              <div className="flex-1 min-w-0 space-y-1">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span
                      className={`text-[10px] font-extrabold uppercase px-2 py-0.2 rounded-full border ${priorityBadge}`}
                    >
                      {rec.priority} Priority
                    </span>

                    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-500 dark:text-slate-400 bg-white dark:bg-navy-900 px-2 py-0.2 rounded border border-slate-200/80 dark:border-navy-800">
                      <CatIcon className={`h-3 w-3 ${catMeta.color}`} />
                      {catMeta.label}
                    </span>
                  </div>

                  {isDone && (
                    <span className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400">
                      Action Completed
                    </span>
                  )}
                </div>

                <div
                  className={`text-xs font-bold leading-snug transition-all ${
                    isDone
                      ? 'line-through text-slate-400 dark:text-slate-500'
                      : 'text-slate-900 dark:text-slate-100'
                  }`}
                >
                  {rec.action}
                </div>

                <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                  <strong className="font-semibold text-slate-700 dark:text-slate-300">Rationale: </strong>
                  {rec.rationale}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
