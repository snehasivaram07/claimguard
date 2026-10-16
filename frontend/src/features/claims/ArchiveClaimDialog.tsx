import React, { useState } from 'react';
import { Modal } from '../../components/ui/Modal';
import { Button } from '../../components/ui/Button';
import { AlertTriangle } from 'lucide-react';
import { claimService } from '../../services/claim-service';
import type { Claim } from '../../types';

interface ArchiveClaimDialogProps {
  isOpen: boolean;
  claim: Claim | null;
  onClose: () => void;
  onSuccess: (archivedId: string) => void;
}

export const ArchiveClaimDialog: React.FC<ArchiveClaimDialogProps> = ({
  isOpen,
  claim,
  onClose,
  onSuccess,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleArchive = async () => {
    if (!claim) return;
    setLoading(true);
    setError(null);

    try {
      await claimService.archiveClaim(claim.id);
      onSuccess(claim.id);
      onClose();
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { message?: string } } };
      setError(
        axiosErr.response?.data?.message || 'Failed to archive claim. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Archive Claim Record"
      maxWidth="md"
    >
      <div className="space-y-4">
        <div className="flex items-start gap-3 p-3.5 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60 text-amber-800 dark:text-amber-300 text-xs leading-relaxed">
          <AlertTriangle className="h-5 w-5 shrink-0 text-amber-500 mt-0.5" />
          <div>
            <p className="font-semibold">Soft-Delete Confirmation</p>
            <p className="mt-0.5">
              Archiving will mark this claim status as <strong>ARCHIVED</strong>. It will be hidden from active caseload searches unless explicitly filtered. All evidentiary documents and audit logs are securely retained.
            </p>
          </div>
        </div>

        {error && (
          <div className="p-3 text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/40 rounded-xl border border-red-200 dark:border-red-900/60">
            {error}
          </div>
        )}

        <div className="p-3 rounded-xl bg-slate-50 dark:bg-navy-850 border border-slate-200 dark:border-navy-750 text-xs">
          <p className="text-slate-500 dark:text-slate-400">Target Claim File:</p>
          <p className="text-sm font-semibold text-slate-900 dark:text-slate-100 mt-0.5">
            {claim?.title}
          </p>
          <p className="font-mono text-slate-400 mt-0.5">
            ID: {claim?.id}
          </p>
        </div>

        <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100 dark:border-navy-800">
          <Button type="button" variant="outline" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button
            type="button"
            variant="danger"
            isLoading={loading}
            onClick={handleArchive}
          >
            Confirm & Archive
          </Button>
        </div>
      </div>
    </Modal>
  );
};
