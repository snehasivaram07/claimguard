import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Shield, AlertCircle, CheckCircle2, ArrowRight } from 'lucide-react';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { useAuth } from '../context/AuthContext';
import { ThemeToggle } from '../components/layout/ThemeToggle';
import type { ApiError } from '../types';

export const RegisterPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { register, login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (password !== confirmPassword) {
      setError('Passwords do not match. Please verify.');
      return;
    }

    if (password.length < 8) {
      setError('Password must contain at least 8 characters.');
      return;
    }

    setLoading(true);

    try {
      await register({ email, password });
      setSuccess('Account created successfully! Logging you in...');
      // Automatically log the newly registered user in
      await login({ email, password });
      navigate('/', { replace: true });
    } catch (err: unknown) {
      const axiosErr = err as {
        response?: {
          status?: number;
          data?: ApiError;
        };
      };

      const errCode = axiosErr.response?.data?.code;
      const errMsg = axiosErr.response?.data?.message;

      if (errCode === 'USER_ALREADY_EXISTS' || axiosErr.response?.status === 400) {
        setError(errMsg || 'An account with this email already exists.');
      } else if (errCode === 'RATE_LIMIT_EXCEEDED' || axiosErr.response?.status === 429) {
        setError('Too many registration attempts. Please wait a minute before retrying.');
      } else if (errMsg) {
        setError(errMsg);
      } else {
        setError('Unable to register account. Verify ClaimGuard backend is running.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-navy-950 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 transition-colors relative">
      <div className="absolute top-4 right-4 sm:top-6 sm:right-6">
        <ThemeToggle />
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="mx-auto h-14 w-14 rounded-2xl bg-gradient-to-br from-brand-400 to-brand-600 text-white flex items-center justify-center shadow-xl shadow-brand-500/25 mb-4">
          <Shield className="h-7 w-7" />
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">
          Create Investigator Profile
        </h2>
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
          Start investigating insurance claims with graph intelligence
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white dark:bg-navy-900 py-8 px-6 shadow-xl border border-slate-200 dark:border-navy-750 sm:rounded-2xl sm:px-10 transition-all">
          <form className="space-y-5" onSubmit={handleSubmit}>
            {error && (
              <div className="p-3.5 text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/40 rounded-xl border border-red-200 dark:border-red-900/60 flex items-start gap-2.5">
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                <span className="leading-relaxed">{error}</span>
              </div>
            )}

            {success && (
              <div className="p-3.5 text-xs text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 rounded-xl border border-emerald-200 dark:border-emerald-900/60 flex items-start gap-2.5">
                <CheckCircle2 className="h-4 w-4 shrink-0 mt-0.5" />
                <span className="leading-relaxed">{success}</span>
              </div>
            )}

            <Input
              label="Official Work Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="investigator@company.com"
              required
              autoFocus
            />

            <Input
              label="Password (min 8 characters)"
              isPassword
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />

            <Input
              label="Confirm Password"
              isPassword
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
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
              Complete Registration
            </Button>
          </form>

          <div className="mt-6 pt-5 border-t border-slate-100 dark:border-navy-800 text-center">
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Already have an authorized account?{' '}
              <Link
                to="/login"
                className="font-semibold text-brand-600 dark:text-brand-400 hover:underline"
              >
                Sign in here
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
