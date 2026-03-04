import apiClient from './api';
import type { 
  AuthResponse, 
  LoginCredentials, 
  RegisterData, 
  User 
} from '@/types';

export const authService = {
  /**
   * Login user
   */
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/login', credentials);
    return response.data;
  },

  /**
   * Register new user
   */
  async register(data: RegisterData): Promise<User> {
    const response = await apiClient.post<User>('/auth/register', data);
    return response.data;
  },

  /**
   * Get current user profile
   */
  async getMe(): Promise<User> {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },

  /**
   * Logout (client-side only, clear token)
   */
  logout(): void {
    localStorage.removeItem('sirccd-auth-storage');
  },
};
