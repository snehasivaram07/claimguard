import React, { useState, useRef } from 'react';
import { UploadCloud, File, AlertCircle, CheckCircle2 } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { documentService } from '../../services/document-service';
import type { DocumentItem } from '../../types';

interface DocumentUploaderProps {
  claimId: string;
  onUploadSuccess: (doc: DocumentItem) => void;
}

const MAX_FILE_SIZE_BYTES = 26214400; // 25 MB exactly per backend config
const ALLOWED_EXTENSIONS = ['.pdf', '.png', '.jpg', '.jpeg', '.txt', '.eml'];

export const DocumentUploader: React.FC<DocumentUploaderProps> = ({
  claimId,
  onUploadSuccess,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [documentType, setDocumentType] = useState('GENERAL_ATTACHMENT');
  const [allowDuplicate, setAllowDuplicate] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): string | null => {
    if (file.size > MAX_FILE_SIZE_BYTES) {
      return `File size (${(file.size / (1024 * 1024)).toFixed(2)} MB) exceeds the 25 MB limit.`;
    }
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      return `Unsupported file format (${ext}). Supported formats: PDF, PNG, JPG, TXT, EML.`;
    }
    return null;
  };

  const handleFiles = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const file = files[0];
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      setSelectedFile(null);
      return;
    }
    setError(null);
    setSuccess(null);
    setSelectedFile(file);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    handleFiles(e.dataTransfer.files);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setError(null);
    setSuccess(null);
    setUploadProgress(0);

    try {
      const doc = await documentService.uploadDocument(
        claimId,
        selectedFile,
        documentType,
        allowDuplicate,
        (percent) => setUploadProgress(percent)
      );
      setSuccess(`Successfully uploaded and verified "${doc.original_filename}"`);
      setSelectedFile(null);
      setUploadProgress(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      onUploadSuccess(doc);
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { message?: string; code?: string } } };
      const errCode = axiosErr.response?.data?.code;
      const errMsg = axiosErr.response?.data?.message;

      if (errCode === 'DUPLICATE_FILE') {
        setError(
          'A document with this identical SHA-256 hash already exists on this claim. Enable "Allow duplicate hash" to override.'
        );
      } else {
        setError(errMsg || 'Failed to upload document to secure storage vault.');
      }
      setUploadProgress(null);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-750 rounded-2xl p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100">
            Upload Evidentiary Evidence
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Attach police reports, medical records, repair estimates, or accident photos (Max 25 MB).
          </p>
        </div>
      </div>

      {error && (
        <div className="p-3 text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/40 rounded-xl border border-red-200 dark:border-red-900/60 flex items-start gap-2">
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="p-3 text-xs text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 rounded-xl border border-emerald-200 dark:border-emerald-900/60 flex items-start gap-2">
          <CheckCircle2 className="h-4 w-4 shrink-0 mt-0.5" />
          <span>{success}</span>
        </div>
      )}

      {/* Drag & Drop Surface */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-2xl p-6 sm:p-8 text-center cursor-pointer transition-all flex flex-col items-center justify-center gap-2 ${
          dragActive
            ? 'border-brand-500 bg-brand-50/50 dark:bg-brand-950/20 scale-[0.99]'
            : 'border-slate-300 dark:border-navy-750 hover:border-slate-400 dark:hover:border-navy-600 bg-slate-50/50 dark:bg-navy-950/30'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".pdf,.png,.jpg,.jpeg,.txt,.eml"
          onChange={(e) => handleFiles(e.target.files)}
        />

        <div className="h-12 w-12 rounded-2xl bg-brand-50 dark:bg-brand-950/60 border border-brand-200 dark:border-brand-800/60 flex items-center justify-center text-brand-600 dark:text-brand-400 shadow-sm">
          <UploadCloud className="h-6 w-6" />
        </div>

        <div>
          <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">
            Click to upload or drag and drop
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            PDF, PNG, JPG, TXT, or EML (Strict 25 MB limit)
          </p>
        </div>
      </div>

      {/* Selected File & Metadata Form */}
      {selectedFile && (
        <div className="p-4 rounded-xl border border-slate-200 dark:border-navy-750 bg-slate-50/80 dark:bg-navy-850 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 truncate">
              <File className="h-5 w-5 text-brand-500 shrink-0" />
              <div className="truncate">
                <p className="text-xs font-semibold text-slate-900 dark:text-slate-100 truncate">
                  {selectedFile.name}
                </p>
                <p className="text-[11px] text-slate-400">
                  {(selectedFile.size / 1024).toFixed(1)} KB • {selectedFile.type || 'Binary'}
                </p>
              </div>
            </div>

            <Button
              size="sm"
              variant="ghost"
              onClick={() => setSelectedFile(null)}
              disabled={isUploading}
            >
              Remove
            </Button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-slate-200 dark:border-navy-750">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1">
                Document Classification Tag
              </label>
              <select
                value={documentType}
                onChange={(e) => setDocumentType(e.target.value)}
                className="block w-full rounded-lg border border-slate-300 dark:border-navy-750 bg-white dark:bg-navy-900 text-slate-900 dark:text-slate-100 py-2 px-3 text-xs focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                <option value="GENERAL_ATTACHMENT">General Attachment</option>
                <option value="POLICE_REPORT">Police Incident Report</option>
                <option value="MEDICAL_RECORD">Medical Record / Billing</option>
                <option value="REPAIR_ESTIMATE">Repair / Bodily Estimate</option>
                <option value="PROOF_OF_LOSS">Proof of Loss Statement</option>
                <option value="CORRESPONDENCE">Insurer / Claimant Correspondence</option>
              </select>
            </div>

            <div className="flex items-center pt-5">
              <label className="flex items-center gap-2 text-xs text-slate-700 dark:text-slate-300 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={allowDuplicate}
                  onChange={(e) => setAllowDuplicate(e.target.checked)}
                  className="rounded border-slate-300 text-brand-500 focus:ring-brand-500"
                />
                <span>Allow duplicate file upload (override hash check)</span>
              </label>
            </div>
          </div>

          {/* Progress Bar */}
          {uploadProgress !== null && (
            <div className="space-y-1.5 pt-1">
              <div className="flex justify-between text-xs text-slate-500">
                <span>Uploading to S3 vault...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-slate-200 dark:bg-navy-800 rounded-full h-1.5 overflow-hidden">
                <div
                  className="bg-brand-500 h-1.5 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          <div className="flex justify-end pt-2">
            <Button
              variant="primary"
              size="md"
              onClick={handleUpload}
              isLoading={isUploading}
            >
              Upload to Secure Vault
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
