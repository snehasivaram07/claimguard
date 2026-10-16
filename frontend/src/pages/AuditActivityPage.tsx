import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { ShieldCheck } from 'lucide-react';
import { EmptyState } from '../components/ui/EmptyState';

export const AuditActivityPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="pb-2">
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          Security & Audit Activity Trail
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Tamper-proof chronological log of all investigative access, claim views, and dossier exports.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Audit Log</CardTitle>
          <CardDescription>
            Immutable event records from PostgreSQL audit repository.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={<ShieldCheck className="h-7 w-7" />}
            title="Audit Logger Active"
            description="All user logins, claim updates, and analysis requests are being tracked by the backend. In Milestone 9, your personal audit log will render here."
          />
        </CardContent>
      </Card>
    </div>
  );
};
