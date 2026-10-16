import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  ShieldCheck,
  Search,
  RotateCw,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  Code,
  Copy,
  Check,
  Globe,
  Clock,
  X,
} from 'lucide-react';
import { auditService } from '../services/audit-service';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { Button } from '../components/ui/Button';
import type { AuditEventItem } from '../types';

export const AuditActivityPage: React.FC = () => {
  const [page, setPage] = useState<number>(0);
  const [pageSize, setPageSize] = useState<number>(25);
  const [actionCategory, setActionCategory] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedEvent, setSelectedEvent] = useState<AuditEventItem | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  // Fetch Audit Trail
  const {
    data: auditData,
    isLoading,
    error,
    refetch,
    isRefetching,
  } = useQuery({
    queryKey: ['user-audit', page * pageSize, pageSize],
    queryFn: () => auditService.getUserAudit(page * pageSize, pageSize),
  });

  const total = auditData?.total || 0;
  const items = auditData?.items || [];
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  // Copy helper
  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  // Filter items locally based on search and action category
  const filteredItems = useMemo(() => {
    return items.filter((event) => {
      // Category filter
      let matchCategory = true;
      if (actionCategory !== 'all') {
        matchCategory = event.action.toLowerCase().includes(actionCategory.toLowerCase());
      }

      // Search term filter
      const q = searchTerm.toLowerCase().trim();
      const matchSearch =
        !q ||
        event.action.toLowerCase().includes(q) ||
        event.resource_type.toLowerCase().includes(q) ||
        event.resource_id.toLowerCase().includes(q) ||
        (event.request_id && event.request_id.toLowerCase().includes(q)) ||
        (event.ip && event.ip.toLowerCase().includes(q));

      return matchCategory && matchSearch;
    });
  }, [items, actionCategory, searchTerm]);

  // Action badge color mapping
  const getActionStyle = (action: string) => {
    const act = action.toUpperCase();
    if (act.includes('LOGIN') || act.includes('AUTH') || act.includes('REGISTER')) {
      return 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20';
    }
    if (act.includes('ANALYSIS') || act.includes('EXTRACT')) {
      return 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20';
    }
    if (act.includes('DOSSIER') || act.includes('EXPORT')) {
      return 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20';
    }
    if (act.includes('CREATE') || act.includes('UPLOAD')) {
      return 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20';
    }
    return 'bg-slate-100 dark:bg-navy-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-navy-700';
  };

  const formatTimestamp = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2.5">
            <ShieldCheck className="h-6 w-6 text-brand-500" />
            Security & Audit Activity Trail
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            Tamper-proof, immutable ledger of investigative access, claims modifications, and dossier exports
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isLoading || isRefetching}
            isLoading={isRefetching}
            leftIcon={<RotateCw className={`h-4 w-4 ${isRefetching ? 'animate-spin' : ''}`} />}
          >
            {isRefetching ? 'Refreshing...' : 'Refresh Log'}
          </Button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700/80 rounded-xl p-4 shadow-sm flex flex-col lg:flex-row lg:items-center justify-between gap-3">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search by action, resource ID, IP, or request trace ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-950 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
        </div>

        {/* Facet Selectors */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Action Category Filter */}
          <select
            value={actionCategory}
            onChange={(e) => setActionCategory(e.target.value)}
            className="px-2.5 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-950 text-slate-800 dark:text-slate-200 font-semibold focus:outline-none focus:ring-1 focus:ring-brand-500"
          >
            <option value="all">All Action Categories</option>
            <option value="claim">Claims Operations</option>
            <option value="document">Document Ingestion</option>
            <option value="analysis">Intelligence Analysis</option>
            <option value="dossier">Dossier Exports</option>
            <option value="auth">Authentication & Sessions</option>
          </select>

          {/* Page Size Selector */}
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setPage(0);
            }}
            className="px-2.5 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-950 text-slate-800 dark:text-slate-200 font-semibold focus:outline-none focus:ring-1 focus:ring-brand-500"
          >
            <option value={25}>25 / page</option>
            <option value={50}>50 / page</option>
            <option value={100}>100 / page</option>
          </select>
        </div>
      </div>

      {/* Main Table Card */}
      <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700/80 rounded-xl shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="py-20 flex flex-col items-center justify-center space-y-3">
            <LoadingSpinner size="lg" label="Loading cryptographic audit trail..." />
          </div>
        ) : error ? (
          <div className="p-8 text-center text-xs text-rose-500">
            Failed to retrieve audit trail. Please check your network connection and session status.
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="py-12 text-center text-xs text-slate-500">
            No audit events found matching your query.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-navy-950/70 border-b border-slate-200 dark:border-navy-800 text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-3.5">Timestamp</th>
                  <th className="py-3 px-3">Action Event</th>
                  <th className="py-3 px-3">Outcome</th>
                  <th className="py-3 px-3">Resource Target</th>
                  <th className="py-3 px-3">Trace (IP / Request ID)</th>
                  <th className="py-3 px-3.5 text-right">Event Metadata</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-navy-800">
                {filteredItems.map((event) => {
                  const actionStyle = getActionStyle(event.action);
                  const isSuccess = event.outcome.toUpperCase() === 'SUCCESS';
                  const isClaimTarget = event.resource_type === 'claim';

                  return (
                    <tr
                      key={event.id}
                      className="hover:bg-slate-50/60 dark:hover:bg-navy-950/40 transition-colors"
                    >
                      {/* Timestamp */}
                      <td className="py-3 px-3.5 font-mono text-[11px] text-slate-500 dark:text-slate-400 whitespace-nowrap">
                        <div className="flex items-center gap-1.5">
                          <Clock className="h-3 w-3 text-slate-400 shrink-0" />
                          <span>{formatTimestamp(event.timestamp)}</span>
                        </div>
                      </td>

                      {/* Action Event */}
                      <td className="py-3 px-3">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wider border ${actionStyle}`}
                        >
                          {event.action}
                        </span>
                      </td>

                      {/* Outcome */}
                      <td className="py-3 px-3">
                        <span
                          className={`inline-flex items-center px-2 py-0.2 rounded-full text-[10px] font-bold uppercase ${
                            isSuccess
                              ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                              : 'bg-rose-500/10 text-rose-600 dark:text-rose-400'
                          }`}
                        >
                          {event.outcome}
                        </span>
                      </td>

                      {/* Resource Target */}
                      <td className="py-3 px-3">
                        <div className="flex items-center gap-1.5 font-medium text-slate-700 dark:text-slate-300">
                          <span className="text-[10px] uppercase font-bold text-slate-400">
                            {event.resource_type}:
                          </span>
                          {isClaimTarget && event.resource_id !== 'all' ? (
                            <Link
                              to={`/claims/${event.resource_id}`}
                              className="font-mono text-brand-600 dark:text-brand-400 hover:underline flex items-center gap-0.5"
                            >
                              <span>{event.resource_id.slice(0, 8)}...</span>
                              <ExternalLink className="h-3 w-3" />
                            </Link>
                          ) : (
                            <span className="font-mono text-[11px] text-slate-600 dark:text-slate-400 truncate max-w-[120px]" title={event.resource_id}>
                              {event.resource_id}
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Trace (IP / Request ID) */}
                      <td className="py-3 px-3 font-mono text-[11px] text-slate-500 dark:text-slate-400">
                        <div className="space-y-0.5">
                          {event.ip && (
                            <div className="flex items-center gap-1">
                              <Globe className="h-2.5 w-2.5 text-slate-400" />
                              <span>{event.ip}</span>
                            </div>
                          )}
                          {event.request_id && (
                            <div className="flex items-center gap-1 text-[10px] text-slate-400 truncate max-w-[140px]" title={event.request_id}>
                              <span>Req: {event.request_id.slice(0, 8)}</span>
                              <button
                                onClick={() => handleCopy(event.request_id!, `req-${event.id}`)}
                                className="hover:text-brand-500"
                                title="Copy full request ID"
                              >
                                {copiedKey === `req-${event.id}` ? (
                                  <Check className="h-2.5 w-2.5 text-emerald-500" />
                                ) : (
                                  <Copy className="h-2.5 w-2.5 opacity-60" />
                                )}
                              </button>
                            </div>
                          )}
                        </div>
                      </td>

                      {/* Metadata Action */}
                      <td className="py-3 px-3.5 text-right">
                        <button
                          onClick={() => setSelectedEvent(event)}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-semibold text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-navy-800 hover:bg-slate-200 dark:hover:bg-navy-700 transition-colors"
                        >
                          <Code className="h-3 w-3 text-brand-500" />
                          <span>View JSON</span>
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Server Pagination Bar */}
        <div className="p-4 border-t border-slate-100 dark:border-navy-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-slate-500 dark:text-slate-400">
          <div>
            Showing <strong className="text-slate-800 dark:text-slate-200">{filteredItems.length}</strong> of{' '}
            <strong className="text-slate-800 dark:text-slate-200">{total}</strong> total audit records
          </div>

          <div className="flex items-center gap-2 self-end sm:self-center">
            <span className="font-medium mr-1">
              Page {page + 1} of {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="p-1.5 rounded-lg border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-950 text-slate-700 dark:text-slate-300 disabled:opacity-40 hover:bg-slate-100 dark:hover:bg-navy-800 transition-colors"
              title="Previous Page"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              className="p-1.5 rounded-lg border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-950 text-slate-700 dark:text-slate-300 disabled:opacity-40 hover:bg-slate-100 dark:hover:bg-navy-800 transition-colors"
              title="Next Page"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Event Metadata JSON Modal */}
      {selectedEvent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
          <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-navy-800">
              <div className="space-y-0.5">
                <span className="text-[10px] font-mono font-bold uppercase text-brand-500">
                  {selectedEvent.action}
                </span>
                <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                  Audit Event Details & Metadata
                </h3>
              </div>
              <button
                onClick={() => setSelectedEvent(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-2 text-[11px]">
                <div className="p-2 rounded bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-navy-800">
                  <span className="text-slate-400 uppercase font-bold text-[9px]">Resource</span>
                  <div className="font-semibold text-slate-800 dark:text-slate-200 truncate">
                    {selectedEvent.resource_type}: {selectedEvent.resource_id}
                  </div>
                </div>
                <div className="p-2 rounded bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-navy-800">
                  <span className="text-slate-400 uppercase font-bold text-[9px]">User ID</span>
                  <div className="font-mono text-slate-800 dark:text-slate-200 truncate">
                    {selectedEvent.user_id}
                  </div>
                </div>
              </div>

              <div>
                <span className="text-[10px] font-bold uppercase text-slate-400 mb-1 block">
                  Event Metadata JSON
                </span>
                <pre className="p-3 rounded-xl bg-slate-950 text-slate-200 font-mono text-[11px] overflow-x-auto max-h-60 border border-navy-800 leading-relaxed">
                  {JSON.stringify(selectedEvent.event_metadata, null, 2)}
                </pre>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <Button variant="outline" size="sm" onClick={() => setSelectedEvent(null)}>
                Close Viewer
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
