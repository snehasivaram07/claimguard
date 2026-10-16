import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Sparkles,
  AlertTriangle,
  Clock,
  HelpCircle,
  FileText,
  RotateCw,
  Layers,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import { intelligenceService } from '../../services/intelligence-service';
import { documentService } from '../../services/document-service';
import { RiskScoreMeter } from './RiskScoreMeter';
import { DiscrepancyCard } from './DiscrepancyCard';
import { TimelineView } from './TimelineView';
import { InterviewQuestions } from './InterviewQuestions';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { Button } from '../../components/ui/Button';

interface TimelineContradictionsTabProps {
  claimId: string;
}

type SubSectionTab = 'all' | 'discrepancies' | 'timeline' | 'questions';

export const TimelineContradictionsTab: React.FC<TimelineContradictionsTabProps> = ({
  claimId,
}) => {
  const queryClient = useQueryClient();
  const [activeSubTab, setActiveSubTab] = useState<SubSectionTab>('all');
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [actionError, setActionError] = useState<string | null>(null);

  // 1. Fetch Cached Intelligence Analysis
  const {
    data: analysis,
    isLoading: isAnalysisLoading,
  } = useQuery({
    queryKey: ['claim-intelligence', claimId],
    queryFn: () => intelligenceService.getIntelligence(claimId),
    retry: false,
  });

  // 2. Fetch Attached Documents (for friendly name lookup & count)
  const { data: docData, isLoading: isDocsLoading } = useQuery({
    queryKey: ['claim-documents', claimId],
    queryFn: () => documentService.listDocuments(claimId),
  });

  // Build documentId -> filename lookup dictionary
  const documentNameMap = useMemo(() => {
    const map: Record<string, string> = {};
    if (docData?.items) {
      docData.items.forEach((doc) => {
        map[doc.id] = doc.original_filename;
      });
    }
    return map;
  }, [docData]);

  // 3. Trigger Cross-Document Analysis Mutation
  const analyzeMutation = useMutation({
    mutationFn: () => intelligenceService.analyzeClaim(claimId),
    onSuccess: (newAnalysis) => {
      setActionError(null);
      // Invalidate relevant queries
      queryClient.setQueryData(['claim-intelligence', claimId], newAnalysis);
      queryClient.invalidateQueries({ queryKey: ['claim-details', claimId] });
      queryClient.invalidateQueries({ queryKey: ['claim-audit', claimId] });
      queryClient.invalidateQueries({ queryKey: ['claim-documents', claimId] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-metrics'] });
    },
    onError: (err: unknown) => {
      const msg =
        err instanceof Error
          ? err.message
          : 'Failed to run cross-document analysis. Ensure the backend AI worker is active.';
      setActionError(msg);
    },
  });

  // Filtered discrepancies
  const filteredDiscrepancies = useMemo(() => {
    if (!analysis?.discrepancies) return [];
    return analysis.discrepancies.filter((d) => {
      const matchSeverity =
        severityFilter === 'all' || d.severity.toLowerCase() === severityFilter.toLowerCase();
      const matchCategory =
        categoryFilter === 'all' || d.category.toLowerCase() === categoryFilter.toLowerCase();
      return matchSeverity && matchCategory;
    });
  }, [analysis, severityFilter, categoryFilter]);

  // Unique categories for the filter dropdown
  const uniqueCategories = useMemo(() => {
    if (!analysis?.discrepancies) return [];
    return Array.from(new Set(analysis.discrepancies.map((d) => d.category)));
  }, [analysis]);

  if (isAnalysisLoading || isDocsLoading) {
    return (
      <div className="py-20 flex flex-col items-center justify-center space-y-3">
        <LoadingSpinner size="lg" label="Retrieving cross-document intelligence..." />
      </div>
    );
  }

  const documentCount = docData?.total || docData?.items?.length || 0;
  const isAnalyzing = analyzeMutation.isPending;

  // Render State 1: No Analysis Yet (Empty State)
  if (!analysis) {
    return (
      <div className="space-y-6">
        {actionError && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs text-rose-600 dark:text-rose-400 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{actionError}</span>
            </div>
            <button
              onClick={() => setActionError(null)}
              className="text-xs font-bold underline ml-3"
            >
              Dismiss
            </button>
          </div>
        )}

        <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700/80 rounded-2xl p-8 sm:p-12 text-center max-w-3xl mx-auto shadow-sm space-y-6">
          <div className="inline-flex p-4 rounded-2xl bg-brand-500/10 text-brand-500 ring-8 ring-brand-500/5">
            <Sparkles className="h-10 w-10 animate-pulse" />
          </div>

          <div className="space-y-2">
            <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100">
              Cross-Document Intelligence Analysis
            </h3>
            <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 max-w-xl mx-auto leading-relaxed">
              No cross-document intelligence report has been generated yet for this claim. Run the AI
              investigative engine to cross-reference evidence, align timelines, and detect contradictions.
            </p>
          </div>

          {/* Key capabilities pills */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-left">
            <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-950/70 border border-slate-200 dark:border-navy-800 space-y-1">
              <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800 dark:text-slate-200">
                <Clock className="h-4 w-4 text-brand-500" />
                Chronological Timeline
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-normal">
                Synthesizes dates from police reports, FNOL notes, and repair invoices into one sequence.
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-950/70 border border-slate-200 dark:border-navy-800 space-y-1">
              <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800 dark:text-slate-200">
                <AlertTriangle className="h-4 w-4 text-amber-500" />
                Factual Contradictions
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-normal">
                Discovers conflicting statements (e.g. damage locations or dates) with verbatim quotes.
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-950/70 border border-slate-200 dark:border-navy-800 space-y-1">
              <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800 dark:text-slate-200">
                <HelpCircle className="h-4 w-4 text-purple-500" />
                Deposition Checklist
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-normal">
                Formulates targeted questions to probe contradictory statements during claimant interviews.
              </p>
            </div>
          </div>

          {/* Document count status notice */}
          <div className="pt-2">
            {documentCount === 0 ? (
              <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-700 dark:text-amber-400 max-w-md mx-auto">
                <span className="font-bold">Notice:</span> 0 documents are currently uploaded to this claim.
                Please upload police reports, loss notices, or repair estimates in the Document Hub before running analysis.
              </div>
            ) : (
              <div className="text-xs text-slate-500 dark:text-slate-400">
                <span className="font-bold text-slate-700 dark:text-slate-200">{documentCount}</span> active
                document{documentCount > 1 ? 's' : ''} ready for cross-referencing.
              </div>
            )}
          </div>

          {/* Trigger Button */}
          <div className="pt-2">
            <Button
              variant="primary"
              size="lg"
              disabled={isAnalyzing || documentCount === 0}
              isLoading={isAnalyzing}
              onClick={() => analyzeMutation.mutate()}
              leftIcon={<Sparkles className="h-5 w-5" />}
            >
              {isAnalyzing ? 'Running Intelligence Forensics...' : 'Run Cross-Document Analysis'}
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // Render State 2: Analysis Report Available
  return (
    <div className="space-y-6">
      {/* Top Banner / Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700/80 shadow-sm">
        <div className="space-y-1">
          <div className="flex items-center gap-2 flex-wrap">
            <h2 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <Clock className="h-5 w-5 text-brand-500" />
              Reconstructed Timeline & Contradiction Board
            </h2>
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
              <CheckCircle2 className="h-3 w-3" />
              Analysis Cached
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            {analysis.analyzed_at
              ? `Last analyzed on ${new Date(analysis.analyzed_at).toLocaleString('en-US', {
                  month: 'short',
                  day: 'numeric',
                  year: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })}`
              : 'Analysis up to date with attached records'}
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <Button
            variant="outline"
            size="sm"
            disabled={isAnalyzing}
            isLoading={isAnalyzing}
            onClick={() => analyzeMutation.mutate()}
            leftIcon={<RotateCw className={`h-4 w-4 ${isAnalyzing ? 'animate-spin' : ''}`} />}
          >
            {isAnalyzing ? 'Re-analyzing...' : 'Re-run Analysis'}
          </Button>
        </div>
      </div>

      {actionError && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs text-rose-600 dark:text-rose-400 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{actionError}</span>
          </div>
          <button
            onClick={() => setActionError(null)}
            className="text-xs font-bold underline ml-3"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Hero Grid: Executive Summary & Risk Score Meter */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left: Forensic Executive Summary */}
        <div className="lg:col-span-7 bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700/80 rounded-xl p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-navy-800">
            <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider flex items-center gap-2">
              <FileText className="h-4 w-4 text-brand-500" />
              Executive Forensic Summary
            </h3>
            <span className="text-[11px] font-mono text-slate-400">
              {documentCount} documents evaluated
            </span>
          </div>

          <p className="text-xs sm:text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-normal">
            {analysis.executive_summary}
          </p>

          <div className="pt-2 flex flex-wrap items-center gap-4 text-xs text-slate-500 dark:text-slate-400 border-t border-slate-100 dark:border-navy-800/80">
            <div>
              <span className="font-semibold text-slate-700 dark:text-slate-300">Timeline Events: </span>
              {analysis.timeline.length}
            </div>
            <div>
              <span className="font-semibold text-slate-700 dark:text-slate-300">Contradictions Flagged: </span>
              {analysis.discrepancies.length}
            </div>
            <div>
              <span className="font-semibold text-slate-700 dark:text-slate-300">Interview Inquiries: </span>
              {analysis.unresolved_questions.length}
            </div>
          </div>
        </div>

        {/* Right: Fraud Risk Score Meter */}
        <div className="lg:col-span-5">
          <RiskScoreMeter
            riskScore={analysis.overall_risk_score}
            confidenceScore={analysis.confidence_score}
            discrepancies={analysis.discrepancies}
          />
        </div>
      </div>

      {/* Sub-Section Navigation Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 dark:border-navy-800 pb-2">
        <button
          onClick={() => setActiveSubTab('all')}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            activeSubTab === 'all'
              ? 'bg-brand-500 text-white shadow-sm shadow-brand-500/20'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-navy-800'
          }`}
        >
          <Layers className="h-3.5 w-3.5" />
          <span>All Findings</span>
        </button>

        <button
          onClick={() => setActiveSubTab('discrepancies')}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            activeSubTab === 'discrepancies'
              ? 'bg-brand-500 text-white shadow-sm shadow-brand-500/20'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-navy-800'
          }`}
        >
          <AlertTriangle className="h-3.5 w-3.5" />
          <span>Contradictions Board</span>
          <span
            className={`px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
              activeSubTab === 'discrepancies'
                ? 'bg-white/20 text-white'
                : 'bg-rose-500/10 text-rose-600 dark:text-rose-400'
            }`}
          >
            {analysis.discrepancies.length}
          </span>
        </button>

        <button
          onClick={() => setActiveSubTab('timeline')}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            activeSubTab === 'timeline'
              ? 'bg-brand-500 text-white shadow-sm shadow-brand-500/20'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-navy-800'
          }`}
        >
          <Clock className="h-3.5 w-3.5" />
          <span>Reconstructed Timeline</span>
          <span
            className={`px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
              activeSubTab === 'timeline'
                ? 'bg-white/20 text-white'
                : 'bg-slate-200 dark:bg-navy-700 text-slate-700 dark:text-slate-300'
            }`}
          >
            {analysis.timeline.length}
          </span>
        </button>

        <button
          onClick={() => setActiveSubTab('questions')}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            activeSubTab === 'questions'
              ? 'bg-brand-500 text-white shadow-sm shadow-brand-500/20'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-navy-800'
          }`}
        >
          <HelpCircle className="h-3.5 w-3.5" />
          <span>Interview Inquiries</span>
          <span
            className={`px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
              activeSubTab === 'questions'
                ? 'bg-white/20 text-white'
                : 'bg-slate-200 dark:bg-navy-700 text-slate-700 dark:text-slate-300'
            }`}
          >
            {analysis.unresolved_questions.length}
          </span>
        </button>
      </div>

      {/* Main Content Layout based on activeSubTab */}
      {activeSubTab === 'all' && (
        <div className="space-y-6">
          {/* Section A: Contradictions Board */}
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-rose-500" />
                  Cross-Document Contradiction Board ({filteredDiscrepancies.length})
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Factual contradictions detected by comparing active records with verbatim citations
                </p>
              </div>

              {/* Filters */}
              <div className="flex items-center gap-2 flex-wrap">
                {/* Severity Filter Buttons */}
                <div className="flex items-center bg-slate-100 dark:bg-navy-950 p-1 rounded-lg border border-slate-200 dark:border-navy-800 text-xs">
                  {(['all', 'critical', 'high', 'medium', 'low'] as const).map((sev) => (
                    <button
                      key={sev}
                      onClick={() => setSeverityFilter(sev)}
                      className={`px-2 py-0.5 rounded capitalize font-medium transition-all ${
                        severityFilter === sev
                          ? 'bg-white dark:bg-navy-800 text-slate-900 dark:text-slate-100 shadow-xs font-bold'
                          : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                      }`}
                    >
                      {sev}
                    </button>
                  ))}
                </div>

                {/* Category Filter */}
                {uniqueCategories.length > 0 && (
                  <select
                    value={categoryFilter}
                    onChange={(e) => setCategoryFilter(e.target.value)}
                    className="text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-navy-700 bg-white dark:bg-navy-950 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  >
                    <option value="all">All Categories</option>
                    {uniqueCategories.map((cat) => (
                      <option key={cat} value={cat}>
                        {cat.replace(/_/g, ' ')}
                      </option>
                    ))}
                  </select>
                )}
              </div>
            </div>

            {/* Discrepancies Grid */}
            {filteredDiscrepancies.length === 0 ? (
              <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700/80 rounded-xl p-8 text-center text-xs text-slate-500">
                {analysis.discrepancies.length === 0 ? (
                  <div className="space-y-1">
                    <CheckCircle2 className="h-6 w-6 text-emerald-500 mx-auto mb-1" />
                    <p className="font-bold text-slate-800 dark:text-slate-200">
                      No Cross-Document Discrepancies Flagged
                    </p>
                    <p className="text-slate-400">
                      All statements and entity records across the evaluated documents appear consistent.
                    </p>
                  </div>
                ) : (
                  'No contradictions match the active severity and category filters.'
                )}
              </div>
            ) : (
              <div className="space-y-4">
                {filteredDiscrepancies.map((discrepancy) => (
                  <DiscrepancyCard
                    key={discrepancy.id}
                    discrepancy={discrepancy}
                    documentNameMap={documentNameMap}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Section B: Reconstructed Incident Timeline */}
          <TimelineView
            timeline={analysis.timeline}
            documentNameMap={documentNameMap}
            discrepancies={analysis.discrepancies}
          />

          {/* Section C: Targeted Interview Questions */}
          <InterviewQuestions questions={analysis.unresolved_questions} />
        </div>
      )}

      {/* SubTab: Discrepancies Only */}
      {activeSubTab === 'discrepancies' && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-rose-500" />
                Cross-Document Contradiction Board ({filteredDiscrepancies.length})
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Factual contradictions detected by comparing active records with verbatim citations
              </p>
            </div>

            {/* Filters */}
            <div className="flex items-center gap-2 flex-wrap">
              <div className="flex items-center bg-slate-100 dark:bg-navy-950 p-1 rounded-lg border border-slate-200 dark:border-navy-800 text-xs">
                {(['all', 'critical', 'high', 'medium', 'low'] as const).map((sev) => (
                  <button
                    key={sev}
                    onClick={() => setSeverityFilter(sev)}
                    className={`px-2 py-0.5 rounded capitalize font-medium transition-all ${
                      severityFilter === sev
                        ? 'bg-white dark:bg-navy-800 text-slate-900 dark:text-slate-100 shadow-xs font-bold'
                        : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                    }`}
                  >
                    {sev}
                  </button>
                ))}
              </div>

              {uniqueCategories.length > 0 && (
                <select
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  className="text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-navy-700 bg-white dark:bg-navy-950 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-brand-500"
                >
                  <option value="all">All Categories</option>
                  {uniqueCategories.map((cat) => (
                    <option key={cat} value={cat}>
                      {cat.replace(/_/g, ' ')}
                    </option>
                  ))}
                </select>
              )}
            </div>
          </div>

          {filteredDiscrepancies.length === 0 ? (
            <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700/80 rounded-xl p-8 text-center text-xs text-slate-500">
              No contradictions match the active filter criteria.
            </div>
          ) : (
            <div className="space-y-4">
              {filteredDiscrepancies.map((discrepancy) => (
                <DiscrepancyCard
                  key={discrepancy.id}
                  discrepancy={discrepancy}
                  documentNameMap={documentNameMap}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* SubTab: Timeline Only */}
      {activeSubTab === 'timeline' && (
        <TimelineView
          timeline={analysis.timeline}
          documentNameMap={documentNameMap}
          discrepancies={analysis.discrepancies}
        />
      )}

      {/* SubTab: Interview Questions Only */}
      {activeSubTab === 'questions' && (
        <InterviewQuestions questions={analysis.unresolved_questions} />
      )}
    </div>
  );
};
