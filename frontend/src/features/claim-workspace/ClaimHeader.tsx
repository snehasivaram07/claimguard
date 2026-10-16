import React from 'react';
import { Link } from 'react-router-dom';
import { Badge } from '../../components/ui/Badge';
import {
  ArrowLeft,
  FileText,
  FolderOpen,
  Clock,
  Network,
  FileCheck,
} from 'lucide-react';
import type { Claim } from '../../types';

export type WorkspaceTab =
  | 'overview'
  | 'documents'
  | 'intelligence'
  | 'network'
  | 'dossier';

interface ClaimHeaderProps {
  claim: Claim;
  activeTab: WorkspaceTab;
  onTabChange: (tab: WorkspaceTab) => void;
  documentCount?: number;
}

export const ClaimHeader: React.FC<ClaimHeaderProps> = ({
  claim,
  activeTab,
  onTabChange,
  documentCount = 0,
}) => {
  const tabs = [
    { id: 'overview' as const, label: 'Overview', icon: FileText },
    {
      id: 'documents' as const,
      label: 'Document Hub',
      icon: FolderOpen,
      count: documentCount,
    },
    { id: 'intelligence' as const, label: 'Timeline & Discrepancies', icon: Clock },
    { id: 'network' as const, label: 'Fraud Network Graph', icon: Network },
    { id: 'dossier' as const, label: 'SIU Forensic Dossier', icon: FileCheck },
  ];

  return (
    <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-750 rounded-2xl shadow-sm overflow-hidden mb-6">
      {/* Top Breadcrumb & Metadata Section */}
      <div className="p-5 sm:p-6 pb-4 border-b border-slate-100 dark:border-navy-800">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <Link
                to="/claims"
                className="inline-flex items-center gap-1 text-xs font-semibold text-slate-500 hover:text-brand-500 dark:text-slate-400 dark:hover:text-brand-400 transition-colors"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                Claims Caseload
              </Link>
              <span className="text-slate-300 dark:text-navy-700">/</span>
              <span className="text-xs font-mono text-slate-400">{claim.id.slice(0, 8)}...</span>
            </div>

            <div className="flex flex-wrap items-center gap-2.5">
              <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
                {claim.title}
              </h2>
              <Badge
                variant={
                  claim.status === 'OPEN'
                    ? 'warning'
                    : claim.status === 'CLOSED'
                    ? 'success'
                    : 'neutral'
                }
                size="sm"
              >
                {claim.status}
              </Badge>
              <Badge variant="neutral" size="sm" className="font-mono uppercase text-[10px]">
                {claim.claim_type}
              </Badge>
            </div>
          </div>

          {/* Reference IDs pill */}
          <div className="flex items-center gap-3 p-2.5 rounded-xl bg-slate-50 dark:bg-navy-850 border border-slate-200 dark:border-navy-800 text-xs shrink-0">
            <div>
              <p className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
                Claim Ref #
              </p>
              <p className="font-mono font-medium text-slate-800 dark:text-slate-200 mt-0.5">
                {claim.claim_number || 'UNASSIGNED'}
              </p>
            </div>
            <div className="h-6 w-px bg-slate-200 dark:bg-navy-750" />
            <div>
              <p className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
                Policy Ref #
              </p>
              <p className="font-mono font-medium text-slate-800 dark:text-slate-200 mt-0.5">
                {claim.policy_number || 'UNASSIGNED'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 5-Tabs Navigation Bar */}
      <div className="flex items-center px-4 overflow-x-auto no-scrollbar bg-slate-50/50 dark:bg-navy-950/40">
        <nav className="flex space-x-1 sm:space-x-2 py-2" aria-label="Investigation tabs">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`flex items-center gap-2 px-3.5 py-2 text-xs sm:text-sm font-semibold rounded-xl transition-all whitespace-nowrap select-none ${
                  isActive
                    ? 'bg-brand-500 text-white shadow-sm'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-200/50 dark:hover:bg-navy-800'
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{tab.label}</span>
                {typeof tab.count === 'number' && (
                  <span
                    className={`ml-1 px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
                      isActive
                        ? 'bg-white/20 text-white'
                        : 'bg-slate-200 dark:bg-navy-800 text-slate-700 dark:text-slate-300'
                    }`}
                  >
                    {tab.count}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>
    </div>
  );
};
