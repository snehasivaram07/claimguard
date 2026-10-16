import React from 'react';
import { Link } from 'react-router-dom';
import {
  FileText,
  User,
  Building2,
  Target,
  ArrowRight,
  X,
  ExternalLink,
  Link as LinkIcon,
  Network,
} from 'lucide-react';
import type { FraudRingNode, FraudRingEdge } from '../../types';

interface NodeInspectorPanelProps {
  selectedNode: FraudRingNode | null;
  selectedEdge: FraudRingEdge | null;
  nodes: FraudRingNode[];
  edges: FraudRingEdge[];
  onClose: () => void;
}

export const NodeInspectorPanel: React.FC<NodeInspectorPanelProps> = ({
  selectedNode,
  selectedEdge,
  nodes,
  edges,
  onClose,
}) => {
  // Helper to find node label by ID
  const getNodeLabel = (id: string) => {
    const node = nodes.find((n) => n.id === id);
    return node ? node.label : id;
  };

  // When nothing is selected
  if (!selectedNode && !selectedEdge) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-6 text-center text-slate-500 bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700/80 rounded-xl shadow-sm">
        <Network className="h-10 w-10 text-slate-400 mb-3 stroke-[1.5]" />
        <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200">
          Network Element Inspector
        </h4>
        <p className="text-xs text-slate-400 max-w-xs mt-1 leading-relaxed">
          Select any node or connecting edge in the graph to inspect entity metadata, multi-claim connections, and collusion roles.
        </p>
      </div>
    );
  }

  // --- 1. Selected Edge Inspector ---
  if (selectedEdge) {
    const sourceLabel = getNodeLabel(selectedEdge.source);
    const targetLabel = getNodeLabel(selectedEdge.target);

    return (
      <div className="h-full flex flex-col bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700/80 rounded-xl shadow-sm overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-slate-100 dark:border-navy-800 flex items-center justify-between bg-slate-50/50 dark:bg-navy-950/40">
          <div className="flex items-center gap-2">
            <LinkIcon className="h-4 w-4 text-brand-500" />
            <span className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
              Relationship Edge
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-md text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-navy-800"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4 flex-1 overflow-y-auto text-xs">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Relationship Type
            </span>
            <div className="text-sm font-bold font-mono text-brand-600 dark:text-brand-400 mt-0.5">
              {selectedEdge.type}
            </div>
          </div>

          <div className="p-3 rounded-lg bg-slate-50 dark:bg-navy-950/70 border border-slate-200 dark:border-navy-800 space-y-2">
            <div className="text-[11px] font-medium text-slate-500">Connected Nodes:</div>
            <div className="flex items-center justify-between gap-2 font-semibold text-slate-800 dark:text-slate-200">
              <span className="truncate" title={sourceLabel}>
                {sourceLabel}
              </span>
              <ArrowRight className="h-3.5 w-3.5 shrink-0 text-slate-400" />
              <span className="truncate" title={targetLabel}>
                {targetLabel}
              </span>
            </div>
          </div>

          {/* Properties */}
          {selectedEdge.properties && Object.keys(selectedEdge.properties).length > 0 && (
            <div className="space-y-1.5">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Edge Attributes
              </span>
              <div className="rounded-lg border border-slate-200 dark:border-navy-800 overflow-hidden divide-y divide-slate-100 dark:divide-navy-800">
                {Object.entries(selectedEdge.properties).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between p-2.5 bg-white dark:bg-navy-900">
                    <span className="text-slate-500 capitalize">{key.replace(/_/g, ' ')}</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200">
                      {String(value)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // --- 2. Selected Node Inspector ---
  const node = selectedNode!;
  const isTarget = !!node.is_target;
  const nodeType = node.type || 'claim';

  // Connected edges for this node
  const connectedEdges = edges.filter(
    (e) => e.source === node.id || e.target === node.id
  );

  // Connected other nodes
  const connectedNodeIds = new Set<string>();
  connectedEdges.forEach((e) => {
    if (e.source !== node.id) connectedNodeIds.add(e.source);
    if (e.target !== node.id) connectedNodeIds.add(e.target);
  });
  const connectedNodesList = nodes.filter((n) => connectedNodeIds.has(n.id));

  // Determine Type Icon & Badge
  let TypeIcon = FileText;
  let typeLabel = 'Claim Record';
  let badgeStyle = 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20';

  if (isTarget) {
    TypeIcon = Target;
    typeLabel = 'Focal Investigation Target';
    badgeStyle = 'bg-brand-500 text-white border-transparent shadow-xs';
  } else if (nodeType === 'person') {
    TypeIcon = User;
    typeLabel = 'Person / Individual';
    badgeStyle = 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20';
  } else if (nodeType === 'organization') {
    TypeIcon = Building2;
    typeLabel = 'Organization / Facility';
    badgeStyle = 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20';
  } else {
    TypeIcon = FileText;
    typeLabel = 'Connected Claim';
    badgeStyle = 'bg-slate-100 dark:bg-navy-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-navy-700';
  }

  return (
    <div className="h-full flex flex-col bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700/80 rounded-xl shadow-sm overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-slate-100 dark:border-navy-800 flex items-center justify-between bg-slate-50/50 dark:bg-navy-950/40">
        <div className="flex items-center gap-2">
          <TypeIcon className="h-4 w-4 text-brand-500" />
          <span className={`text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full border ${badgeStyle}`}>
            {typeLabel}
          </span>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-md text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-navy-800"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Body Content */}
      <div className="p-4 space-y-4 flex-1 overflow-y-auto text-xs">
        {/* Node Title & ID */}
        <div className="space-y-1">
          <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 leading-snug">
            {node.label}
          </h3>
          <div className="text-[10px] font-mono text-slate-400 truncate">
            ID: {node.id}
          </div>
        </div>

        {/* Quick Metrics Bar */}
        <div className="grid grid-cols-2 gap-2 text-center">
          <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-navy-950/70 border border-slate-200 dark:border-navy-800">
            <div className="text-[10px] font-bold uppercase text-slate-400">Connections</div>
            <div className="text-sm font-extrabold text-slate-800 dark:text-slate-200 mt-0.5">
              {connectedEdges.length}
            </div>
          </div>
          <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-navy-950/70 border border-slate-200 dark:border-navy-800">
            <div className="text-[10px] font-bold uppercase text-slate-400">Entity Type</div>
            <div className="text-sm font-extrabold capitalize text-slate-800 dark:text-slate-200 mt-0.5">
              {nodeType}
            </div>
          </div>
        </div>

        {/* Properties Table */}
        {node.properties && Object.keys(node.properties).length > 0 && (
          <div className="space-y-1.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Entity Attributes
            </span>
            <div className="rounded-lg border border-slate-200 dark:border-navy-800 overflow-hidden divide-y divide-slate-100 dark:divide-navy-800">
              {Object.entries(node.properties).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between p-2.5 bg-white dark:bg-navy-900">
                  <span className="text-slate-500 capitalize">{key.replace(/_/g, ' ')}</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200 truncate max-w-[150px]">
                    {String(value)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Multi-Claim Linkage (Collusion warning if person/org connected to multiple claims) */}
        {nodeType !== 'claim' && (
          <div className="space-y-2 pt-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Neighboring Claims ({connectedNodesList.filter((n) => n.type === 'claim').length})
            </span>
            <div className="space-y-1.5 max-h-36 overflow-y-auto">
              {connectedNodesList
                .filter((n) => n.type === 'claim')
                .map((claimNode) => (
                  <div
                    key={claimNode.id}
                    className="p-2 rounded-lg bg-slate-50 dark:bg-navy-950/70 border border-slate-200 dark:border-navy-800 flex items-center justify-between text-xs"
                  >
                    <div className="flex items-center gap-1.5 truncate">
                      <FileText className="h-3.5 w-3.5 text-brand-500 shrink-0" />
                      <span className="font-semibold text-slate-800 dark:text-slate-200 truncate">
                        {claimNode.label}
                      </span>
                    </div>
                    {claimNode.is_target ? (
                      <span className="text-[10px] font-bold text-brand-500 shrink-0">Current</span>
                    ) : (
                      <Link
                        to={`/claims/${claimNode.id}`}
                        className="text-brand-500 hover:underline inline-flex items-center gap-0.5 text-[11px] shrink-0"
                      >
                        <span>Open</span>
                        <ExternalLink className="h-3 w-3" />
                      </Link>
                    )}
                  </div>
                ))}
            </div>
          </div>
        )}

        {/* If this node is an external claim, show Quick Link to its Caseload */}
        {nodeType === 'claim' && !isTarget && (
          <div className="pt-2">
            <Link to={`/claims/${node.id}`}>
              <button className="w-full flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-semibold bg-brand-500 text-white hover:bg-brand-600 transition-colors shadow-xs">
                <span>Investigate Claim 360</span>
                <ExternalLink className="h-3.5 w-3.5" />
              </button>
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};
