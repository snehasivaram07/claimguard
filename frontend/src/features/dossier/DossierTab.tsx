import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  AlertCircle,
  RotateCw,
} from 'lucide-react';
import { dossierService } from '../../services/dossier-service';
import { DossierOverview } from './DossierOverview';
import { ExportCenter } from './ExportCenter';
import { PrioritizedActionChecklist } from './PrioritizedActionChecklist';
import { EvidenceSummaryTable } from './EvidenceSummaryTable';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { Button } from '../../components/ui/Button';

interface DossierTabProps {
  claimId: string;
}

export const DossierTab: React.FC<DossierTabProps> = ({ claimId }) => {
  const {
    data: dossier,
    isLoading,
    error,
    refetch,
    isRefetching,
  } = useQuery({
    queryKey: ['claim-dossier', claimId],
    queryFn: () => dossierService.getDossier(claimId),
  });

  if (isLoading) {
    return (
      <div className="py-24 flex flex-col items-center justify-center space-y-3">
        <LoadingSpinner size="lg" label="Synthesizing forensic SIU dossier and evidentiary report..." />
      </div>
    );
  }

  if (error || !dossier) {
    return (
      <div className="p-8 text-center bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700/80 rounded-xl space-y-4 max-w-lg mx-auto">
        <AlertCircle className="h-10 w-10 text-rose-500 mx-auto" />
        <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
          Failed to Generate Dossier
        </h3>
        <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
          Could not assemble the forensic claim brief. Ensure all documents and intelligence extractions are accessible.
        </p>
        <Button
          variant="primary"
          size="sm"
          onClick={() => refetch()}
          leftIcon={<RotateCw className={`h-4 w-4 ${isRefetching ? 'animate-spin' : ''}`} />}
        >
          {isRefetching ? 'Retrying...' : 'Retry Generation'}
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 1. Dossier Header & Executive Brief Overview */}
      <DossierOverview dossier={dossier} />

      {/* 2. Multi-Format Export Center (HTML, Markdown, JSON) */}
      <ExportCenter claimId={claimId} />

      {/* 3. Prioritized Action Checklist */}
      <PrioritizedActionChecklist recommendations={dossier.investigator_recommendations} />

      {/* 4. Evidentiary Document Inventory & Grounding Summary */}
      <EvidenceSummaryTable claimId={claimId} documents={dossier.documents_summary} />
    </div>
  );
};
