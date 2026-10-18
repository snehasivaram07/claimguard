import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { documentService } from '../../services/document-service';
import { DocumentUploader } from './DocumentUploader';
import { DocumentList } from './DocumentList';
import { ExtractionDrawer } from './ExtractionDrawer';
import type { DocumentItem, DocumentExtraction } from '../../types';

interface DocumentHubTabProps {
  claimId: string;
}

export const DocumentHubTab: React.FC<DocumentHubTabProps> = ({ claimId }) => {
  const queryClient = useQueryClient();

  const [selectedDoc, setSelectedDoc] = useState<DocumentItem | null>(null);
  const [extractionData, setExtractionData] = useState<DocumentExtraction | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [extractingDocId, setExtractingDocId] = useState<string | null>(null);

  // Fetch Documents
  const { data: docListData, isLoading } = useQuery({
    queryKey: ['claim-documents', claimId],
    queryFn: () => documentService.listDocuments(claimId),
  });

  // Extract Mutation
  const extractMutation = useMutation({
    mutationFn: (doc: DocumentItem) => documentService.extractDocument(claimId, doc.id),
    onMutate: (doc) => {
      setExtractingDocId(doc.id);
      setSelectedDoc(doc);
      setIsDrawerOpen(true);
      setExtractionData(null);
    },
    onSuccess: (data) => {
      setExtractionData(data);
      queryClient.invalidateQueries({ queryKey: ['claim-documents', claimId] });
      queryClient.invalidateQueries({ queryKey: ['claim-details', claimId] });
    },
    onError: (err: unknown) => {
      const axiosErr = err as {
        response?: {
          data?: {
            message?: string;
            error?: { message?: string; code?: string };
          };
        };
      };
      const detail =
        axiosErr.response?.data?.error?.message ||
        axiosErr.response?.data?.message ||
        'Extraction failed. Please verify LLM inference configuration.';
      alert(detail);
    },
    onSettled: () => {
      setExtractingDocId(null);
    },
  });

  // Archive Document Mutation
  const archiveMutation = useMutation({
    mutationFn: (doc: DocumentItem) => documentService.deleteDocument(claimId, doc.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['claim-documents', claimId] });
    },
  });

  const handleUploadSuccess = () => {
    queryClient.invalidateQueries({ queryKey: ['claim-documents', claimId] });
  };

  const handleInspect = async (doc: DocumentItem) => {
    setSelectedDoc(doc);
    setIsDrawerOpen(true);
    // If we don't have active extraction in state, trigger fresh extraction or inspect
    extractMutation.mutate(doc);
  };

  const documents = docListData?.items || [];

  return (
    <div className="space-y-6">
      {/* Evidence Uploader */}
      <DocumentUploader
        claimId={claimId}
        onUploadSuccess={handleUploadSuccess}
      />

      {/* Evidence Document List */}
      <DocumentList
        claimId={claimId}
        documents={documents}
        isLoading={isLoading}
        extractingDocId={extractingDocId}
        onExtract={(doc) => extractMutation.mutate(doc)}
        onInspect={handleInspect}
        onArchive={(doc) => {
          if (confirm(`Archive document "${doc.original_filename}"?`)) {
            archiveMutation.mutate(doc);
          }
        }}
      />

      {/* AI Extraction & Grounding Slide-Over Drawer */}
      <ExtractionDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        document={selectedDoc}
        extraction={extractionData}
        isLoading={extractMutation.isPending}
      />
    </div>
  );
};
