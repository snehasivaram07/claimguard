import { apiClient } from '../lib/api-client';
import type {
  DocumentItem,
  DocumentListResponse,
  PresignedUrlResponse,
  DocumentExtraction,
} from '../types';

export const documentService = {
  /**
   * Uploads an evidentiary document file attached to a claim.
   */
  async uploadDocument(
    claimId: string,
    file: File,
    documentType = 'GENERAL_ATTACHMENT',
    allowDuplicate = false,
    onProgress?: (percent: number) => void
  ): Promise<DocumentItem> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);

    const response = await apiClient.post<DocumentItem>(
      `/claims/${claimId}/documents`,
      formData,
      {
        params: { allow_duplicate: allowDuplicate },
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total && onProgress) {
            const percent = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            onProgress(percent);
          }
        },
      }
    );
    return response.data;
  },

  /**
   * Retrieves all documents attached to a specific claim.
   */
  async listDocuments(
    claimId: string,
    includeArchived = false
  ): Promise<DocumentListResponse> {
    const response = await apiClient.get<DocumentListResponse>(
      `/claims/${claimId}/documents`,
      { params: { include_archived: includeArchived } }
    );
    return response.data;
  },

  /**
   * Retrieves single document metadata.
   */
  async getDocument(claimId: string, documentId: string): Promise<DocumentItem> {
    const response = await apiClient.get<DocumentItem>(
      `/claims/${claimId}/documents/${documentId}`
    );
    return response.data;
  },

  /**
   * Generates a short-lived (5 min) presigned S3 download URL on demand.
   */
  async getDownloadUrl(
    claimId: string,
    documentId: string
  ): Promise<PresignedUrlResponse> {
    const response = await apiClient.get<PresignedUrlResponse>(
      `/claims/${claimId}/documents/${documentId}/download-url`
    );
    return response.data;
  },

  /**
   * Soft-deletes / archives a document attached to a claim.
   */
  async deleteDocument(
    claimId: string,
    documentId: string
  ): Promise<{ message: string; id: string }> {
    const response = await apiClient.delete<{ message: string; id: string }>(
      `/claims/${claimId}/documents/${documentId}`
    );
    return response.data;
  },

  /**
   * Triggers text extraction and structured AI entity extraction.
   */
  async extractDocument(
    claimId: string,
    documentId: string
  ): Promise<DocumentExtraction> {
    const response = await apiClient.post<DocumentExtraction>(
      `/claims/${claimId}/documents/${documentId}/extract`
    );
    return response.data;
  },
};
