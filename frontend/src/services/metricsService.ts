import apiClient from './api';
import type { SystemMetrics } from '@/types';

export const metricsService = {
  /**
   * Get system-wide metrics
   */
  async getSystemMetrics(): Promise<SystemMetrics> {
    const response = await apiClient.get<SystemMetrics>('/metrics/system');
    return response.data;
  },

  /**
   * Get health check
   */
  async getHealth(): Promise<{
    status: string;
    service: string;
    version: string;
    timestamp: string;
  }> {
    const response = await apiClient.get('/health');
    return response.data;
  },
};
