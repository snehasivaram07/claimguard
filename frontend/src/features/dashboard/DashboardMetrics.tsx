import React from 'react';
import { Card, CardContent } from '../../components/ui/Card';
import { FileText, FolderOpen, Network, CheckCircle2 } from 'lucide-react';
import { Link } from 'react-router-dom';

interface DashboardMetricsProps {
  totalClaims: number;
  openClaims: number;
  totalFraudRings: number;
  isEngineHealthy: boolean;
  isLoading?: boolean;
}

export const DashboardMetrics: React.FC<DashboardMetricsProps> = ({
  totalClaims,
  openClaims,
  totalFraudRings,
  isEngineHealthy,
  isLoading = false,
}) => {
  const cards = [
    {
      title: 'Total Claims',
      value: totalClaims,
      subtitle: 'Tenant portfolio claims',
      icon: FileText,
      color: 'text-brand-500 bg-brand-500/10',
      link: '/claims',
    },
    {
      title: 'Open Investigations',
      value: openClaims,
      subtitle: 'Active SIU caseload',
      icon: FolderOpen,
      color: 'text-amber-500 bg-amber-500/10',
      link: '/claims',
    },
    {
      title: 'Detected Fraud Rings',
      value: totalFraudRings,
      subtitle: 'Multi-claim collusion clusters',
      icon: Network,
      color: 'text-red-500 bg-red-500/10',
      link: '/fraud-rings',
    },
    {
      title: 'Backend Infrastructure',
      value: isEngineHealthy ? 'Operational' : 'Degraded',
      subtitle: 'Postgres, Graph & S3 ready',
      icon: CheckCircle2,
      color: isEngineHealthy
        ? 'text-emerald-500 bg-emerald-500/10'
        : 'text-red-500 bg-red-500/10',
      link: '/system-health',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <Link key={card.title} to={card.link}>
            <Card className="hover:border-brand-500/40 dark:hover:border-brand-500/40 hover:shadow-md transition-all cursor-pointer h-full">
              <CardContent className="p-5 flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    {card.title}
                  </p>
                  <div className="mt-1 flex items-baseline gap-2">
                    {isLoading ? (
                      <div className="h-7 w-12 bg-slate-200 dark:bg-navy-800 animate-pulse rounded" />
                    ) : (
                      <span className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
                        {card.value}
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-1">
                    {card.subtitle}
                  </p>
                </div>
                <div
                  className={`h-11 w-11 rounded-xl flex items-center justify-center shrink-0 ${card.color}`}
                >
                  <Icon className="h-5 w-5" />
                </div>
              </CardContent>
            </Card>
          </Link>
        );
      })}
    </div>
  );
};
