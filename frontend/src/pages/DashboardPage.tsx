import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Plus, Shield, Activity, FileText, Network } from 'lucide-react';
import { Link } from 'react-router-dom';

export const DashboardPage: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            SIU Investigation Command Center
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Real-time multi-tenant claims intelligence, fraud network detection, and evidence grounding.
          </p>
        </div>
        <Link to="/claims">
          <Button leftIcon={<Plus className="h-4 w-4" />} variant="primary">
            New Claim
          </Button>
        </Link>
      </div>

      {/* Metrics Row Placeholder */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500 dark:text-slate-400">Total Active Claims</p>
              <h4 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1">12</h4>
            </div>
            <div className="h-10 w-10 rounded-xl bg-brand-500/10 text-brand-500 flex items-center justify-center">
              <FileText className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500 dark:text-slate-400">High-Risk Discrepancies</p>
              <h4 className="text-2xl font-bold text-amber-500 mt-1">3</h4>
            </div>
            <div className="h-10 w-10 rounded-xl bg-amber-500/10 text-amber-500 flex items-center justify-center">
              <Shield className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500 dark:text-slate-400">Collusion Networks</p>
              <h4 className="text-2xl font-bold text-red-500 mt-1">2</h4>
            </div>
            <div className="h-10 w-10 rounded-xl bg-red-500/10 text-red-500 flex items-center justify-center">
              <Network className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500 dark:text-slate-400">System Engines</p>
              <h4 className="text-2xl font-bold text-emerald-500 mt-1">Ready</h4>
            </div>
            <div className="h-10 w-10 rounded-xl bg-emerald-500/10 text-emerald-500 flex items-center justify-center">
              <Activity className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Section */}
      <Card>
        <CardHeader>
          <CardTitle>Welcome to ClaimGuard</CardTitle>
          <CardDescription>
            The project foundation and app shell have been scaffolded for Milestone 1. Select a navigation item from the sidebar or click New Claim to begin.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
            Every backend capability (Claims, Documents, Extraction, Timeline & Contradiction Detection, Graph Fraud Rings, and SIU Dossier generation) is connected through the centralized API client with automatic token refreshing and multi-tenant security.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};
