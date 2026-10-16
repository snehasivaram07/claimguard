import React from 'react';
import { useParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';

export const ClaimWorkspacePage: React.FC = () => {
  const { claimId } = useParams<{ claimId: string }>();

  return (
    <div className="space-y-6">
      <div className="pb-2">
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          Claim 360 Workspace
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Investigating Claim ID: <span className="font-mono text-brand-500">{claimId || 'CLM-DEMO'}</span>
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>5-Tab Investigation Workspace</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-600 dark:text-slate-300">
            This workspace includes Overview, Document Hub, Timeline & Contradiction Board, Fraud Network Graph, and SIU Dossier generation.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};
