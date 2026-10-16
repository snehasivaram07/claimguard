import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { EmptyState } from '../components/ui/EmptyState';
import { FileText } from 'lucide-react';

export const ClaimsDirectoryPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="pb-2">
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          Claims Directory
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Manage, search, and investigate insurance claims under active investigation.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Claims Database</CardTitle>
          <CardDescription>
            Server-side paginated claims list with type and status filtering will be fully integrated in Milestone 4.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={<FileText className="h-7 w-7" />}
            title="Claims Directory Ready"
            description="The Claims CRUD foundation is active. In Milestone 4, all claims will populate here with live search, filtering, and create modals."
          />
        </CardContent>
      </Card>
    </div>
  );
};
