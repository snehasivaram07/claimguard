import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { ArrowRight, ShieldAlert, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { FraudRingAnalysis, Claim } from '../../types';

interface PriorityActionCenterProps {
  fraudRings: FraudRingAnalysis[];
  openClaims: Claim[];
  isLoading?: boolean;
}

export const PriorityActionCenter: React.FC<PriorityActionCenterProps> = ({
  fraudRings,
  openClaims,
  isLoading = false,
}) => {
  // Synthesize prioritized investigative tasks from real backend evidence
  const actionableItems = [
    ...fraudRings.slice(0, 2).map((ring) => ({
      id: ring.ring_id,
      title: `Potential Collusion: ${ring.title}`,
      targetId: ring.claim_ids[0] || ring.ring_id,
      targetType: 'ring' as const,
      severity: ring.severity,
      description: ring.summary,
      link: '/fraud-rings',
      actionLabel: 'Inspect Network',
    })),
    ...openClaims.slice(0, 2).map((claim) => ({
      id: claim.id,
      title: `Active Investigation: ${claim.title}`,
      targetId: claim.id,
      targetType: 'claim' as const,
      severity: 'medium' as const,
      description: claim.description || 'Claim is currently open and awaiting evidence analysis.',
      link: `/claims/${claim.id}`,
      actionLabel: 'Open Workspace',
    })),
  ];

  return (
    <Card className="h-full">
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <div>
          <div className="flex items-center gap-2">
            <ShieldAlert className="h-4 w-4 text-amber-500" />
            <CardTitle>Priority Action Center</CardTitle>
          </div>
          <CardDescription>
            High-priority investigative leads and unreviewed collusion alerts.
          </CardDescription>
        </div>
        <Badge variant="warning" size="sm">
          {actionableItems.length} Leads
        </Badge>
      </CardHeader>

      <CardContent className="space-y-3">
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2].map((i) => (
              <div
                key={i}
                className="p-4 rounded-xl border border-slate-200 dark:border-navy-800 bg-slate-50 dark:bg-navy-850 animate-pulse h-20"
              />
            ))}
          </div>
        ) : actionableItems.length === 0 ? (
          <div className="py-8 text-center text-slate-500 dark:text-slate-400">
            <Sparkles className="h-8 w-8 text-emerald-500 mx-auto mb-2 opacity-80" />
            <p className="text-sm font-medium">All Caseload Clean</p>
            <p className="text-xs text-slate-400 mt-0.5">
              No critical fraud rings or unresolved discrepancies requiring immediate triage.
            </p>
          </div>
        ) : (
          actionableItems.map((item) => (
            <div
              key={item.id}
              className="p-3.5 rounded-xl border border-slate-200 dark:border-navy-800 bg-slate-50/70 dark:bg-navy-850/60 hover:border-slate-300 dark:hover:border-navy-700 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3"
            >
              <div className="space-y-1 min-w-0">
                <div className="flex items-center gap-2">
                  <Badge
                    variant={
                      item.severity === 'critical'
                        ? 'danger'
                        : item.severity === 'high'
                        ? 'danger'
                        : 'warning'
                    }
                    size="sm"
                  >
                    {item.severity.toUpperCase()}
                  </Badge>
                  <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100 truncate">
                    {item.title}
                  </h4>
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-1">
                  {item.description}
                </p>
              </div>

              <Link to={item.link} className="shrink-0 self-end sm:self-center">
                <Button
                  size="sm"
                  variant="outline"
                  rightIcon={<ArrowRight className="h-3.5 w-3.5" />}
                >
                  {item.actionLabel}
                </Button>
              </Link>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
};
