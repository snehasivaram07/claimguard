import React, { useEffect } from 'react';
import { X, Sparkles, FileText } from 'lucide-react';
import { GroundedFactViewer } from './GroundedFactViewer';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import type { DocumentItem, DocumentExtraction } from '../../types';

interface ExtractionDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  document: DocumentItem | null;
  extraction: DocumentExtraction | null;
  isLoading: boolean;
}

export const ExtractionDrawer: React.FC<ExtractionDrawerProps> = ({
  isOpen,
  onClose,
  document,
  extraction,
  isLoading,
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) onClose();
    };
    if (isOpen) {
      window.document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      window.document.body.style.overflow = 'unset';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-900/60 dark:bg-navy-950/80 backdrop-blur-sm transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-xl bg-white dark:bg-navy-900 border-l border-slate-200 dark:border-navy-750 shadow-2xl flex flex-col">
          {/* Drawer Header */}
          <div className="p-6 border-b border-slate-100 dark:border-navy-800 flex items-start justify-between">
            <div className="space-y-1 pr-6 min-w-0">
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-brand-500 shrink-0" />
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 truncate">
                  AI Entity Extraction & Grounding
                </h3>
              </div>
              <p className="text-xs text-slate-500 truncate">
                File: {document?.original_filename || 'Evidence File'}
              </p>
            </div>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-navy-800 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Drawer Body */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {isLoading ? (
              <div className="py-20 flex flex-col items-center justify-center">
                <LoadingSpinner size="lg" label="Extracting entities & validating groundings..." />
              </div>
            ) : extraction ? (
              <GroundedFactViewer extraction={extraction} />
            ) : (
              <div className="py-16 text-center text-slate-400">
                <FileText className="h-10 w-10 mx-auto mb-2 opacity-50" />
                <p className="text-sm font-medium">No extraction data available.</p>
                <p className="text-xs text-slate-500 mt-1">
                  Click "Run AI Extraction" on the document to analyze text and ground facts.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
