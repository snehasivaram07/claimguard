import React from 'react';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { EmptyState } from '../../components/ui/EmptyState';
import {
  FileText,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Edit2,
  Archive,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import type { Claim } from '../../types';

interface ClaimsTableProps {
  claims: Claim[];
  total: number;
  skip: number;
  limit: number;
  onPageChange: (newSkip: number) => void;
  onEdit: (claim: Claim) => void;
  onArchive: (claim: Claim) => void;
  isLoading?: boolean;
  hasFilters?: boolean;
  onClearFilters?: () => void;
  onCreateClaim?: () => void;
}

export const ClaimsTable: React.FC<ClaimsTableProps> = ({
  claims,
  total,
  skip,
  limit,
  onPageChange,
  onEdit,
  onArchive,
  isLoading = false,
  hasFilters = false,
  onClearFilters,
  onCreateClaim,
}) => {
  const currentPage = Math.floor(skip / limit) + 1;
  const totalPages = Math.ceil(total / limit) || 1;
  const fromRecord = total === 0 ? 0 : skip + 1;
  const toRecord = Math.min(skip + limit, total);

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-750 rounded-2xl p-6 shadow-sm space-y-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className="h-14 bg-slate-100 dark:bg-navy-800 animate-pulse rounded-xl"
          />
        ))}
      </div>
    );
  }

  if (claims.length === 0) {
    return (
      <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-750 rounded-2xl p-6 shadow-sm">
        {hasFilters ? (
          <EmptyState
            icon={<FileText className="h-7 w-7" />}
            title="No Matching Claims Found"
            description="No claim records match your current search and filter criteria. Try resetting your filters."
            actionLabel="Clear Filter Criteria"
            onAction={onClearFilters}
          />
        ) : (
          <EmptyState
            icon={<FileText className="h-7 w-7" />}
            title="Your Claims Caseload is Empty"
            description="Start building your portfolio by creating your first claim file to upload evidence and trigger AI discrepancy detection."
            actionLabel="Create First Claim"
            onAction={onCreateClaim}
          />
        )}
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-750 rounded-2xl shadow-sm overflow-hidden flex flex-col">
      <div className="overflow-x-auto flex-1">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50/80 dark:bg-navy-850 text-slate-500 dark:text-slate-400 font-semibold uppercase tracking-wider border-b border-slate-200 dark:border-navy-800">
            <tr>
              <th className="py-3.5 px-5">Claim Reference</th>
              <th className="py-3.5 px-4">Category</th>
              <th className="py-3.5 px-4">Status</th>
              <th className="py-3.5 px-4">Policy #</th>
              <th className="py-3.5 px-4">Date Created</th>
              <th className="py-3.5 px-5 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-navy-800/80">
            {claims.map((claim) => (
              <tr
                key={claim.id}
                className="hover:bg-slate-50/80 dark:hover:bg-navy-800/40 transition-colors group"
              >
                {/* Title & Internal ID */}
                <td className="py-4 px-5">
                  <div className="flex flex-col">
                    <Link
                      to={`/claims/${claim.id}`}
                      className="font-semibold text-slate-900 dark:text-slate-100 hover:text-brand-500 dark:hover:text-brand-400 transition-colors max-w-sm truncate text-sm"
                      title={claim.title}
                    >
                      {claim.title}
                    </Link>
                    <div className="flex items-center gap-2 mt-0.5 text-[11px] text-slate-400 font-mono">
                      <span>{claim.claim_number || 'NO-REF-NUMBER'}</span>
                      <span>•</span>
                      <span className="truncate max-w-[120px]">{claim.id.slice(0, 13)}...</span>
                    </div>
                  </div>
                </td>

                {/* Category */}
                <td className="py-4 px-4">
                  <Badge variant="neutral" size="sm" className="font-mono uppercase text-[10px]">
                    {claim.claim_type}
                  </Badge>
                </td>

                {/* Status */}
                <td className="py-4 px-4">
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
                </td>

                {/* Policy Number */}
                <td className="py-4 px-4 font-mono text-slate-600 dark:text-slate-300">
                  {claim.policy_number || '—'}
                </td>

                {/* Created Date */}
                <td className="py-4 px-4 text-slate-500 dark:text-slate-400">
                  {new Date(claim.created_at).toLocaleDateString([], {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                  })}
                </td>

                {/* Actions */}
                <td className="py-4 px-5 text-right">
                  <div className="flex items-center justify-end gap-1">
                    <Link to={`/claims/${claim.id}`}>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="text-slate-600 dark:text-slate-300 hover:text-brand-500 dark:hover:text-brand-400"
                        title="Open Investigation Workspace"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </Button>
                    </Link>

                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => onEdit(claim)}
                      className="text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white"
                      title="Edit Claim"
                    >
                      <Edit2 className="h-4 w-4" />
                    </Button>

                    {claim.status !== 'ARCHIVED' && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => onArchive(claim)}
                        className="text-slate-400 hover:text-red-500 dark:hover:text-red-400"
                        title="Archive Claim"
                      >
                        <Archive className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="px-5 py-4 bg-slate-50/50 dark:bg-navy-950/40 border-t border-slate-100 dark:border-navy-800 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500 dark:text-slate-400">
        <div>
          Showing <span className="font-semibold text-slate-900 dark:text-slate-100">{fromRecord}</span> to{' '}
          <span className="font-semibold text-slate-900 dark:text-slate-100">{toRecord}</span> of{' '}
          <span className="font-semibold text-slate-900 dark:text-slate-100">{total}</span> claim records
        </div>

        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            disabled={skip === 0}
            onClick={() => onPageChange(Math.max(0, skip - limit))}
            leftIcon={<ChevronLeft className="h-4 w-4" />}
          >
            Previous
          </Button>
          <span className="px-2 font-medium">
            Page {currentPage} of {totalPages}
          </span>
          <Button
            size="sm"
            variant="outline"
            disabled={skip + limit >= total}
            onClick={() => onPageChange(skip + limit)}
            rightIcon={<ChevronRight className="h-4 w-4" />}
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  );
};
