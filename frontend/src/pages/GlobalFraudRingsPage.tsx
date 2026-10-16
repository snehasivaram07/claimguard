import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { Network } from 'lucide-react';
import { EmptyState } from '../components/ui/EmptyState';

export const GlobalFraudRingsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="pb-2">
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          Fraud Rings Explorer
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Multi-claim collusion network detection, staged collisions, and repeat claimant syndicates.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Tenant-Wide Collusion Radar</CardTitle>
          <CardDescription>
            Powered by FalkorDB Cypher traversal.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={<Network className="h-7 w-7" />}
            title="Fraud Ring Radar Active"
            description="The FalkorDB graph backend query pipeline is fully functional. In Milestone 9, multi-claim syndicates will render here with full network exploration."
          />
        </CardContent>
      </Card>
    </div>
  );
};
