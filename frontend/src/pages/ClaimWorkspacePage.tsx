import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { claimService } from '../services/claim-service';
import { documentService } from '../services/document-service';
import { ClaimHeader } from '../features/claim-workspace/ClaimHeader';
import type { WorkspaceTab } from '../features/claim-workspace/ClaimHeader';
import { OverviewTab } from '../features/claim-workspace/OverviewTab';
import { DocumentHubTab } from '../features/documents/DocumentHubTab';
import { TimelineContradictionsTab } from '../features/intelligence/TimelineContradictionsTab';
import { FraudNetworkTab } from '../features/network/FraudNetworkTab';
import { EditClaimModal } from '../features/claims/EditClaimModal';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { FileCheck, ArrowLeft } from 'lucide-react';

export const ClaimWorkspacePage: React.FC = () => {
  const { claimId } = useParams<{ claimId: string }>();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<WorkspaceTab>('overview');
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);

  // Fetch Claim Details
  const {
    data: claim,
    isLoading: isClaimLoading,
    error: claimError,
  } = useQuery({
    queryKey: ['claim-details', claimId],
    queryFn: () => claimService.getClaim(claimId || ''),
    enabled: !!claimId,
  });

  // Fetch Documents Count
  const { data: docData } = useQuery({
    queryKey: ['claim-documents', claimId],
    queryFn: () => documentService.listDocuments(claimId || ''),
    enabled: !!claimId,
  });

  if (isClaimLoading) {
    return (
      <div className="py-24 flex flex-col items-center justify-center">
        <LoadingSpinner size="lg" label="Loading claim investigation workspace..." />
      </div>
    );
  }

  if (claimError || !claim) {
    return (
      <Card className="max-w-lg mx-auto my-12 text-center p-8">
        <CardContent className="space-y-4">
          <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
            Claim Not Found
          </h3>
          <p className="text-xs text-slate-500 leading-relaxed">
            The requested claim does not exist or belongs to another tenant. Under strict tenant isolation policies, access is restricted.
          </p>
          <Link to="/claims">
            <Button variant="primary" size="md" leftIcon={<ArrowLeft className="h-4 w-4" />}>
              Return to Claims Caseload
            </Button>
          </Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Claim 360 Header with 5 Tabs Navigation */}
      <ClaimHeader
        claim={claim}
        activeTab={activeTab}
        onTabChange={(tab) => setActiveTab(tab)}
        documentCount={docData?.total || docData?.items?.length || 0}
      />

      {/* Tab 1: Overview */}
      {activeTab === 'overview' && (
        <OverviewTab
          claim={claim}
          onEdit={() => setIsEditModalOpen(true)}
        />
      )}

      {/* Tab 2: Document Hub */}
      {activeTab === 'documents' && (
        <DocumentHubTab claimId={claim.id} />
      )}

      {/* Tab 3: Reconstructed Timeline & Contradiction Board */}
      {activeTab === 'intelligence' && (
        <TimelineContradictionsTab claimId={claim.id} />
      )}

      {/* Tab 4: Interactive Fraud Network Graph */}
      {activeTab === 'network' && (
        <FraudNetworkTab claimId={claim.id} />
      )}

      {/* Tab 5: SIU Forensic Dossier Placeholder (Milestone 8) */}
      {activeTab === 'dossier' && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <FileCheck className="h-5 w-5 text-emerald-500" />
              <CardTitle>Forensic SIU Dossier & Export Center</CardTitle>
            </div>
            <CardDescription>
              Executive investigative summary, categorized action checklist, and print-ready HTML / Markdown / JSON export.
            </CardDescription>
          </CardHeader>
          <CardContent className="py-12 text-center text-slate-500">
            <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">
              Ready for Milestone 8 Integration
            </p>
            <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
              Full dossier synthesis with categorized recommendations and one-click court-ready file exports.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Edit Claim Metadata Modal */}
      <EditClaimModal
        isOpen={isEditModalOpen}
        claim={claim}
        onClose={() => setIsEditModalOpen(false)}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ['claim-details', claim.id] });
          queryClient.invalidateQueries({ queryKey: ['claims-list'] });
        }}
      />
    </div>
  );
};
