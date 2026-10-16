import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Network,
  AlertTriangle,
  Users,
  CheckCircle2,
  Search,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  RotateCw,
  ShieldCheck,
} from 'lucide-react';
import { fraudRingService } from '../services/fraud-ring-service';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { Button } from '../components/ui/Button';

export const GlobalFraudRingsPage: React.FC = () => {
  const [minShared, setMinShared] = useState<number>(2);
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [patternFilter, setPatternFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [expandedRings, setExpandedRings] = useState<Set<string>>(new Set());

  // Fetch Fraud Rings
  const {
    data: ringData,
    isLoading,
    error,
    refetch,
    isRefetching,
  } = useQuery({
    queryKey: ['fraud-rings', minShared],
    queryFn: () => fraudRingService.listFraudRings(minShared),
  });

  const toggleExpand = (ringId: string) => {
    setExpandedRings((prev) => {
      const next = new Set(prev);
      if (next.has(ringId)) {
        next.delete(ringId);
      } else {
        next.add(ringId);
      }
      return next;
    });
  };

  const rings = useMemo(() => ringData?.rings || [], [ringData]);

  // Filtered rings
  const filteredRings = useMemo(() => {
    return rings.filter((ring) => {
      const matchSeverity =
        severityFilter === 'all' || ring.severity.toLowerCase() === severityFilter.toLowerCase();
      const matchPattern =
        patternFilter === 'all' || ring.pattern.toLowerCase() === patternFilter.toLowerCase();
      const q = searchTerm.toLowerCase().trim();
      const matchSearch =
        !q ||
        ring.title.toLowerCase().includes(q) ||
        ring.summary.toLowerCase().includes(q) ||
        ring.shared_entities.some((e) => e.name.toLowerCase().includes(q)) ||
        ring.claim_ids.some((c) => c.toLowerCase().includes(q));

      return matchSeverity && matchPattern && matchSearch;
    });
  }, [rings, severityFilter, patternFilter, searchTerm]);

  // Aggregate stats
  const totalRings = rings.length;
  const criticalRings = rings.filter((r) => r.severity.toLowerCase() === 'critical').length;
  const totalSharedEntities = rings.reduce((sum, r) => sum + (r.shared_entities?.length || 0), 0);
  const avgRiskScore =
    totalRings > 0
      ? Math.round((rings.reduce((sum, r) => sum + (r.risk_score || 0), 0) / totalRings) * 100)
      : 0;

  const formatPattern = (pattern: string) => {
    return pattern
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (char) => char.toUpperCase());
  };

  const getSeverityStyle = (sev: string) => {
    switch (sev.toLowerCase()) {
      case 'critical':
        return 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/30';
      case 'high':
        return 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30';
      case 'medium':
        return 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 border-yellow-500/30';
      case 'low':
      default:
        return 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/30';
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Title & Refresh */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2.5">
            <Network className="h-6 w-6 text-brand-500" />
            Global Fraud Rings & Collusion Radar
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            Tenant-wide graph analytics identifying staged collisions, role reversals, and repeat claimant syndicates
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
            {isRefetching ? 'Scanning Graph...' : 'Re-scan Radar'}
          </Button>
        </div>
      </div>

      {/* KPI Stats Strip */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700/80 shadow-sm space-y-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
            Detected Syndicates
          </span>
          <div className="text-2xl font-extrabold text-slate-900 dark:text-slate-100">
            {totalRings}
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400">Multi-claim clusters</p>
        </div>

        <div className="p-4 rounded-xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700/80 shadow-sm space-y-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
            Critical Severity Rings
          </span>
          <div className="text-2xl font-extrabold text-rose-600 dark:text-rose-400">
            {criticalRings}
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400">Immediate SIU escalation</p>
        </div>

        <div className="p-4 rounded-xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700/80 shadow-sm space-y-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
            Shared Collusion Entities
          </span>
          <div className="text-2xl font-extrabold text-purple-600 dark:text-purple-400">
            {totalSharedEntities}
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400">Linked across multiple claims</p>
        </div>

        <div className="p-4 rounded-xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700/80 shadow-sm space-y-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
            Average Syndicate Risk
          </span>
          <div className="text-2xl font-extrabold text-amber-600 dark:text-amber-400">
            {avgRiskScore}%
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400">Composite collusion rating</p>
        </div>
      </div>

      {/* Filter and Control Toolbar */}
      <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700/80 rounded-xl p-4 shadow-sm flex flex-col lg:flex-row lg:items-center justify-between gap-3">
        {/* Left: Search input */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search rings by title, entity name, or claim ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-950 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
        </div>

        {/* Right: Threshold & Facet Selectors */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Min Shared Entities */}
          <div className="flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-300">
            <span className="font-semibold text-slate-500">Min Shared:</span>
            <select
              value={minShared}
              onChange={(e) => setMinShared(Number(e.target.value))}
              className="px-2 py-1 text-xs rounded-lg border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-950 font-bold focus:outline-none focus:ring-1 focus:ring-brand-500"
            >
              <option value={2}>2+ Entities (Standard)</option>
              <option value={3}>3+ Entities (High Confidence)</option>
              <option value={4}>4+ Entities (Dense Syndicates)</option>
            </select>
          </div>

          {/* Pattern Filter */}
          <select
            value={patternFilter}
            onChange={(e) => setPatternFilter(e.target.value)}
            className="px-2 py-1 text-xs rounded-lg border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-950 font-semibold focus:outline-none focus:ring-1 focus:ring-brand-500 text-slate-800 dark:text-slate-200"
          >
            <option value="all">All Topologies</option>
            <option value="staged_collision_ring">Staged Collisions</option>
            <option value="provider_fraud_collusion">Provider Fraud</option>
            <option value="repeat_claimant_syndicate">Repeat Claimants</option>
            <option value="role_reversal_network">Role Reversals</option>
            <option value="identity_sharing_cluster">Identity Sharing</option>
          </select>

          {/* Severity Filter */}
          <div className="flex items-center bg-slate-100 dark:bg-navy-950 p-1 rounded-lg border border-slate-200 dark:border-navy-800 text-xs">
            {(['all', 'critical', 'high', 'medium'] as const).map((s) => (
              <button
                key={s}
                onClick={() => setSeverityFilter(s)}
                className={`px-2 py-0.5 rounded capitalize font-medium transition-all ${
                  severityFilter === s
                    ? 'bg-white dark:bg-navy-800 text-slate-900 dark:text-slate-100 shadow-xs font-bold'
                    : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      {isLoading ? (
        <div className="py-20 flex flex-col items-center justify-center space-y-3">
          <LoadingSpinner size="lg" label="Scanning FalkorDB knowledge graph for collusion clusters..." />
        </div>
      ) : error ? (
        <div className="p-8 text-center bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700/80 rounded-xl space-y-3">
          <AlertTriangle className="h-8 w-8 text-rose-500 mx-auto" />
          <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
            Failed to Load Fraud Rings
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto">
            Unable to connect to the graph repository. Verify that FalkorDB is running and accessible.
          </p>
        </div>
      ) : filteredRings.length === 0 ? (
        <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700/80 rounded-2xl p-12 text-center max-w-xl mx-auto shadow-sm space-y-4">
          <div className="p-4 rounded-2xl bg-emerald-500/10 text-emerald-500 inline-flex">
            <ShieldCheck className="h-10 w-10" />
          </div>
          <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
            No Collusion Rings Detected
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
            {rings.length === 0
              ? `The FalkorDB graph engine traversed the current claim caseload with a threshold of ${minShared} shared entities and detected no multi-claim collusion syndicates. As more claim documents are ingested and entities extracted, new connections will register automatically.`
              : 'No fraud rings match your active search and severity filters.'}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredRings.map((ring) => {
            const isExpanded = expandedRings.has(ring.ring_id);
            const severityClass = getSeverityStyle(ring.severity);
            const riskPercentage = Math.round((ring.risk_score || 0.8) * 100);

            return (
              <div
                key={ring.ring_id}
                className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700/80 rounded-xl p-5 shadow-sm space-y-4 transition-all hover:shadow-md"
              >
                {/* Ring Header */}
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                  <div className="space-y-1.5 flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span
                        className={`text-[10px] font-extrabold uppercase px-2.5 py-0.5 rounded-full border ${severityClass}`}
                      >
                        {ring.severity} Severity
                      </span>

                      <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-slate-100 dark:bg-navy-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-navy-700">
                        {formatPattern(ring.pattern)}
                      </span>

                      <div className="text-xs font-bold font-mono px-2 py-0.5 rounded bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20">
                        Risk: {riskPercentage}%
                      </div>
                    </div>

                    <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 leading-snug">
                      {ring.title}
                    </h3>

                    <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed max-w-4xl">
                      {ring.summary}
                    </p>
                  </div>

                  {/* Expand Toggle */}
                  <button
                    onClick={() => toggleExpand(ring.ring_id)}
                    className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-50 dark:bg-navy-950 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-navy-800 hover:bg-slate-100 dark:hover:bg-navy-800 transition-colors shrink-0"
                  >
                    <span>{isExpanded ? 'Collapse' : 'Explore Forensics'}</span>
                    {isExpanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                  </button>
                </div>

                {/* Key Summary Strip */}
                <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500 dark:text-slate-400 pt-1 border-t border-slate-100 dark:border-navy-800">
                  <div className="flex items-center gap-1.5">
                    <Users className="h-3.5 w-3.5 text-brand-500" />
                    <span>
                      Shared Entities:{' '}
                      <strong className="text-slate-800 dark:text-slate-200">
                        {ring.shared_entities.length}
                      </strong>
                    </span>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <Network className="h-3.5 w-3.5 text-purple-500" />
                    <span>
                      Involved Claims:{' '}
                      <strong className="text-slate-800 dark:text-slate-200">
                        {ring.claim_ids.length}
                      </strong>
                    </span>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
                    <span>
                      Indicators Flagged:{' '}
                      <strong className="text-slate-800 dark:text-slate-200">
                        {ring.suspicious_indicators.length}
                      </strong>
                    </span>
                  </div>
                </div>

                {/* Expanded Forensics Details */}
                {isExpanded && (
                  <div className="mt-4 pt-4 border-t border-slate-100 dark:border-navy-800 grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                    {/* Col 1: Shared Entities Table */}
                    <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-950/70 border border-slate-200 dark:border-navy-800 space-y-2">
                      <div className="font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                        <Users className="h-4 w-4 text-brand-500" />
                        Collusion Participants ({ring.shared_entities.length})
                      </div>

                      <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                        {ring.shared_entities.map((entity, idx) => (
                          <div
                            key={idx}
                            className="p-2 rounded bg-white dark:bg-navy-900 border border-slate-200/70 dark:border-navy-800 flex items-center justify-between"
                          >
                            <div>
                              <div className="font-bold text-slate-900 dark:text-slate-100">
                                {entity.name}
                              </div>
                              <div className="text-[10px] text-slate-400 capitalize">
                                {entity.entity_type} {entity.roles?.length ? `• ${entity.roles.join(', ')}` : ''}
                              </div>
                            </div>
                            <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-brand-500/10 text-brand-500">
                              {entity.claim_count} claims
                            </span>
                          </div>
                        ))}
                      </div>

                      {/* Involved Claims Links */}
                      <div className="pt-2 border-t border-slate-200/60 dark:border-navy-800 space-y-1">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                          Connected Caseload Claims:
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {ring.claim_ids.map((cid) => (
                            <Link
                              key={cid}
                              to={`/claims/${cid}`}
                              className="inline-flex items-center gap-1 text-[11px] font-mono font-semibold px-2 py-0.5 rounded bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-800 text-brand-600 dark:text-brand-400 hover:border-brand-500 transition-colors"
                            >
                              <span>Claim #{cid.slice(0, 8)}</span>
                              <ExternalLink className="h-3 w-3" />
                            </Link>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Col 2: Suspicious Indicators */}
                    <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-950/70 border border-slate-200 dark:border-navy-800 space-y-2">
                      <div className="font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                        <AlertTriangle className="h-4 w-4 text-amber-500" />
                        Collusion Topologies ({ring.suspicious_indicators.length})
                      </div>
                      <ul className="space-y-1.5 leading-relaxed max-h-56 overflow-y-auto pr-1">
                        {ring.suspicious_indicators.map((indicator, idx) => (
                          <li
                            key={idx}
                            className="flex items-start gap-1.5 text-slate-700 dark:text-slate-300 text-[11px]"
                          >
                            <span className="text-amber-500 font-bold shrink-0 mt-0.5">•</span>
                            <span>{indicator}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Col 3: Recommended SIU Protocols */}
                    <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-950/70 border border-slate-200 dark:border-navy-800 space-y-2">
                      <div className="font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                        <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                        Recommended SIU Protocols
                      </div>
                      <ul className="space-y-1.5 leading-relaxed max-h-56 overflow-y-auto pr-1">
                        {ring.recommended_siu_actions.map((action, idx) => (
                          <li
                            key={idx}
                            className="flex items-start gap-1.5 text-slate-700 dark:text-slate-300 text-[11px]"
                          >
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
          })}
        </div>
      )}
    </div>
  );
};
