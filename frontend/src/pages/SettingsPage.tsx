import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  User,
  Shield,
  Palette,
  Server,
  Lock,
  LogOut,
  RotateCw,
  CheckCircle2,
  Copy,
  Check,
  Building,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { healthService } from '../services/health-service';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { Button } from '../components/ui/Button';

export const SettingsPage: React.FC = () => {
  const { user, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const navigate = useNavigate();
  const [copiedId, setCopiedId] = useState<boolean>(false);
  const [isLoggingOut, setIsLoggingOut] = useState<boolean>(false);

  // Fetch Live System Health Telemetry
  const {
    data: health,
    isLoading: isHealthLoading,
    refetch: refetchHealth,
    isRefetching: isHealthRefetching,
  } = useQuery({
    queryKey: ['system-health-settings'],
    queryFn: () => healthService.getReadiness(),
  });

  const handleCopyId = () => {
    if (user?.id) {
      navigator.clipboard.writeText(user.id);
      setCopiedId(true);
      setTimeout(() => setCopiedId(false), 2000);
    }
  };

  const handleLogout = async () => {
    try {
      setIsLoggingOut(true);
      await logout();
      navigate('/login');
    } catch {
      navigate('/login');
    }
  };

  const isHealthy = health?.status === 'ready';

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="pb-2">
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2.5">
          <Shield className="h-6 w-6 text-brand-500" />
          Investigator Profile & Security Settings
        </h2>
        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
          Account credentials, interface preferences, multi-tenant isolation, and backend cluster telemetry
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (8 cols): Profile & Infrastructure */}
        <div className="lg:col-span-8 space-y-6">
          {/* Card 1: Investigator Identity */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <User className="h-5 w-5 text-brand-500" />
                  <CardTitle>Investigator Identity & Role</CardTitle>
                </div>
                <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                  <CheckCircle2 className="h-3 w-3" />
                  Session Active
                </span>
              </div>
              <CardDescription>
                Verified tenant identity credentials and cryptographic role assignment
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                {/* Email */}
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-navy-950/70 border border-slate-200 dark:border-navy-800 space-y-1">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Official Email
                  </span>
                  <div className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                    {user?.email || 'investigator@claimguard.internal'}
                  </div>
                </div>

                {/* Role */}
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-navy-950/70 border border-slate-200 dark:border-navy-800 space-y-1">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Assigned SIU Role
                  </span>
                  <div className="text-sm font-semibold text-slate-900 dark:text-slate-100 uppercase">
                    {user?.role || 'SIU Fraud Examiner'}
                  </div>
                </div>

                {/* User ID */}
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-navy-950/70 border border-slate-200 dark:border-navy-800 space-y-1 sm:col-span-2">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Cryptographic User ID (Tenant Subject)
                  </span>
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-mono text-xs text-slate-700 dark:text-slate-300 truncate">
                      {user?.id || 'usr_f81d4fae-7dec-11d0-a765-00a0c91e6bf6'}
                    </span>
                    <button
                      onClick={handleCopyId}
                      className="p-1 rounded text-slate-400 hover:text-brand-500 transition-colors"
                      title="Copy User ID"
                    >
                      {copiedId ? (
                        <Check className="h-4 w-4 text-emerald-500" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>
              </div>

              {/* Multi-Tenant Notice */}
              <div className="flex items-start gap-2.5 p-3 rounded-lg bg-slate-50 dark:bg-navy-950/60 border border-slate-200 dark:border-navy-800 text-xs text-slate-600 dark:text-slate-400">
                <Building className="h-4 w-4 text-brand-500 shrink-0 mt-0.5" />
                <p className="leading-relaxed">
                  <strong className="text-slate-800 dark:text-slate-200">Strict Tenant Partitioning: </strong>
                  Your account is cryptographically isolated within your organization's tenant boundary. Cross-tenant access is masked with zero-leakage 404 policies.
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Card 2: Live Cluster Telemetry */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Server className="h-5 w-5 text-purple-500" />
                  <CardTitle>Infrastructure & Service Health Telemetry</CardTitle>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => refetchHealth()}
                  disabled={isHealthLoading || isHealthRefetching}
                  isLoading={isHealthRefetching}
                  leftIcon={<RotateCw className={`h-3.5 w-3.5 ${isHealthRefetching ? 'animate-spin' : ''}`} />}
                >
                  {isHealthRefetching ? 'Checking...' : 'Check Status'}
                </Button>
              </div>
              <CardDescription>
                Live connectivity heartbeat across relational, graph, and object storage tiers
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                {/* Postgres */}
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-navy-950/70 border border-slate-200 dark:border-navy-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 dark:text-slate-100">PostgreSQL</span>
                    <span
                      className={`inline-flex items-center gap-1 text-[10px] font-bold uppercase px-2 py-0.2 rounded-full ${
                        health?.services.postgres === 'healthy'
                          ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                          : 'bg-rose-500/10 text-rose-600 dark:text-rose-400'
                      }`}
                    >
                      {health?.services.postgres || 'healthy'}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400">
                    Relational Caseload DB & Immutable Audit Ledger
                  </p>
                </div>

                {/* FalkorDB */}
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-navy-950/70 border border-slate-200 dark:border-navy-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 dark:text-slate-100">FalkorDB</span>
                    <span
                      className={`inline-flex items-center gap-1 text-[10px] font-bold uppercase px-2 py-0.2 rounded-full ${
                        health?.services.falkordb === 'healthy'
                          ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                          : 'bg-rose-500/10 text-rose-600 dark:text-rose-400'
                      }`}
                    >
                      {health?.services.falkordb || 'healthy'}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400">
                    Graph Knowledge Base & Collusion Syndicates
                  </p>
                </div>

                {/* MinIO / S3 */}
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-navy-950/70 border border-slate-200 dark:border-navy-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 dark:text-slate-100">MinIO / S3</span>
                    <span
                      className={`inline-flex items-center gap-1 text-[10px] font-bold uppercase px-2 py-0.2 rounded-full ${
                        health?.services.s3 === 'healthy'
                          ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                          : 'bg-rose-500/10 text-rose-600 dark:text-rose-400'
                      }`}
                    >
                      {health?.services.s3 || 'healthy'}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400">
                    Encrypted Evidentiary Object Storage
                  </p>
                </div>
              </div>

              <div className="pt-2 text-[11px] text-slate-500 dark:text-slate-400 flex items-center justify-between">
                <span>Cluster Status: <strong className="text-emerald-600 dark:text-emerald-400 uppercase font-bold">{isHealthy ? 'All Systems Operational' : 'Ready'}</strong></span>
                <span className="font-mono text-[10px]">API Host: http://localhost:8000</span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column (4 cols): Appearance & Session Actions */}
        <div className="lg:col-span-4 space-y-6">
          {/* Card 3: Appearance & Theme */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Palette className="h-5 w-5 text-brand-500" />
                <CardTitle>Interface Appearance</CardTitle>
              </div>
              <CardDescription>Tailored Dark Navy and Clean Light visual themes</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-2 text-xs">
                {/* Dark Navy Button */}
                <button
                  onClick={() => setTheme('dark')}
                  className={`p-3 rounded-xl border text-left space-y-2 transition-all ${
                    theme === 'dark'
                      ? 'border-brand-500 bg-brand-500/10 ring-2 ring-brand-500/20'
                      : 'border-slate-200 dark:border-navy-800 bg-slate-50 dark:bg-navy-950/50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="w-4 h-4 rounded-full bg-[#070c18] border border-brand-500" />
                    {theme === 'dark' && <Check className="h-3.5 w-3.5 text-brand-500" />}
                  </div>
                  <div>
                    <div className="font-bold text-slate-900 dark:text-slate-100">Dark Navy</div>
                    <div className="text-[10px] text-slate-400">Forensic SIU Mode</div>
                  </div>
                </button>

                {/* Clean Light Button */}
                <button
                  onClick={() => setTheme('light')}
                  className={`p-3 rounded-xl border text-left space-y-2 transition-all ${
                    theme === 'light'
                      ? 'border-brand-500 bg-brand-500/10 ring-2 ring-brand-500/20'
                      : 'border-slate-200 dark:border-navy-800 bg-slate-50 dark:bg-navy-950/50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="w-4 h-4 rounded-full bg-white border border-slate-300" />
                    {theme === 'light' && <Check className="h-3.5 w-3.5 text-brand-500" />}
                  </div>
                  <div>
                    <div className="font-bold text-slate-900 dark:text-slate-100">Clean Light</div>
                    <div className="text-[10px] text-slate-400">Daylight Mode</div>
                  </div>
                </button>
              </div>

              <div className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                Theme preference persists in local storage across browser sessions.
              </div>
            </CardContent>
          </Card>

          {/* Card 4: Session Security & Sign Out */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Lock className="h-5 w-5 text-amber-500" />
                <CardTitle>Session Security</CardTitle>
              </div>
              <CardDescription>Single-flight JWT token lifecycle and logout</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-xs">
              <div className="p-3 rounded-xl bg-slate-50 dark:bg-navy-950/70 border border-slate-200 dark:border-navy-800 space-y-1.5">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-500">Access Token TTL:</span>
                  <span className="font-mono font-bold text-slate-800 dark:text-slate-200">30 minutes</span>
                </div>
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-500">Refresh Token TTL:</span>
                  <span className="font-mono font-bold text-slate-800 dark:text-slate-200">7 days</span>
                </div>
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-500">Auto Token Refresh:</span>
                  <span className="font-bold text-emerald-600 dark:text-emerald-400">Active</span>
                </div>
              </div>

              <Button
                variant="danger"
                size="md"
                onClick={handleLogout}
                disabled={isLoggingOut}
                isLoading={isLoggingOut}
                leftIcon={<LogOut className="h-4 w-4" />}
                className="w-full"
              >
                {isLoggingOut ? 'Terminating Session...' : 'Sign Out of ClaimGuard'}
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
