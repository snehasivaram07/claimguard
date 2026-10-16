import { apiClient, tokenStorage } from '../lib/api-client';
import type { LoginRequest, RegisterRequest, TokenResponse, User } from '../types';

export const authService = {
  /**
   * Registers a new user account with email and password.
   */
  async register(data: RegisterRequest): Promise<User> {
    const response = await apiClient.post<User>('/auth/register', data);
    return response.data;
  },

  /**
   * Authenticates user and stores access & refresh tokens.
   */
  async login(credentials: LoginRequest): Promise<TokenResponse> {
    const response = await apiClient.post<TokenResponse>('/auth/login', credentials);
    const { access_token, refresh_token } = response.data;
    tokenStorage.setTokens(access_token, refresh_token);
    return response.data;
  },

  /**
   * Manually refreshes the access token using the stored refresh token.
   */
  async refreshToken(): Promise<TokenResponse | null> {
    const refreshToken = tokenStorage.getRefreshToken();
    if (!refreshToken) return null;

    try {
      const response = await apiClient.post<TokenResponse>('/auth/refresh', {
        refresh_token: refreshToken,
      });
      const { access_token, refresh_token: newRefreshToken } = response.data;
      tokenStorage.setTokens(access_token, newRefreshToken);
      return response.data;
    } catch (error) {
      tokenStorage.clearTokens();
      throw error;
    }
  },

  /**
   * Revokes the current session and invalidates refresh token on the backend.
   */
  async logout(): Promise<void> {
    const refreshToken = tokenStorage.getRefreshToken();
    if (refreshToken) {
      try {
        await apiClient.post('/auth/logout', { refresh_token: refreshToken });
      } catch {
        // Silently proceed if network fails during logout
      }
    }
    tokenStorage.clearTokens();
  },

  /**
   * Retrieves the authenticated user profile from /auth/me.
   */
  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },

  /**
   * Checks whether tokens exist in local storage.
   */
  hasStoredSession(): boolean {
    return !!tokenStorage.getAccessToken() || !!tokenStorage.getRefreshToken();
  },
};
