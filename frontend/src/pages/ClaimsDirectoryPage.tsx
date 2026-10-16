import React, { useState, useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { claimService } from '../services/claim-service';
import { ClaimFilters } from '../features/claims/ClaimFilters';
import { ClaimsTable } from '../features/claims/ClaimsTable';
import { CreateClaimModal } from '../features/claims/CreateClaimModal';
import { EditClaimModal } from '../features/claims/EditClaimModal';
import { ArchiveClaimDialog } from '../features/claims/ArchiveClaimDialog';
import { Button } from '../components/ui/Button';
import { Plus, RefreshCw } from 'lucide-react';
import type { Claim } from '../types';

export const ClaimsDirectoryPage: React.FC = () => {
  const queryClient = useQueryClient();

  // Pagination & Filter States
  const [skip, setSkip] = useState(0);
  const [limit] = useState(25);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [typeFilter, setTypeFilter] = useState('ALL');

  // Modal Dialog States
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingClaim, setEditingClaim] = useState<Claim | null>(null);
  const [archivingClaim, setArchivingClaim] = useState<Claim | null>(null);

  // Live Query
  const includeArchived = statusFilter === 'ARCHIVED' || statusFilter === 'ALL';
  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['claims-list', skip, limit, includeArchived],
    queryFn: () => claimService.listClaims(skip, limit, includeArchived),
  });

  // Client-side refinement for instant search and sub-filters
  const filteredClaims = useMemo(() => {
    if (!data?.items) return [];

    return data.items.filter((claim) => {
      // 1. Status Filter
      if (statusFilter !== 'ALL' && claim.status !== statusFilter) {
        return false;
      }
      // 2. Type Filter
      if (typeFilter !== 'ALL' && claim.claim_type !== typeFilter) {
        return false;
      }
      // 3. Search Query
      if (searchQuery.trim() !== '') {
        const query = searchQuery.toLowerCase();
        const matchesTitle = claim.title.toLowerCase().includes(query);
        const matchesClaimNum = claim.claim_number?.toLowerCase().includes(query);
        const matchesPolicyNum = claim.policy_number?.toLowerCase().includes(query);
        const matchesId = claim.id.toLowerCase().includes(query);
        return matchesTitle || matchesClaimNum || matchesPolicyNum || matchesId;
      }
      return true;
    });
  }, [data?.items, statusFilter, typeFilter, searchQuery]);

  const handleClearFilters = () => {
    setSearchQuery('');
    setStatusFilter('ALL');
    setTypeFilter('ALL');
    setSkip(0);
  };

  const handleMutationSuccess = () => {
    queryClient.invalidateQueries({ queryKey: ['claims-list'] });
    queryClient.invalidateQueries({ queryKey: ['claims-list-dashboard'] });
  };

  const hasActiveFilters = searchQuery !== '' || statusFilter !== 'ALL' || typeFilter !== 'ALL';

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-1">
        <div>
          <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">
            Claims Caseload Directory
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            Search, filter, manage, and investigate insurance claims across your assigned portfolio.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="md"
            onClick={() => refetch()}
            disabled={isFetching}
            leftIcon={<RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />}
          >
            Refresh
          </Button>

          <Button
            variant="primary"
            size="md"
            onClick={() => setIsCreateOpen(true)}
            leftIcon={<Plus className="h-4 w-4" />}
          >
            New Claim
          </Button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <ClaimFilters
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        statusFilter={statusFilter}
        setStatusFilter={(val) => {
          setStatusFilter(val);
          setSkip(0);
        }}
        typeFilter={typeFilter}
        setTypeFilter={(val) => {
          setTypeFilter(val);
          setSkip(0);
        }}
        onClearFilters={handleClearFilters}
      />

      {/* Main Table */}
      <ClaimsTable
        claims={filteredClaims}
        total={data?.total || filteredClaims.length}
        skip={skip}
        limit={limit}
        onPageChange={(newSkip) => setSkip(newSkip)}
        onEdit={(claim) => setEditingClaim(claim)}
        onArchive={(claim) => setArchivingClaim(claim)}
        isLoading={isLoading}
        hasFilters={hasActiveFilters}
        onClearFilters={handleClearFilters}
        onCreateClaim={() => setIsCreateOpen(true)}
      />

      {/* Modals */}
      <CreateClaimModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onSuccess={handleMutationSuccess}
      />

      <EditClaimModal
        isOpen={!!editingClaim}
        claim={editingClaim}
        onClose={() => setEditingClaim(null)}
        onSuccess={handleMutationSuccess}
      />

      <ArchiveClaimDialog
        isOpen={!!archivingClaim}
        claim={archivingClaim}
        onClose={() => setArchivingClaim(null)}
        onSuccess={handleMutationSuccess}
      />
    </div>
  );
};
