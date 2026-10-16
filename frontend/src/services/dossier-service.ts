import { apiClient } from '../lib/api-client';
import type { ForensicDossier, DossierExportFormat } from '../types';

export const dossierService = {
  /**
   * Generates or retrieves the comprehensive forensic SIU claim dossier.
   */
  async getDossier(claimId: string): Promise<ForensicDossier> {
    const response = await apiClient.get<ForensicDossier>(`/claims/${claimId}/dossier`);
    return response.data;
  },

  /**
   * Fetches the exported dossier file as a Blob in HTML, Markdown, or JSON.
   */
  async exportDossier(claimId: string, format: DossierExportFormat): Promise<Blob> {
    const response = await apiClient.get(`/claims/${claimId}/dossier/export`, {
      params: { format },
      responseType: 'blob',
    });
    return response.data;
  },

  /**
   * Downloads the exported dossier directly to the user's browser.
   */
  async downloadDossier(claimId: string, format: DossierExportFormat): Promise<void> {
    const response = await apiClient.get(`/claims/${claimId}/dossier/export`, {
      params: { format },
      responseType: 'blob',
    });

    // Determine filename
    let filename = `claimguard_dossier_${claimId.slice(0, 8)}.${format === 'markdown' ? 'md' : format}`;
    const disposition = response.headers['content-disposition'] || response.headers['Content-Disposition'];
    if (disposition && typeof disposition === 'string') {
      const match = disposition.match(/filename="?([^";]+)"?/i);
      if (match && match[1]) {
        filename = match[1];
      }
    }

    // Trigger browser download
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};
