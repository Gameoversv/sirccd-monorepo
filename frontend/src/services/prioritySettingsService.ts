import apiClient from './api';
import type { PrioritySettings, UpdatePrioritySettingsData } from '@/types';

export const prioritySettingsService = {
  async getPrioritySettings(): Promise<PrioritySettings> {
    const response = await apiClient.get<PrioritySettings>('/admin/settings/priority');
    return response.data;
  },

  async updatePrioritySettings(data: UpdatePrioritySettingsData): Promise<PrioritySettings> {
    const response = await apiClient.put<PrioritySettings>('/admin/settings/priority', data);
    return response.data;
  },
};

