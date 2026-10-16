import { apiClient } from '../lib/api-client';
import type {
  Claim,
  ClaimCreateRequest,
  ClaimListResponse,
  ClaimUpdateRequest,
  AuditTrailResponse,
} from '../types';

export const claimService = {
  /**
   * Retrieves paginated claims owned by the authenticated tenant.
   */
  async listClaims(
    skip = 0,
    limit = 50,
    includeArchived = false
  ): Promise<ClaimListResponse> {
    const response = await apiClient.get<ClaimListResponse>('/claims', {
      params: { skip, limit, include_archived: includeArchived },
    });
    return response.data;
  },

  /**
   * Retrieves full details of a specific claim.
   */
  async getClaim(claimId: string): Promise<Claim> {
    const response = await apiClient.get<Claim>(`/claims/${claimId}`);
    return response.data;
  },

  /**
   * Creates a new insurance claim.
   */
  async createClaim(data: ClaimCreateRequest): Promise<Claim> {
    const response = await apiClient.post<Claim>('/claims', data);
    return response.data;
  },

  /**
   * Updates fields or lifecycle status of an existing claim.
   */
  async updateClaim(claimId: string, data: ClaimUpdateRequest): Promise<Claim> {
    const response = await apiClient.patch<Claim>(`/claims/${claimId}`, data);
    return response.data;
  },

  /**
   * Soft-deletes a claim by transitioning status to ARCHIVED.
   */
  async archiveClaim(claimId: string): Promise<{ message: string; id: string }> {
    const response = await apiClient.delete<{ message: string; id: string }>(
      `/claims/${claimId}`
    );
    return response.data;
  },

  /**
   * Retrieves the immutable audit trail for a specific claim.
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
