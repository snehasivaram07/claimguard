import { apiClient } from '../lib/api-client';
import type { SystemHealthResponse } from '../types';

export const healthService = {
  /**
   * Retrieves readiness status for all backing engines (PostgreSQL, FalkorDB, S3).
   */
  async getReadiness(): Promise<SystemHealthResponse> {
    const response = await apiClient.get<SystemHealthResponse>('/health/ready');
    return response.data;
  },

  /**
   * Basic liveness ping confirming backend process is active.
   */
  async getLiveness(): Promise<{ status: string }> {
    const response = await apiClient.get<{ status: string }>('/health/live');
    return response.data;
  },
};
