import React, { useState, useMemo } from 'react';
import {
  Calendar,
  Clock,
  ArrowUpDown,
  Search,
  FileText,
  AlertTriangle,
  Info,
} from 'lucide-react';
import type { TimelineEvent, ClaimDiscrepancy } from '../../types';

interface TimelineViewProps {
  timeline: TimelineEvent[];
  documentNameMap?: Record<string, string>;
  discrepancies?: ClaimDiscrepancy[];
}

export const TimelineView: React.FC<TimelineViewProps> = ({
  timeline,
  documentNameMap = {},
  discrepancies = [],
}) => {
  const [sortAsc, setSortAsc] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>('');

  // Extract set of dates mentioned in date discrepancies
  const dateConflictKeywords = useMemo(() => {
    const keywords: string[] = [];
    discrepancies
      .filter((d) => d.category.toLowerCase().includes('date'))
      .forEach((d) => {
        // Collect quotes or description tokens
        d.citations.forEach((c) => keywords.push(c.quoted_statement.toLowerCase()));
      });
    return keywords;
  }, [discrepancies]);

  // Filter & sort events
  const filteredEvents = useMemo(() => {
    let list = [...timeline];

    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase();
      list = list.filter(
        (ev) =>
          ev.date.toLowerCase().includes(q) ||
          ev.event_description.toLowerCase().includes(q) ||
          (ev.source_context && ev.source_context.toLowerCase().includes(q))
      );
    }

    // Sort chronologically
    list.sort((a, b) => {
      const dateA = new Date(a.date).getTime();
      const dateB = new Date(b.date).getTime();

      const validA = !isNaN(dateA);
      const validB = !isNaN(dateB);

      if (validA && validB) {
        return sortAsc ? dateA - dateB : dateB - dateA;
      }
      return sortAsc ? a.date.localeCompare(b.date) : b.date.localeCompare(a.date);
    });

    return list;
  }, [timeline, searchTerm, sortAsc]);

  const getDocName = (docId: string) => {
    if (documentNameMap[docId]) return documentNameMap[docId];
    return `Doc #${docId.slice(0, 8)}`;
  };

  const formatDate = (dateStr: string) => {
    const parsed = new Date(dateStr);
    if (!isNaN(parsed.getTime())) {
      return parsed.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    }
    return dateStr;
  };

  return (
    <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700/80 rounded-xl p-5 shadow-sm space-y-5">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100 dark:border-navy-800">
        <div>
          <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider flex items-center gap-2">
            <Clock className="h-4 w-4 text-brand-500" />
            Reconstructed Incident Timeline ({timeline.length})
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Chronological events extracted from cross-document intelligence
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Search Box */}
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search events..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-950 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-brand-500 w-36 sm:w-48"
            />
          </div>

          {/* Sort Toggle */}
          <button
            onClick={() => setSortAsc(!sortAsc)}
            className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-semibold rounded-lg border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-950 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-navy-800 transition-colors"
            title="Toggle chronological sort order"
          >
            <ArrowUpDown className="h-3.5 w-3.5 text-slate-400" />
            <span>{sortAsc ? 'Oldest First' : 'Newest First'}</span>
          </button>
        </div>
      </div>

      {/* Empty State */}
      {timeline.length === 0 ? (
        <div className="py-12 text-center text-slate-500">
          <Calendar className="h-8 w-8 mx-auto text-slate-400 mb-2" />
          <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">
            No Timeline Events Extracted
          </p>
          <p className="text-xs text-slate-400 mt-1">
            Run cross-document analysis to parse chronological events from uploaded records.
          </p>
        </div>
      ) : filteredEvents.length === 0 ? (
        <div className="py-8 text-center text-slate-500 text-xs">
          No events match the search query "{searchTerm}".
        </div>
      ) : (
        /* Chronological Vertical Timeline */
        <div className="relative pl-6 sm:pl-8 space-y-6 before:absolute before:left-2.5 sm:before:left-3.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200 dark:before:bg-navy-700">
          {filteredEvents.map((event, index) => {
            const docName = getDocName(event.document_id);
            const isConflictSuspect = dateConflictKeywords.some(
              (kw) =>
                event.event_description.toLowerCase().includes(kw) ||
                event.date.toLowerCase().includes(kw)
            );

            return (
              <div key={`${event.document_id}-${index}`} className="relative group">
                {/* Timeline Node Dot */}
                <div
                  className={`absolute -left-6 sm:-left-8 top-1.5 h-5 w-5 rounded-full border-2 flex items-center justify-center transition-all ${
                    isConflictSuspect
                      ? 'bg-rose-500 border-rose-300 text-white shadow-sm shadow-rose-500/50'
                      : 'bg-white dark:bg-navy-900 border-brand-500 text-brand-500 group-hover:scale-110'
                  }`}
                >
                  <div
                    className={`h-2 w-2 rounded-full ${
                      isConflictSuspect ? 'bg-white' : 'bg-brand-500'
                    }`}
                  />
                </div>

                {/* Event Card */}
                <div className="bg-slate-50/80 dark:bg-navy-950/60 hover:bg-slate-50 dark:hover:bg-navy-950 border border-slate-200/80 dark:border-navy-800 rounded-lg p-3.5 space-y-2 transition-all">
                  {/* Top: Date & Badges */}
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="inline-flex items-center gap-1.5 text-xs font-bold font-mono text-slate-800 dark:text-slate-200 bg-white dark:bg-navy-900 px-2 py-0.5 rounded border border-slate-200 dark:border-navy-700">
                        <Calendar className="h-3 w-3 text-brand-500" />
                        {formatDate(event.date)}
                      </span>

                      {isConflictSuspect && (
                        <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-rose-600 dark:text-rose-400 bg-rose-500/10 border border-rose-500/20 px-1.5 py-0.5 rounded">
                          <AlertTriangle className="h-3 w-3" />
                          Contradiction Subject
                        </span>
                      )}
                    </div>

                    {/* Source Document Tag */}
                    <div
                      className="inline-flex items-center gap-1 text-[11px] text-slate-500 dark:text-slate-400 bg-white dark:bg-navy-900 px-2 py-0.5 rounded border border-slate-200/60 dark:border-navy-800 font-medium truncate max-w-[200px]"
                      title={docName}
                    >
                      <FileText className="h-3 w-3 shrink-0 text-slate-400" />
                      <span className="truncate">{docName}</span>
                    </div>
                  </div>

                  {/* Event Description */}
                  <p className="text-xs text-slate-800 dark:text-slate-200 font-medium leading-relaxed">
                    {event.event_description}
                  </p>

                  {/* Context Quote */}
                  {event.source_context && (
                    <div className="text-[11px] text-slate-500 dark:text-slate-400 italic bg-white dark:bg-navy-900 p-2 rounded border border-slate-200/60 dark:border-navy-800 flex items-start gap-1.5">
                      <Info className="h-3 w-3 text-slate-400 shrink-0 mt-0.5" />
                      <span>"{event.source_context}"</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
