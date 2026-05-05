import apiClient from './api';

export interface Zone {
  id: number;
  name: string;
  code: string | null;
}

export const zonesService = {
  async getZones(): Promise<Zone[]> {
    const response = await apiClient.get<Zone[]>('/zones/');
    return response.data;
  },
};
