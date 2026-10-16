import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { apiClient, tokenStorage } from '../lib/api-client';
import type { LoginRequest, RegisterRequest, TokenResponse, User } from '../types';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<User>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchCurrentUser = useCallback(async () => {
    try {
      const response = await apiClient.get<User>('/auth/me');
      setUser(response.data);
    } catch {
      setUser(null);
      tokenStorage.clearTokens();
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    const token = tokenStorage.getAccessToken();
    const refreshToken = tokenStorage.getRefreshToken();
    if (token || refreshToken) {
      fetchCurrentUser();
    } else {
      setIsLoading(false);
    }

    // Listen for global auth expiration events triggered by api-client interceptor
    const handleAuthExpired = () => {
      setUser(null);
    };

    window.addEventListener('claimguard:auth-expired', handleAuthExpired);
    return () => {
      window.removeEventListener('claimguard:auth-expired', handleAuthExpired);
    };
  }, [fetchCurrentUser]);

  const login = async (credentials: LoginRequest): Promise<void> => {
    const response = await apiClient.post<TokenResponse>('/auth/login', credentials);
    const { access_token, refresh_token } = response.data;
    tokenStorage.setTokens(access_token, refresh_token);
    await fetchCurrentUser();
  };

  const register = async (data: RegisterRequest): Promise<User> => {
    const response = await apiClient.post<User>('/auth/register', data);
    return response.data;
  };

  const logout = async (): Promise<void> => {
    const refreshToken = tokenStorage.getRefreshToken();
    if (refreshToken) {
      try {
        await apiClient.post('/auth/logout', { refresh_token: refreshToken });
      } catch {
        // Silently continue if logout call fails on network
      }
    }
    tokenStorage.clearTokens();
    setUser(null);
  };

  const refreshProfile = async (): Promise<void> => {
    await fetchCurrentUser();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
