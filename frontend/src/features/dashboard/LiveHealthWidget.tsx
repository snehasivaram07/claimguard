import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { healthService } from '../../services/health-service';
import { Badge } from '../../components/ui/Badge';
import { RefreshCw, Database, Share2, HardDrive } from 'lucide-react';

export const LiveHealthWidget: React.FC = () => {
  const { data: health, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ['system-readiness'],
    queryFn: () => healthService.getReadiness(),
    refetchInterval: 30000, // Poll every 30s
  });

  const allHealthy = health?.status === 'ready';

  return (
    <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-750 rounded-2xl p-4 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        <div
          className={`h-3.5 w-3.5 rounded-full ${
            isLoading
              ? 'bg-amber-400 animate-pulse'
              : allHealthy
              ? 'bg-emerald-500'
              : 'bg-red-500'
          }`}
        />
        <div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">
              System Health
            </span>
            <Badge variant={allHealthy ? 'success' : isError ? 'danger' : 'warning'} size="sm">
              {isLoading ? 'Probing...' : allHealthy ? 'All Engines Operational' : 'Degraded'}
            </Badge>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            PostgreSQL, FalkorDB Graph & MinIO S3 Object Vault
          </p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-3 text-xs text-slate-600 dark:text-slate-300">
          <span className="flex items-center gap-1.5" title="PostgreSQL 16">
            <Database className="h-3.5 w-3.5 text-blue-500" />
            <span className="capitalize">{health?.services?.postgres || '...'}</span>
          </span>
          <span className="text-slate-300 dark:text-navy-700">|</span>
          <span className="flex items-center gap-1.5" title="FalkorDB Graph">
            <Share2 className="h-3.5 w-3.5 text-purple-500" />
            <span className="capitalize">{health?.services?.falkordb || '...'}</span>
          </span>
          <span className="text-slate-300 dark:text-navy-700">|</span>
          <span className="flex items-center gap-1.5" title="MinIO S3 Storage">
            <HardDrive className="h-3.5 w-3.5 text-emerald-500" />
            <span className="capitalize">{health?.services?.s3 || '...'}</span>
          </span>
        </div>

        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-navy-800 transition-colors disabled:opacity-50"
          title="Refresh health status"
        >
          <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
        </button>
      </div>
    </div>
  );
};
