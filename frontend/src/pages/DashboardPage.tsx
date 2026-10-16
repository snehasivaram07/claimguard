import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { claimService } from '../services/claim-service';
import { fraudRingService } from '../services/fraud-ring-service';
import { healthService } from '../services/health-service';
import { auditService } from '../services/audit-service';

import { LiveHealthWidget } from '../features/dashboard/LiveHealthWidget';
import { DashboardMetrics } from '../features/dashboard/DashboardMetrics';
import { PriorityActionCenter } from '../features/dashboard/PriorityActionCenter';
import { RecentClaimsWidget } from '../features/dashboard/RecentClaimsWidget';
import { RecentActivityWidget } from '../features/dashboard/RecentActivityWidget';

import { Button } from '../components/ui/Button';
import { Modal } from '../components/ui/Modal';
import { Input } from '../components/ui/Input';
import { Plus, RefreshCw } from 'lucide-react';
import type { ClaimCreateRequest } from '../types';

export const DashboardPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newClaimType, setNewClaimType] = useState('AUTO');
  const [newClaimNumber, setNewClaimNumber] = useState('');
  const [newPolicyNumber, setNewPolicyNumber] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  // Queries
  const {
    data: claimsData,
    isLoading: isClaimsLoading,
    refetch: refetchClaims,
  } = useQuery({
    queryKey: ['claims-list-dashboard'],
    queryFn: () => claimService.listClaims(0, 10),
  });

  const {
    data: fraudRingsData,
    isLoading: isRingsLoading,
    refetch: refetchRings,
  } = useQuery({
    queryKey: ['fraud-rings-dashboard'],
    queryFn: () => fraudRingService.listFraudRings(2),
  });

  const {
    data: healthData,
    isLoading: isHealthLoading,
    refetch: refetchHealth,
  } = useQuery({
    queryKey: ['health-readiness-dashboard'],
    queryFn: () => healthService.getReadiness(),
    refetchInterval: 30000,
  });

  const {
    data: auditData,
    isLoading: isAuditLoading,
    refetch: refetchAudit,
  } = useQuery({
    queryKey: ['user-audit-dashboard'],
    queryFn: () => auditService.getUserAudit(0, 5),
  });

  const handleRefreshAll = () => {
    refetchClaims();
    refetchRings();
    refetchHealth();
    refetchAudit();
  };

  // Create claim mutation
  const createClaimMutation = useMutation({
    mutationFn: (data: ClaimCreateRequest) => claimService.createClaim(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['claims-list-dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['user-audit-dashboard'] });
      setIsCreateModalOpen(false);
      setNewTitle('');
      setNewClaimNumber('');
      setNewPolicyNumber('');
      setNewDescription('');
      setFormError(null);
    },
    onError: (err: unknown) => {
      const axiosErr = err as { response?: { data?: { message?: string } } };
      setFormError(
        axiosErr.response?.data?.message || 'Failed to create claim. Please check inputs.'
      );
    },
  });

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) {
      setFormError('Claim title is required.');
      return;
    }
    createClaimMutation.mutate({
      title: newTitle.trim(),
      claim_type: newClaimType,
      claim_number: newClaimNumber.trim() || undefined,
      policy_number: newPolicyNumber.trim() || undefined,
      description: newDescription.trim() || undefined,
    });
  };

  const claims = claimsData?.items || [];
  const openClaims = claims.filter((c) => c.status === 'OPEN');
  const totalClaims = claimsData?.total || claims.length;
  const totalFraudRings = fraudRingsData?.total || fraudRingsData?.rings?.length || 0;
  const isEngineHealthy = healthData?.status === 'ready';

  return (
    <div className="space-y-6">
      {/* Top Welcome & Actions Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-1">
        <div>
          <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">
            SIU Investigation Command Center
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            Real-time claim evidence synthesis, multi-claim collusion networks, and forensic audit intelligence.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="md"
            onClick={handleRefreshAll}
            leftIcon={<RefreshCw className="h-4 w-4" />}
          >
            Refresh
          </Button>

          <Button
            variant="primary"
            size="md"
            onClick={() => setIsCreateModalOpen(true)}
            leftIcon={<Plus className="h-4 w-4" />}
          >
            New Claim
          </Button>
        </div>
      </div>

      {/* Live System Health Bar */}
      <LiveHealthWidget />

      {/* KPI Metric Cards */}
      <DashboardMetrics
        totalClaims={totalClaims}
        openClaims={openClaims.length}
        totalFraudRings={totalFraudRings}
        isEngineHealthy={isEngineHealthy}
        isLoading={isClaimsLoading || isRingsLoading || isHealthLoading}
      />

      {/* 2-Column Core Sections: Priority Action Center & Recent Caseload */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PriorityActionCenter
          fraudRings={fraudRingsData?.rings || []}
          openClaims={openClaims}
          isLoading={isRingsLoading || isClaimsLoading}
        />

        <RecentClaimsWidget
          claims={claims}
          isLoading={isClaimsLoading}
          onCreateClaim={() => setIsCreateModalOpen(true)}
        />
      </div>

      {/* Full-width Activity Trail */}
      <RecentActivityWidget
        events={auditData?.items || []}
        isLoading={isAuditLoading}
      />

      {/* New Claim Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Register New Claim Investigation"
        description="Initialize a new insurance claim file to begin evidence ingestion and cross-document analysis."
      >
        <form onSubmit={handleCreateSubmit} className="space-y-4">
          {formError && (
            <div className="p-3 text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/40 rounded-lg border border-red-200 dark:border-red-900/60">
              {formError}
            </div>
          )}

          <Input
            label="Claim Title *"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            placeholder="e.g. 2024 Interstate Multi-Vehicle Collision"
            required
            autoFocus
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                Claim Type
              </label>
              <select
                value={newClaimType}
                onChange={(e) => setNewClaimType(e.target.value)}
                className="block w-full rounded-lg border border-slate-300 dark:border-navy-750 bg-white dark:bg-navy-900 text-slate-900 dark:text-slate-100 py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500"
              >
                <option value="AUTO">Auto Collision</option>
                <option value="PROPERTY">Property / Homeowner</option>
                <option value="HEALTH">Health / Bodily Injury</option>
                <option value="WORKERS_COMP">Workers Compensation</option>
                <option value="GENERAL">General Liability</option>
              </select>
            </div>

            <Input
              label="Claim Number"
              value={newClaimNumber}
              onChange={(e) => setNewClaimNumber(e.target.value)}
              placeholder="e.g. CLM-2024-8841"
            />
          </div>

          <Input
            label="Policy Reference Number"
            value={newPolicyNumber}
            onChange={(e) => setNewPolicyNumber(e.target.value)}
            placeholder="e.g. POL-99201-B"
          />

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
              Case Description & Initial Notes
            </label>
            <textarea
              rows={3}
              value={newDescription}
              onChange={(e) => setNewDescription(e.target.value)}
              placeholder="Brief summary of reported loss, involved parties, or suspected inconsistencies..."
              className="block w-full rounded-lg border border-slate-300 dark:border-navy-750 bg-white dark:bg-navy-900 text-slate-900 dark:text-slate-100 p-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100 dark:border-navy-800">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsCreateModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              isLoading={createClaimMutation.isPending}
            >
              Create Claim File
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
