import { apiClient } from '../lib/api-client';
import type { AuditTrailResponse } from '../types';

export const auditService = {
  /**
   * Retrieves security audit events for the current authenticated user.
   */
  async getUserAudit(skip = 0, limit = 50): Promise<AuditTrailResponse> {
    const response = await apiClient.get<AuditTrailResponse>('/auth/me/audit', {
      params: { skip, limit },
    });
    return response.data;
  },

  /**
   * Retrieves immutable audit events for a specific claim.
   */
  async getClaimAudit(
    claimId: string,
    skip = 0,
    limit = 50
  ): Promise<AuditTrailResponse> {
    const response = await apiClient.get<AuditTrailResponse>(
      `/claims/${claimId}/audit`,
      { params: { skip, limit } }
    );
    return response.data;
  },
};
