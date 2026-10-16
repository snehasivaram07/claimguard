import React, { useState } from 'react';
import {
  FileText,
  Download,
  CheckCircle2,
  Database,
} from 'lucide-react';
import { documentService } from '../../services/document-service';
import type { DossierDocumentSummary } from '../../types';

interface EvidenceSummaryTableProps {
  claimId: string;
  documents: DossierDocumentSummary[];
}

export const EvidenceSummaryTable: React.FC<EvidenceSummaryTableProps> = ({
  claimId,
  documents,
}) => {
  const [downloadingDocId, setDownloadingDocId] = useState<string | null>(null);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
  };

  const handleDownloadOriginal = async (docId: string, filename: string) => {
    try {
      setDownloadingDocId(docId);
      const { download_url } = await documentService.getDownloadUrl(claimId, docId);
      const link = document.createElement('a');
      link.href = download_url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch {
      // Ignore presigned error
    } finally {
      setDownloadingDocId(null);
    }
  };

  const totalEntities = documents.reduce((sum, d) => sum + (d.extracted_entities_count || 0), 0);
  const totalDates = documents.reduce((sum, d) => sum + (d.extracted_dates_count || 0), 0);

  return (
    <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700/80 rounded-xl p-5 shadow-sm space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100 dark:border-navy-800">
        <div>
          <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider flex items-center gap-2">
            <Database className="h-4 w-4 text-brand-500" />
            Evidentiary Document Inventory ({documents.length})
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Audit chain-of-custody, extraction metrics, and secure file downloads
          </p>
        </div>

        {/* Extraction Aggregates */}
        <div className="flex items-center gap-3 text-xs">
          <span className="text-slate-500 dark:text-slate-400">
            Entities Grounded: <strong className="text-slate-800 dark:text-slate-200">{totalEntities}</strong>
          </span>
          <span>•</span>
          <span className="text-slate-500 dark:text-slate-400">
            Dates Extracted: <strong className="text-slate-800 dark:text-slate-200">{totalDates}</strong>
          </span>
        </div>
      </div>

      {/* Table */}
      {documents.length === 0 ? (
        <div className="py-8 text-center text-xs text-slate-500">
          No evidentiary records are currently attached to this case file.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-navy-800">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 dark:bg-navy-950/70 border-b border-slate-200 dark:border-navy-800 text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              <tr>
                <th className="py-3 px-3.5">Document Name</th>
                <th className="py-3 px-3">Classification</th>
                <th className="py-3 px-3">Status</th>
                <th className="py-3 px-3">File Size</th>
                <th className="py-3 px-3 text-center">Grounded Entities</th>
                <th className="py-3 px-3 text-center">Dates Extracted</th>
                <th className="py-3 px-3.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-navy-800">
              {documents.map((doc) => {
                const isDownloading = downloadingDocId === doc.document_id;

                return (
                  <tr
                    key={doc.document_id}
                    className="hover:bg-slate-50/60 dark:hover:bg-navy-950/40 transition-colors"
                  >
                    {/* Filename */}
                    <td className="py-3 px-3.5 font-semibold text-slate-900 dark:text-slate-100">
                      <div className="flex items-center gap-2 max-w-[200px] truncate" title={doc.original_filename}>
                        <FileText className="h-4 w-4 text-brand-500 shrink-0" />
                        <span className="truncate">{doc.original_filename}</span>
                      </div>
                    </td>

                    {/* Document Type */}
                    <td className="py-3 px-3">
                      <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-slate-100 dark:bg-navy-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-navy-700">
                        {doc.document_type.replace(/_/g, ' ')}
                      </span>
                    </td>

                    {/* Status */}
                    <td className="py-3 px-3">
                      <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase px-2 py-0.2 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                        <CheckCircle2 className="h-3 w-3" />
                        {doc.status}
                      </span>
                    </td>

                    {/* File Size */}
                    <td className="py-3 px-3 font-mono text-slate-500 dark:text-slate-400">
                      {formatFileSize(doc.size_bytes)}
                    </td>

                    {/* Grounded Entities Count */}
                    <td className="py-3 px-3 text-center">
                      <span className="font-mono font-bold text-slate-800 dark:text-slate-200 bg-slate-100 dark:bg-navy-800 px-2 py-0.5 rounded">
                        {doc.extracted_entities_count}
                      </span>
                    </td>

                    {/* Dates Count */}
                    <td className="py-3 px-3 text-center">
                      <span className="font-mono font-bold text-slate-800 dark:text-slate-200 bg-slate-100 dark:bg-navy-800 px-2 py-0.5 rounded">
                        {doc.extracted_dates_count}
                      </span>
                    </td>

                    {/* Action */}
                    <td className="py-3 px-3.5 text-right">
                      <button
                        onClick={() => handleDownloadOriginal(doc.document_id, doc.original_filename)}
                        disabled={isDownloading}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-semibold text-brand-600 dark:text-brand-400 hover:bg-brand-500/10 transition-colors disabled:opacity-50"
                        title="Download verified original document"
                      >
                        <Download className="h-3 w-3" />
                        <span>{isDownloading ? 'Downloading...' : 'Download'}</span>
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
