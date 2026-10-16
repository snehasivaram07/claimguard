import React from 'react';
import { ShieldAlert, ShieldCheck, AlertTriangle, Info } from 'lucide-react';
import type { ClaimDiscrepancy } from '../../types';

interface RiskScoreMeterProps {
  riskScore: number;
  confidenceScore: number;
  discrepancies: ClaimDiscrepancy[];
}

export const RiskScoreMeter: React.FC<RiskScoreMeterProps> = ({
  riskScore,
  confidenceScore,
  discrepancies,
}) => {
  const percentage = Math.min(100, Math.max(0, Math.round(riskScore * 100)));
  const confidencePct = Math.min(100, Math.max(0, Math.round(confidenceScore * 100)));

  // Risk Classification
  let tierLabel = 'Low Risk';
  let tierColor = 'text-emerald-500 dark:text-emerald-400';
  let ringStrokeColor = '#10b981';
  let badgeBg = 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20';
  let Icon = ShieldCheck;

  if (percentage >= 80) {
    tierLabel = 'Critical Risk';
    tierColor = 'text-rose-600 dark:text-rose-400';
    ringStrokeColor = '#f43f5e';
    badgeBg = 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20';
    Icon = ShieldAlert;
  } else if (percentage >= 60) {
    tierLabel = 'High Risk';
    tierColor = 'text-amber-600 dark:text-amber-400';
    ringStrokeColor = '#f97316';
    badgeBg = 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20';
    Icon = AlertTriangle;
  } else if (percentage >= 30) {
    tierLabel = 'Moderate Risk';
    tierColor = 'text-yellow-600 dark:text-yellow-400';
    ringStrokeColor = '#eab308';
    badgeBg = 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 border-yellow-500/20';
    Icon = AlertTriangle;
  }

  // Count severities
  const counts = {
    critical: discrepancies.filter((d) => d.severity === 'critical').length,
    high: discrepancies.filter((d) => d.severity === 'high').length,
    medium: discrepancies.filter((d) => d.severity === 'medium').length,
    low: discrepancies.filter((d) => d.severity === 'low').length,
  };

  // SVG Gauge calculations (radius = 54, circumference = 2 * PI * 54 = 339.29)
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  // We'll show an open arc of 260 degrees (0.722 of full circle)
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700/80 rounded-xl p-5 shadow-sm space-y-5">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-navy-800">
        <div>
          <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider flex items-center gap-2">
            <Icon className={`h-4 w-4 ${tierColor}`} />
            Fraud Risk Index
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Cross-document inconsistency & entity correlation score
          </p>
        </div>
        <span
          className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border ${badgeBg}`}
        >
          {tierLabel}
        </span>
      </div>

      {/* Main Gauge & Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-12 gap-6 items-center">
        {/* Circular Gauge */}
        <div className="sm:col-span-5 flex flex-col items-center justify-center">
          <div className="relative w-36 h-36 flex items-center justify-center">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 128 128">
              {/* Background Track */}
              <circle
                cx="64"
                cy="64"
                r={radius}
                className="stroke-slate-100 dark:stroke-navy-800"
                strokeWidth="10"
                fill="none"
              />
              {/* Progress Ring */}
              <circle
                cx="64"
                cy="64"
                r={radius}
                stroke={ringStrokeColor}
                strokeWidth="10"
                fill="none"
                strokeLinecap="round"
                style={{
                  strokeDasharray: circumference,
                  strokeDashoffset: strokeDashoffset,
                  transition: 'stroke-dashoffset 1s ease-in-out, stroke 0.5s ease',
                }}
              />
            </svg>
            {/* Center Content */}
            <div className="absolute flex flex-col items-center justify-center text-center">
              <span className={`text-3xl font-extrabold tracking-tight ${tierColor}`}>
                {percentage}%
              </span>
              <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                Risk Score
              </span>
            </div>
          </div>
        </div>

        {/* Breakdown Stats */}
        <div className="sm:col-span-7 space-y-3">
          <div className="flex items-center justify-between text-xs pb-2 border-b border-slate-100 dark:border-navy-800/80">
            <span className="text-slate-600 dark:text-slate-300 font-medium">
              Inference Confidence
            </span>
            <span className="font-bold text-slate-900 dark:text-slate-100">
              {confidencePct}%
            </span>
          </div>

          <div>
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2">
              Detected Inconsistencies ({discrepancies.length})
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="flex items-center justify-between p-2 rounded-lg bg-rose-500/5 dark:bg-rose-500/10 border border-rose-500/20">
                <span className="text-rose-700 dark:text-rose-400 font-medium">Critical</span>
                <span className="font-bold text-rose-700 dark:text-rose-300">{counts.critical}</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded-lg bg-amber-500/5 dark:bg-amber-500/10 border border-amber-500/20">
                <span className="text-amber-700 dark:text-amber-400 font-medium">High</span>
                <span className="font-bold text-amber-700 dark:text-amber-300">{counts.high}</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded-lg bg-yellow-500/5 dark:bg-yellow-500/10 border border-yellow-500/20">
                <span className="text-yellow-700 dark:text-yellow-400 font-medium">Medium</span>
                <span className="font-bold text-yellow-700 dark:text-yellow-300">{counts.medium}</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded-lg bg-slate-100 dark:bg-navy-800 border border-slate-200 dark:border-navy-700">
                <span className="text-slate-700 dark:text-slate-400 font-medium">Low</span>
                <span className="font-bold text-slate-700 dark:text-slate-300">{counts.low}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Human-in-the-Loop Safeguard Notice */}
      <div className="flex items-start gap-2.5 p-3 rounded-lg bg-slate-50 dark:bg-navy-950/60 border border-slate-200 dark:border-navy-800 text-xs text-slate-600 dark:text-slate-400">
        <Info className="h-4 w-4 text-brand-500 shrink-0 mt-0.5" />
        <div className="leading-relaxed">
          <span className="font-semibold text-slate-700 dark:text-slate-200">
            Investigative Leads Only:{' '}
          </span>
          AI-generated scores evaluate textual and entity contradictions across submitted documents to assist certified adjusters. They highlight areas requiring human review and do not constitute legal proof of guilt.
        </div>
      </div>
    </div>
  );
};
