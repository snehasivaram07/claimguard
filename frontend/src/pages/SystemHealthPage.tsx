import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { RefreshCw, Database, Share2, HardDrive } from 'lucide-react';
import { apiClient } from '../lib/api-client';
import type { SystemHealthResponse } from '../types';

export const SystemHealthPage: React.FC = () => {
  const [health, setHealth] = useState<SystemHealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [lastChecked, setLastChecked] = useState<string>('');

  const fetchHealth = async () => {
    setLoading(true);
    try {
      const resp = await apiClient.get<SystemHealthResponse>('/health/ready');
      setHealth(resp.data);
    } catch {
      setHealth({
        status: 'unhealthy',
        services: {
          postgres: 'unhealthy',
          falkordb: 'unhealthy',
          s3: 'unhealthy',
        },
      });
    } finally {
      setLoading(false);
      setLastChecked(new Date().toLocaleTimeString());
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            System Health & Infrastructure
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Live telemetry and readiness probes for core backing engines.
          </p>
        </div>
        <Button
          onClick={fetchHealth}
          isLoading={loading}
          variant="outline"
          leftIcon={<RefreshCw className="h-4 w-4" />}
        >
          Probe Services
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* PostgreSQL */}
        <Card>
          <CardContent className="p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-xl bg-blue-500/10 text-blue-500 flex items-center justify-center">
                <Database className="h-6 w-6" />
              </div>
              <Badge variant={health?.services.postgres === 'healthy' ? 'success' : 'danger'}>
                {health?.services.postgres === 'healthy' ? 'Operational' : 'Unavailable'}
              </Badge>
            </div>
            <div>
              <h4 className="text-base font-semibold text-slate-900 dark:text-slate-100">PostgreSQL 16</h4>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Relational schema, multi-tenant claims, user authentication & audit logging.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* FalkorDB */}
        <Card>
          <CardContent className="p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-xl bg-purple-500/10 text-purple-500 flex items-center justify-center">
                <Share2 className="h-6 w-6" />
              </div>
              <Badge variant={health?.services.falkordb === 'healthy' ? 'success' : 'danger'}>
                {health?.services.falkordb === 'healthy' ? 'Operational' : 'Unavailable'}
              </Badge>
            </div>
            <div>
              <h4 className="text-base font-semibold text-slate-900 dark:text-slate-100">FalkorDB Graph</h4>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                In-memory knowledge graph for multi-claim link analysis & fraud ring discovery.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* MinIO S3 */}
        <Card>
          <CardContent className="p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-xl bg-emerald-500/10 text-emerald-500 flex items-center justify-center">
                <HardDrive className="h-6 w-6" />
              </div>
              <Badge variant={health?.services.s3 === 'healthy' ? 'success' : 'danger'}>
                {health?.services.s3 === 'healthy' ? 'Operational' : 'Unavailable'}
              </Badge>
            </div>
            <div>
              <h4 className="text-base font-semibold text-slate-900 dark:text-slate-100">MinIO S3 Vault</h4>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Encrypted object storage for uploaded claim binaries & presigned download URLs.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Probe Status Summary</CardTitle>
          <CardDescription>
            Last checked at: {lastChecked || 'Checking now...'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-3">
            <div
              className={`h-3 w-3 rounded-full ${
                health?.status === 'ready' ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'
              }`}
            />
            <span className="text-sm font-medium text-slate-700 dark:text-slate-200">
              Overall Status: {health?.status === 'ready' ? 'All Backing Engines Ready' : 'Degraded Service'}
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
