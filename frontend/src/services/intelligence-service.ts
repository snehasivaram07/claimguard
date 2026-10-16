import { apiClient } from '../lib/api-client';
import type { ClaimIntelligenceAnalysis } from '../types';

export const intelligenceService = {
  /**
   * Retrieves cached claim intelligence analysis, timeline, and discrepancy report.
   * Returns null if analysis has not been performed yet (404 Not Found).
   */
  async getIntelligence(claimId: string): Promise<ClaimIntelligenceAnalysis | null> {
    try {
      const response = await apiClient.get<ClaimIntelligenceAnalysis>(
        `/claims/${claimId}/intelligence`
      );
      return response.data;
    } catch (err: unknown) {
      if (
        typeof err === 'object' &&
        err !== null &&
        'response' in err &&
        (err as { response?: { status?: number } }).response?.status === 404
      ) {
        return null;
      }
      throw err;
    }
  },

  /**
   * Triggers cross-document intelligence analysis, timeline reconstruction, and discrepancy detection.
   */
  async analyzeClaim(claimId: string): Promise<ClaimIntelligenceAnalysis> {
    const response = await apiClient.post<ClaimIntelligenceAnalysis>(
      `/claims/${claimId}/analyze`
    );
    return response.data;
  },
};
