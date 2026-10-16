import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { EmptyState } from '../../components/ui/EmptyState';
import { FileText, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { Claim } from '../../types';

interface RecentClaimsWidgetProps {
  claims: Claim[];
  isLoading?: boolean;
  onCreateClaim?: () => void;
}

export const RecentClaimsWidget: React.FC<RecentClaimsWidgetProps> = ({
  claims,
  isLoading = false,
  onCreateClaim,
}) => {
  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <div>
          <CardTitle>Recent Claims Caseload</CardTitle>
          <CardDescription>
            Latest insurance claims under active investigation.
          </CardDescription>
        </div>
        <Link to="/claims" className="text-xs font-semibold text-brand-500 hover:text-brand-400">
          View all claims &rarr;
        </Link>
      </CardHeader>

      <CardContent className="flex-1 p-0">
        {isLoading ? (
          <div className="p-6 space-y-4">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-12 bg-slate-100 dark:bg-navy-800 animate-pulse rounded-lg"
              />
            ))}
          </div>
        ) : claims.length === 0 ? (
          <div className="p-6">
            <EmptyState
              icon={<FileText className="h-6 w-6" />}
              title="No Claims Created Yet"
              description="Start by creating your first claim to attach evidence and run AI cross-document forensics."
              actionLabel="Create Claim"
              onAction={onCreateClaim}
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-navy-850/80 text-slate-500 dark:text-slate-400 font-semibold uppercase tracking-wider border-b border-slate-200 dark:border-navy-800">
                <tr>
                  <th className="py-3 px-4">Claim</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Created</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-navy-800">
                {claims.map((claim) => (
                  <tr
                    key={claim.id}
                    className="hover:bg-slate-50/80 dark:hover:bg-navy-800/40 transition-colors"
                  >
                    <td className="py-3 px-4 font-medium text-slate-900 dark:text-slate-100">
                      <div className="truncate max-w-[200px]" title={claim.title}>
                        {claim.title}
                      </div>
                      <div className="text-[11px] font-mono text-slate-400">
                        {claim.claim_number || claim.id.slice(0, 8)}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-mono text-slate-600 dark:text-slate-300 uppercase text-[11px]">
                        {claim.claim_type}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <Badge
                        variant={
                          claim.status === 'OPEN'
                            ? 'warning'
                            : claim.status === 'CLOSED'
                            ? 'success'
                            : 'neutral'
                        }
                        size="sm"
                      >
                        {claim.status}
                      </Badge>
                    </td>
                    <td className="py-3 px-4 text-slate-500 dark:text-slate-400">
                      {new Date(claim.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Link to={`/claims/${claim.id}`}>
                        <Button size="sm" variant="ghost">
                          Inspect
                        </Button>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>

      <CardFooter className="py-3">
        <span className="text-xs text-slate-500 dark:text-slate-400">
          Showing {claims.length} recent claim records
        </span>
        <Link to="/claims">
          <Button size="sm" variant="outline" rightIcon={<ArrowRight className="h-3.5 w-3.5" />}>
            All Claims
          </Button>
        </Link>
      </CardFooter>
    </Card>
  );
};
