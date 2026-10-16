import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Shield, AlertCircle, ArrowRight } from 'lucide-react';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { useAuth } from '../context/AuthContext';
import { ThemeToggle } from '../components/layout/ThemeToggle';
import type { ApiError } from '../types';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await login({ email, password });
      navigate(from, { replace: true });
    } catch (err: unknown) {
      const axiosErr = err as {
        response?: {
          status?: number;
          data?: ApiError;
        };
      };

      const errCode = axiosErr.response?.data?.code;
      const errMsg = axiosErr.response?.data?.message;

      if (errCode === 'INVALID_CREDENTIALS' || axiosErr.response?.status === 401) {
        setError('Incorrect email or password. Please verify your credentials.');
      } else if (errCode === 'RATE_LIMIT_EXCEEDED' || axiosErr.response?.status === 429) {
        setError('Too many login attempts. Please wait a minute before retrying.');
      } else if (errMsg) {
        setError(errMsg);
      } else {
        setError('Unable to connect to ClaimGuard backend. Ensure the server is online.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-navy-950 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 transition-colors relative">
      {/* Top right theme toggle */}
      <div className="absolute top-4 right-4 sm:top-6 sm:right-6">
        <ThemeToggle />
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="mx-auto h-14 w-14 rounded-2xl bg-gradient-to-br from-brand-400 to-brand-600 text-white flex items-center justify-center shadow-xl shadow-brand-500/25 mb-4">
          <Shield className="h-7 w-7" />
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">
          ClaimGuard SIU
        </h2>
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
          Multi-Tenant Insurance Fraud Intelligence & Forensics
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white dark:bg-navy-900 py-8 px-6 shadow-xl border border-slate-200 dark:border-navy-750 sm:rounded-2xl sm:px-10 transition-all">
          <form className="space-y-5" onSubmit={handleSubmit}>
            {error && (
              <div className="p-3.5 text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/40 rounded-xl border border-red-200 dark:border-red-900/60 flex items-start gap-2.5 animate-fadeIn">
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                <span className="leading-relaxed">{error}</span>
              </div>
            )}

            <Input
              label="Investigator Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="agent@claimguard.internal"
              required
              autoFocus
            />

            <Input
              label="Password"
              isPassword
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />

            <Button
              type="submit"
              variant="primary"
              size="lg"
              className="w-full mt-2"
              isLoading={loading}
              rightIcon={<ArrowRight className="h-4 w-4" />}
            >
              Sign In to Command Center
            </Button>
          </form>

          <div className="mt-6 pt-5 border-t border-slate-100 dark:border-navy-800 text-center">
            <p className="text-xs text-slate-500 dark:text-slate-400">
              New investigator?{' '}
              <Link
                to="/register"
                className="font-semibold text-brand-600 dark:text-brand-400 hover:underline"
              >
                Create an account
              </Link>
            </p>
          </div>
        </div>

        {/* Security badge footer */}
        <div className="mt-8 text-center text-[11px] text-slate-500 dark:text-slate-500 flex items-center justify-center gap-1.5">
          <Shield className="h-3.5 w-3.5 text-brand-500" />
          <span>Strict Tenant Isolation & AES-256 Audit Grounding</span>
        </div>
      </div>
    </div>
  );
};
