import React, { useState } from 'react';
import { Modal } from '../../components/ui/Modal';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import { claimService } from '../../services/claim-service';
import type { Claim, ClaimCreateRequest } from '../../types';

interface CreateClaimModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (claim: Claim) => void;
}

export const CreateClaimModal: React.FC<CreateClaimModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [title, setTitle] = useState('');
  const [claimType, setClaimType] = useState('AUTO');
  const [claimNumber, setClaimNumber] = useState('');
  const [policyNumber, setPolicyNumber] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setError('Claim title is required.');
      return;
    }

    setLoading(true);
    setError(null);

    const payload: ClaimCreateRequest = {
      title: title.trim(),
      claim_type: claimType,
      claim_number: claimNumber.trim() || null,
      policy_number: policyNumber.trim() || null,
      description: description.trim() || '',
    };

    try {
      const created = await claimService.createClaim(payload);
      // Reset form
      setTitle('');
      setClaimNumber('');
      setPolicyNumber('');
      setDescription('');
      onSuccess(created);
      onClose();
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { message?: string } } };
      setError(
        axiosErr.response?.data?.message || 'Failed to create claim. Please verify your inputs.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Create New Insurance Claim"
      description="Initialize a new insurance file for evidence collection, entity extraction, and timeline analysis."
      maxWidth="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3.5 text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/40 rounded-xl border border-red-200 dark:border-red-900/60">
            {error}
          </div>
        )}

        <Input
          label="Claim Title *"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g. Commercial Vehicle Intersection Collision"
          required
          autoFocus
          maxLength={255}
        />

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
              Claim Category
            </label>
            <select
              value={claimType}
              onChange={(e) => setClaimType(e.target.value)}
              className="block w-full rounded-xl border border-slate-300 dark:border-navy-750 bg-white dark:bg-navy-900 text-slate-900 dark:text-slate-100 py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500"
            >
              <option value="AUTO">Auto Collision</option>
              <option value="PROPERTY">Property / Homeowner</option>
              <option value="HEALTH">Health / Bodily Injury</option>
              <option value="WORKERS_COMP">Workers Compensation</option>
              <option value="GENERAL">General Liability</option>
            </select>
          </div>

          <Input
            label="Claim Reference #"
            value={claimNumber}
            onChange={(e) => setClaimNumber(e.target.value)}
            placeholder="e.g. CLM-2024-991"
            maxLength={64}
          />
        </div>

        <Input
          label="Policy Reference #"
          value={policyNumber}
          onChange={(e) => setPolicyNumber(e.target.value)}
          placeholder="e.g. POL-AZ-4421"
          maxLength={64}
        />

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
            Initial Circumstances & Notes
          </label>
          <textarea
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Brief narrative of reported accident, claimed injuries, or initial fraud suspicion..."
            className="block w-full rounded-xl border border-slate-300 dark:border-navy-750 bg-white dark:bg-navy-900 text-slate-900 dark:text-slate-100 p-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500"
            maxLength={4000}
          />
        </div>

        <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100 dark:border-navy-800">
          <Button type="button" variant="outline" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" isLoading={loading}>
            Register Claim
          </Button>
        </div>
      </form>
    </Modal>
  );
};
