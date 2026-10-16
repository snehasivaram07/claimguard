import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { claimService } from '../../services/claim-service';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { Edit2, ShieldCheck, Clock, Calendar } from 'lucide-react';
import type { Claim } from '../../types';

interface OverviewTabProps {
  claim: Claim;
  onEdit: () => void;
}

export const OverviewTab: React.FC<OverviewTabProps> = ({ claim, onEdit }) => {
  const { data: auditData, isLoading: isAuditLoading } = useQuery({
    queryKey: ['claim-audit', claim.id],
    queryFn: () => claimService.getClaimAudit(claim.id, 0, 10),
  });

  return (
    <div className="space-y-6">
      {/* Narrative & Details Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2 cols): Case Description & Findings */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <div>
                <CardTitle>Case Narrative & Incident Circumstances</CardTitle>
                <CardDescription>
                  Reported accident facts and initial adjuster notes.
                </CardDescription>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={onEdit}
                leftIcon={<Edit2 className="h-3.5 w-3.5" />}
              >
                Edit Details
              </Button>
            </CardHeader>

            <CardContent>
              {claim.description ? (
                <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-wrap">
                  {claim.description}
                </p>
              ) : (
                <div className="py-6 text-center text-slate-400 text-xs italic">
                  No detailed description recorded yet. Click "Edit Details" to add notes.
                </div>
              )}
            </CardContent>
          </Card>

          {/* Claim Lifecycle & Security Metadata */}
          <Card>
            <CardHeader>
              <CardTitle>Audit & Security Governance</CardTitle>
              <CardDescription>
                Tenant boundary and cryptographic integrity metadata.
              </CardDescription>
            </CardHeader>
            <CardContent className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-850 border border-slate-200 dark:border-navy-800">
                <span className="text-slate-400 uppercase text-[10px] font-semibold tracking-wider">
                  Tenant Owner ID
                </span>
                <p className="font-mono text-slate-800 dark:text-slate-200 mt-1 truncate">
                  {claim.owner_id}
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-850 border border-slate-200 dark:border-navy-800">
                <span className="text-slate-400 uppercase text-[10px] font-semibold tracking-wider">
                  Schema Architecture
                </span>
                <p className="font-semibold text-slate-800 dark:text-slate-200 mt-1">
                  ClaimGuard V{claim.schema_version} Relational Record
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column (1 col): Metadata Summary & Quick Facts */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Claim File Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-xs">
              <div>
                <span className="text-slate-400 uppercase text-[10px] font-semibold tracking-wider">
                  Insurance Category
                </span>
                <p className="font-medium text-slate-900 dark:text-slate-100 text-sm mt-0.5">
                  {claim.claim_type}
                </p>
              </div>

              <div>
                <span className="text-slate-400 uppercase text-[10px] font-semibold tracking-wider">
                  Lifecycle Status
                </span>
                <div className="mt-1">
                  <Badge
                    variant={
                      claim.status === 'OPEN'
                        ? 'warning'
                        : claim.status === 'CLOSED'
                        ? 'success'
                        : 'neutral'
                    }
                  >
                    {claim.status}
                  </Badge>
                </div>
              </div>

              <div>
                <span className="text-slate-400 uppercase text-[10px] font-semibold tracking-wider">
                  Internal Claim #
                </span>
                <p className="font-mono text-slate-900 dark:text-slate-100 text-sm mt-0.5">
                  {claim.claim_number || 'UNASSIGNED'}
                </p>
              </div>

              <div>
                <span className="text-slate-400 uppercase text-[10px] font-semibold tracking-wider">
                  Policy Reference #
                </span>
                <p className="font-mono text-slate-900 dark:text-slate-100 text-sm mt-0.5">
                  {claim.policy_number || 'UNASSIGNED'}
                </p>
              </div>

              <div className="pt-2 border-t border-slate-100 dark:border-navy-800 space-y-2 text-[11px] text-slate-500">
                <div className="flex items-center gap-1.5">
                  <Calendar className="h-3.5 w-3.5" />
                  <span>Created: {new Date(claim.created_at).toLocaleString()}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Clock className="h-3.5 w-3.5" />
                  <span>Last Modified: {new Date(claim.updated_at).toLocaleString()}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Claim-Specific Audit Trail */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-brand-500" />
            <CardTitle>Claim Audit & Evidence Trail</CardTitle>
          </div>
          <CardDescription>
            Immutable event history specifically logged for this claim file.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isAuditLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-10 bg-slate-100 dark:bg-navy-800 animate-pulse rounded-lg" />
              ))}
            </div>
          ) : !auditData?.items || auditData.items.length === 0 ? (
            <div className="py-6 text-center text-slate-400 text-xs">
              No audit events recorded for this claim yet.
            </div>
          ) : (
            <div className="divide-y divide-slate-100 dark:divide-navy-800 text-xs">
              {auditData.items.map((event) => (
                <div key={event.id} className="py-2.5 flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <span className="font-medium text-slate-800 dark:text-slate-200">
                      {event.action.replace(/_/g, ' ')}
                    </span>
                    <Badge variant={event.outcome === 'SUCCESS' ? 'success' : 'danger'} size="sm">
                      {event.outcome}
                    </Badge>
                  </div>
                  <span className="text-[11px] text-slate-400">
                    {new Date(event.timestamp).toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
