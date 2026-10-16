import { apiClient } from '../lib/api-client';
import type {
  FraudRingListResponse,
  ClaimFraudNetworkResponse,
} from '../types';

export const fraudRingService = {
  /**
   * Scans tenant graph and returns detected multi-claim fraud rings and collusion syndicates.
   */
  async listFraudRings(minShared = 2): Promise<FraudRingListResponse> {
    const response = await apiClient.get<FraudRingListResponse>('/fraud-rings', {
      params: { min_shared: minShared },
    });
    return response.data;
  },

  /**
   * Retrieves 1-hop and 2-hop graph neighborhood for a focal claim formatted for Cytoscape.
   */
  async getClaimNetwork(
    claimId: string,
    maxHops = 2
  ): Promise<ClaimFraudNetworkResponse> {
    const response = await apiClient.get<ClaimFraudNetworkResponse>(
      `/claims/${claimId}/fraud-network`,
      { params: { max_hops: maxHops } }
    );
    return response.data;
  },
};
