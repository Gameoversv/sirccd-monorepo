import apiClient from './api';
import type { UserDetail, UserListResponse, CreateUserData, UpdateUserData } from '@/types';

export const usersService = {
  async getMe(): Promise<UserDetail> {
    const response = await apiClient.get<UserDetail>('/users/me');
    return response.data;
  },

  async listUsers(params?: {
    page?: number;
    per_page?: number;
    role?: string;
    is_active?: boolean;
    search?: string;
  }): Promise<UserListResponse> {
    const query = new URLSearchParams();
    if (params?.page) query.set('page', String(params.page));
    if (params?.per_page) query.set('per_page', String(params.per_page));
    if (params?.role) query.set('role', params.role);
    if (params?.is_active != null) query.set('is_active', String(params.is_active));
    if (params?.search) query.set('search', params.search);
    const response = await apiClient.get<UserListResponse>(`/users?${query.toString()}`);
    return response.data;
  },

  async getUser(id: number): Promise<UserDetail> {
    const response = await apiClient.get<UserDetail>(`/users/${id}`);
    return response.data;
  },

  async createUser(data: CreateUserData): Promise<UserDetail> {
    const response = await apiClient.post<UserDetail>('/users', data);
    return response.data;
  },

  async updateUser(id: number, data: UpdateUserData): Promise<UserDetail> {
    const response = await apiClient.patch<UserDetail>(`/users/${id}`, data);
    return response.data;
  },

  async deactivateUser(id: number): Promise<void> {
    await apiClient.delete(`/users/${id}`);
  },

  async deleteUser(id: number): Promise<void> {
    await apiClient.delete(`/users/${id}/permanent`);
  },
};
