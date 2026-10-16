import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { ThemeToggle } from '../components/layout/ThemeToggle';

export const SettingsPage: React.FC = () => {
  const { user } = useAuth();
  const { theme } = useTheme();

  return (
    <div className="space-y-6">
      <div className="pb-2">
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          User & Investigation Settings
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Account profile details and interface preferences.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Profile Card */}
        <Card>
          <CardHeader>
            <CardTitle>Investigator Profile</CardTitle>
            <CardDescription>Verified authentication state from ClaimGuard backend</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">Email Address</p>
              <p className="text-sm font-medium text-slate-900 dark:text-slate-100 mt-0.5">
                {user?.email || 'Not logged in (Demo Mode)'}
              </p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">Assigned Role</p>
              <p className="text-sm font-medium text-slate-900 dark:text-slate-100 mt-0.5">
                {user?.role || 'SIU Agent'}
              </p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">User ID</p>
              <p className="text-xs font-mono text-slate-600 dark:text-slate-400 mt-0.5">
                {user?.id || 'guest-session'}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Theme Preferences */}
        <Card>
          <CardHeader>
            <CardTitle>Appearance & Theme</CardTitle>
            <CardDescription>Toggle between Dark Navy and Clean Light mode</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-900 dark:text-slate-100">Theme Mode</p>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Currently active: <span className="font-semibold capitalize text-brand-500">{theme}</span>
                </p>
              </div>
              <ThemeToggle />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
