import React, { useState } from 'react';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { EmptyState } from '../../components/ui/EmptyState';
import {
  FileText,
  Download,
  Sparkles,
  Search,
  Trash2,
} from 'lucide-react';
import { documentService } from '../../services/document-service';
import type { DocumentItem } from '../../types';

interface DocumentListProps {
  claimId: string;
  documents: DocumentItem[];
  isLoading?: boolean;
  extractingDocId?: string | null;
  onExtract: (doc: DocumentItem) => void;
  onInspect: (doc: DocumentItem) => void;
  onArchive: (doc: DocumentItem) => void;
}

export const DocumentList: React.FC<DocumentListProps> = ({
  claimId,
  documents,
  isLoading = false,
  extractingDocId,
  onExtract,
  onInspect,
  onArchive,
}) => {
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const handleDownload = async (doc: DocumentItem) => {
    setDownloadingId(doc.id);
    try {
      const resp = await documentService.getDownloadUrl(claimId, doc.id);
      // Trigger temporary on-demand download
      const link = document.createElement('a');
      link.href = resp.download_url;
      link.download = doc.original_filename;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch {
      alert('Unable to generate presigned download URL. Please check S3 storage readiness.');
    } finally {
      setDownloadingId(null);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(2)} MB`;
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'STORED':
        return <Badge variant="info" size="sm">Stored in Vault</Badge>;
      case 'COMPLETED':
        return <Badge variant="success" size="sm">AI Extracted</Badge>;
      case 'EXTRACTING':
        return <Badge variant="warning" size="sm">Extracting...</Badge>;
      case 'ARCHIVED':
        return <Badge variant="neutral" size="sm">Archived</Badge>;
      default:
        return <Badge variant="neutral" size="sm">{status}</Badge>;
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-750 rounded-2xl p-6 shadow-sm space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-16 bg-slate-100 dark:bg-navy-800 animate-pulse rounded-xl" />
        ))}
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-750 rounded-2xl p-6 shadow-sm">
        <EmptyState
          icon={<FileText className="h-7 w-7" />}
          title="No Evidentiary Documents Attached"
          description="Use the uploader above to attach police reports, accident photos, medical bills, or repair estimates."
        />
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-750 rounded-2xl shadow-sm overflow-hidden flex flex-col">
      <div className="p-4 sm:p-5 border-b border-slate-100 dark:border-navy-800 flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100">
            Attached Evidence ({documents.length})
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Encrypted object storage repository with SHA-256 integrity hashing.
          </p>
        </div>
      </div>

      <div className="divide-y divide-slate-100 dark:divide-navy-800/80">
        {documents.map((doc) => {
          const isExtracting = extractingDocId === doc.id;
          const isDownloading = downloadingId === doc.id;

          return (
            <div
              key={doc.id}
              className="p-4 sm:p-5 hover:bg-slate-50/70 dark:hover:bg-navy-850/40 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              {/* Document Info */}
              <div className="flex items-start gap-3.5 min-w-0">
                <div className="h-10 w-10 min-w-10 rounded-xl bg-brand-50 dark:bg-brand-950/60 border border-brand-200 dark:border-brand-800/60 flex items-center justify-center text-brand-600 dark:text-brand-400 shrink-0 mt-0.5">
                  <FileText className="h-5 w-5" />
                </div>

                <div className="space-y-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm font-semibold text-slate-900 dark:text-slate-100 truncate max-w-xs sm:max-w-md">
                      {doc.original_filename}
                    </span>
                    {getStatusBadge(doc.status)}
                    <Badge variant="neutral" size="sm" className="font-mono text-[10px] uppercase">
                      {doc.document_type.replace(/_/g, ' ')}
                    </Badge>
                  </div>

                  <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-400 font-mono">
                    <span>{formatFileSize(doc.size_bytes)}</span>
                    <span>•</span>
                    <span className="truncate max-w-[150px]">SHA-256: {doc.content_hash.slice(0, 12)}...</span>
                    <span>•</span>
                    <span>Uploaded: {new Date(doc.uploaded_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center justify-end gap-2 shrink-0">
                {/* Secure Presigned Download */}
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleDownload(doc)}
                  isLoading={isDownloading}
                  leftIcon={<Download className="h-3.5 w-3.5" />}
                  title="Generate temporary presigned download URL"
                >
                  Download
                </Button>

                {/* Inspect Extracted Facts */}
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onInspect(doc)}
                  leftIcon={<Search className="h-3.5 w-3.5" />}
                >
                  Inspect Facts
                </Button>

                {/* AI Entity Extraction Trigger */}
                <Button
                  size="sm"
                  variant="primary"
                  onClick={() => onExtract(doc)}
                  isLoading={isExtracting}
                  leftIcon={<Sparkles className="h-3.5 w-3.5" />}
                >
                  Run Extraction
                </Button>

                {/* Soft Delete */}
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => onArchive(doc)}
                  className="text-slate-400 hover:text-red-500 dark:hover:text-red-400 p-2"
                  title="Archive Document"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
