import React from 'react';
import { Search, X, Filter } from 'lucide-react';
import { Button } from '../../components/ui/Button';

interface ClaimFiltersProps {
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  statusFilter: string;
  setStatusFilter: (status: string) => void;
  typeFilter: string;
  setTypeFilter: (type: string) => void;
  onClearFilters: () => void;
}

export const ClaimFilters: React.FC<ClaimFiltersProps> = ({
  searchQuery,
  setSearchQuery,
  statusFilter,
  setStatusFilter,
  typeFilter,
  setTypeFilter,
  onClearFilters,
}) => {
  const hasActiveFilters = searchQuery !== '' || statusFilter !== 'ALL' || typeFilter !== 'ALL';

  return (
    <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-750 rounded-2xl p-4 shadow-sm space-y-3">
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
        {/* Search Bar */}
        <div className="relative flex-1">
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">
            <Search className="h-4 w-4" />
          </div>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by title, claim #, policy #..."
            className="block w-full rounded-xl border border-slate-300 dark:border-navy-750 bg-slate-50 dark:bg-navy-850 pl-9 pr-3.5 py-2 text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500 transition-all"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute inset-y-0 right-0 flex items-center pr-3 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* Status Selector */}
        <div className="w-full sm:w-44">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="block w-full rounded-xl border border-slate-300 dark:border-navy-750 bg-slate-50 dark:bg-navy-850 py-2 px-3 text-sm text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500"
          >
            <option value="ALL">All Statuses</option>
            <option value="OPEN">Open Caseload</option>
            <option value="CLOSED">Closed Files</option>
            <option value="ARCHIVED">Archived Claims</option>
          </select>
        </div>

        {/* Type Selector */}
        <div className="w-full sm:w-48">
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="block w-full rounded-xl border border-slate-300 dark:border-navy-750 bg-slate-50 dark:bg-navy-850 py-2 px-3 text-sm text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500"
          >
            <option value="ALL">All Claim Types</option>
            <option value="AUTO">Auto Collision</option>
            <option value="PROPERTY">Property / Homeowner</option>
            <option value="HEALTH">Health / Bodily Injury</option>
            <option value="WORKERS_COMP">Workers Comp</option>
            <option value="GENERAL">General Liability</option>
          </select>
        </div>

        {/* Clear Filters Button */}
        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onClearFilters}
            leftIcon={<Filter className="h-3.5 w-3.5" />}
            className="text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 shrink-0"
          >
            Reset
          </Button>
        )}
      </div>
    </div>
  );
};
