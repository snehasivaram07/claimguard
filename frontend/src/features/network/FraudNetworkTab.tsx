import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Network,
  Search,
  AlertCircle,
} from 'lucide-react';
import { fraudRingService } from '../../services/fraud-ring-service';
import { FraudNetworkCanvas } from './FraudNetworkCanvas';
import { NodeInspectorPanel } from './NodeInspectorPanel';
import { FraudRingAlertBanner } from './FraudRingAlertBanner';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import type { FraudRingNode, FraudRingEdge } from '../../types';

interface FraudNetworkTabProps {
  claimId: string;
}

export const FraudNetworkTab: React.FC<FraudNetworkTabProps> = ({ claimId }) => {
  const [maxHops, setMaxHops] = useState<number>(2);
  const [selectedNode, setSelectedNode] = useState<FraudRingNode | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<FraudRingEdge | null>(null);
  const [nodeTypeFilter, setNodeTypeFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');

  // Fetch Fraud Network Subgraph
  const {
    data: networkData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['claim-fraud-network', claimId, maxHops],
    queryFn: () => fraudRingService.getClaimNetwork(claimId, maxHops),
  });

  if (isLoading) {
    return (
      <div className="py-24 flex flex-col items-center justify-center space-y-3">
        <LoadingSpinner size="lg" label="Traversing entity graph and calculating multi-hop network..." />
      </div>
    );
  }

  if (error || !networkData) {
    return (
      <div className="p-8 text-center bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700/80 rounded-xl space-y-3">
        <AlertCircle className="h-8 w-8 text-rose-500 mx-auto" />
        <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
          Failed to Load Network Graph
        </h3>
        <p className="text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto">
          Could not retrieve graph neighborhood from FalkorDB. Ensure the graph repository is connected and healthy.
        </p>
      </div>
    );
  }

  const nodes = networkData.nodes || [];
  const edges = networkData.edges || [];
  const fraudRings = networkData.fraud_rings || [];

  return (
    <div className="space-y-5">
      {/* Top Controls Toolbar */}
      <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700/80 rounded-xl p-4 shadow-sm space-y-3">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
          {/* Title & Hop Depth Selector */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2">
              <Network className="h-5 w-5 text-brand-500" />
              <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider">
                Graph Neighborhood & Fraud Rings
              </h3>
            </div>

            {/* Depth Selector Pills */}
            <div className="flex items-center bg-slate-100 dark:bg-navy-950 p-1 rounded-lg border border-slate-200 dark:border-navy-800 text-xs">
              <button
                onClick={() => setMaxHops(1)}
                className={`px-2.5 py-1 rounded font-semibold transition-all ${
                  maxHops === 1
                    ? 'bg-white dark:bg-navy-800 text-slate-900 dark:text-slate-100 shadow-xs'
                    : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
                }`}
              >
                1-Hop (Direct Relations)
              </button>
              <button
                onClick={() => setMaxHops(2)}
                className={`px-2.5 py-1 rounded font-semibold transition-all ${
                  maxHops === 2
                    ? 'bg-white dark:bg-navy-800 text-slate-900 dark:text-slate-100 shadow-xs'
                    : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
                }`}
              >
                2-Hop (Collusion & Cross-Claim)
              </button>
            </div>
          </div>

          {/* Search & Filter Bar */}
          <div className="flex flex-wrap items-center gap-2.5">
            {/* Search Input */}
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
              <input
                type="text"
                placeholder="Find entity by name..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-950 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-brand-500 w-44 sm:w-52"
              />
            </div>

            {/* Node Type Filter */}
            <div className="flex items-center gap-1 bg-slate-100 dark:bg-navy-950 p-1 rounded-lg border border-slate-200 dark:border-navy-800 text-xs">
              {(['all', 'claim', 'person', 'organization'] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => setNodeTypeFilter(t)}
                  className={`px-2 py-0.5 rounded capitalize font-medium transition-all ${
                    nodeTypeFilter === t
                      ? 'bg-white dark:bg-navy-800 text-slate-900 dark:text-slate-100 shadow-xs font-bold'
                      : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                  }`}
                >
                  {t === 'all' ? 'All' : t === 'claim' ? 'Claims' : t === 'person' ? 'Persons' : 'Orgs'}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Fraud Ring Alert Banner (if syndicates detected) */}
      <FraudRingAlertBanner fraudRings={fraudRings} />

      {/* Main Grid: Cytoscape Canvas (8 cols) + Node Inspector (4 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* Graph Canvas Column */}
        <div className="lg:col-span-8 space-y-3">
          <FraudNetworkCanvas
            nodes={nodes}
            edges={edges}
            onSelectNode={(n) => {
              setSelectedNode(n);
              setSelectedEdge(null);
            }}
            onSelectEdge={(e) => {
              setSelectedEdge(e);
              setSelectedNode(null);
            }}
            selectedNodeId={selectedNode?.id}
            nodeTypeFilter={nodeTypeFilter}
            searchTerm={searchTerm}
          />

          {/* Visual Legend */}
          <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700/80 rounded-xl p-3 shadow-sm flex flex-wrap items-center justify-between gap-3 text-xs text-slate-600 dark:text-slate-400">
            <span className="font-bold uppercase tracking-wider text-[10px] text-slate-400">
              Graph Legend:
            </span>

            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-1.5">
                <div className="w-3.5 h-3.5 rotate-45 bg-brand-500 border-2 border-brand-300 shadow-xs" />
                <span className="text-[11px] font-medium">Focal Target Claim</span>
              </div>

              <div className="flex items-center gap-1.5">
                <div className="w-3.5 h-3.5 rounded bg-slate-800 dark:bg-slate-950 border border-slate-500" />
                <span className="text-[11px] font-medium">Connected Claim</span>
              </div>

              <div className="flex items-center gap-1.5">
                <div className="w-3.5 h-3.5 rounded-full bg-emerald-600 border border-emerald-400" />
                <span className="text-[11px] font-medium">Person / Driver</span>
              </div>

              <div className="flex items-center gap-1.5">
                <div className="w-3.5 h-3.5 bg-purple-600 border border-purple-400" />
                <span className="text-[11px] font-medium">Organization / Facility</span>
              </div>
            </div>
          </div>
        </div>

        {/* Node Inspector Column */}
        <div className="lg:col-span-4 h-[580px]">
          <NodeInspectorPanel
            selectedNode={selectedNode}
            selectedEdge={selectedEdge}
            nodes={nodes}
            edges={edges}
            onClose={() => {
              setSelectedNode(null);
              setSelectedEdge(null);
            }}
          />
        </div>
      </div>
    </div>
  );
};
