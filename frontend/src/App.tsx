import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider } from './context/AuthContext';
import { AppShell } from './components/layout/AppShell';
import { AuthGuard } from './components/auth/AuthGuard';
import { GuestGuard } from './components/auth/GuestGuard';

import { DashboardPage } from './pages/DashboardPage';
import { ClaimsDirectoryPage } from './pages/ClaimsDirectoryPage';
import { ClaimWorkspacePage } from './pages/ClaimWorkspacePage';
import { GlobalFraudRingsPage } from './pages/GlobalFraudRingsPage';
import { SystemHealthPage } from './pages/SystemHealthPage';
import { AuditActivityPage } from './pages/AuditActivityPage';
import { SettingsPage } from './pages/SettingsPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30000,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <BrowserRouter>
            <Routes>
              {/* Guest only routes (Login & Registration) */}
              <Route element={<GuestGuard />}>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />
              </Route>

              {/* Authenticated routes protected by AuthGuard */}
              <Route element={<AuthGuard />}>
                <Route element={<AppShell />}>
                  <Route path="/" element={<DashboardPage />} />
                  <Route path="/claims" element={<ClaimsDirectoryPage />} />
                  <Route path="/claims/:claimId" element={<ClaimWorkspacePage />} />
                  <Route path="/fraud-rings" element={<GlobalFraudRingsPage />} />
                  <Route path="/system-health" element={<SystemHealthPage />} />
                  <Route path="/audit" element={<AuditActivityPage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                </Route>
              </Route>

              {/* Fallback redirect */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

export default App;
