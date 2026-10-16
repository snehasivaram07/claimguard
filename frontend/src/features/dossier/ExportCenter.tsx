import React, { useState } from 'react';
import {
  Download,
  FileCode,
  FileText,
  FileJson,
  Printer,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import { dossierService } from '../../services/dossier-service';
import type { DossierExportFormat } from '../../types';

interface ExportCenterProps {
  claimId: string;
}

export const ExportCenter: React.FC<ExportCenterProps> = ({ claimId }) => {
  const [downloadingFormat, setDownloadingFormat] = useState<DossierExportFormat | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [lastDownloaded, setLastDownloaded] = useState<DossierExportFormat | null>(null);

  const handleDownload = async (format: DossierExportFormat) => {
    try {
      setDownloadingFormat(format);
      setDownloadError(null);
      await dossierService.downloadDossier(claimId, format);
      setLastDownloaded(format);
      setTimeout(() => setLastDownloaded(null), 3500);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to export dossier. Please try again.';
      setDownloadError(msg);
    } finally {
      setDownloadingFormat(null);
    }
  };

  return (
    <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700/80 rounded-xl p-5 shadow-sm space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100 dark:border-navy-800">
        <div>
          <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider flex items-center gap-2">
            <Download className="h-4 w-4 text-brand-500" />
            Forensic Dossier Multi-Format Export Center
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Download print-ready court evidence packets, structured case briefs, and raw forensic data
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-400">
          <Printer className="h-3.5 w-3.5" />
          <span>Court & Subrogation Ready</span>
        </div>
      </div>

      {downloadError && (
        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-xs text-rose-600 dark:text-rose-400 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{downloadError}</span>
          </div>
          <button onClick={() => setDownloadError(null)} className="underline font-bold ml-2">
            Dismiss
          </button>
        </div>
      )}

      {/* Export Options Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {/* 1. Print-Ready HTML */}
        <div className="p-4 rounded-xl border border-slate-200 dark:border-navy-800 bg-slate-50/60 dark:bg-navy-950/60 hover:bg-slate-50 dark:hover:bg-navy-950 transition-all space-y-3 flex flex-col justify-between group">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="p-2 rounded-lg bg-brand-500/10 text-brand-500 border border-brand-500/20">
                <FileCode className="h-5 w-5" />
              </div>
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-brand-500/10 text-brand-500">
                .HTML
              </span>
            </div>

            <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100">
              Print-Ready HTML Report
            </h4>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
              Standalone, self-contained report styled for browser printing (Ctrl+P to PDF), legal counsel binders, and SIU case files.
            </p>
          </div>

          <button
            onClick={() => handleDownload('html')}
            disabled={downloadingFormat !== null}
            className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-semibold bg-brand-500 hover:bg-brand-600 text-white transition-colors disabled:opacity-60 shadow-xs"
          >
            {downloadingFormat === 'html' ? (
              <span className="animate-pulse">Generating HTML...</span>
            ) : lastDownloaded === 'html' ? (
              <>
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>Downloaded!</span>
              </>
            ) : (
              <>
                <Download className="h-3.5 w-3.5" />
                <span>Download HTML (.html)</span>
              </>
            )}
          </button>
        </div>

        {/* 2. Structured Markdown */}
        <div className="p-4 rounded-xl border border-slate-200 dark:border-navy-800 bg-slate-50/60 dark:bg-navy-950/60 hover:bg-slate-50 dark:hover:bg-navy-950 transition-all space-y-3 flex flex-col justify-between group">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
                <FileText className="h-5 w-5" />
              </div>
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-500">
                .MD
              </span>
            </div>

            <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100">
              Standard Markdown Dossier
            </h4>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
              Full forensic case text formatted with Markdown tables, cited verbatim statements, and checklist markers for investigator notes.
            </p>
          </div>

          <button
            onClick={() => handleDownload('markdown')}
            disabled={downloadingFormat !== null}
            className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-900 text-white dark:bg-navy-800 dark:hover:bg-navy-700 transition-colors disabled:opacity-60 shadow-xs"
          >
            {downloadingFormat === 'markdown' ? (
              <span className="animate-pulse">Generating MD...</span>
            ) : lastDownloaded === 'markdown' ? (
              <>
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>Downloaded!</span>
              </>
            ) : (
              <>
                <Download className="h-3.5 w-3.5" />
                <span>Download Markdown (.md)</span>
              </>
            )}
          </button>
        </div>

        {/* 3. Forensic JSON */}
        <div className="p-4 rounded-xl border border-slate-200 dark:border-navy-800 bg-slate-50/60 dark:bg-navy-950/60 hover:bg-slate-50 dark:hover:bg-navy-950 transition-all space-y-3 flex flex-col justify-between group">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="p-2 rounded-lg bg-purple-500/10 text-purple-500 border border-purple-500/20">
                <FileJson className="h-5 w-5" />
              </div>
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-purple-500/10 text-purple-500">
                .JSON
              </span>
            </div>

            <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100">
              Raw Forensic JSON Payload
            </h4>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
              Complete machine-readable schema for automated SIU case management systems, regulatory audit compliance, or data lake ingestion.
            </p>
          </div>

          <button
            onClick={() => handleDownload('json')}
            disabled={downloadingFormat !== null}
            className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-semibold bg-purple-600 hover:bg-purple-700 text-white transition-colors disabled:opacity-60 shadow-xs"
          >
            {downloadingFormat === 'json' ? (
              <span className="animate-pulse">Generating JSON...</span>
            ) : lastDownloaded === 'json' ? (
              <>
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>Downloaded!</span>
              </>
            ) : (
              <>
                <Download className="h-3.5 w-3.5" />
                <span>Download Forensic JSON</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
