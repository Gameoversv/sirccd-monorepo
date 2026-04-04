import apiClient from './api';
import type { POILayerCategory, POILayerResponse } from '@/types';

export const poisService = {
  async getPOILayers(options?: {
    categories?: POILayerCategory[];
    limit?: number;
  }): Promise<POILayerResponse> {
    const params = new URLSearchParams();

    if (options?.categories?.length) {
      options.categories.forEach((category) => {
        params.append('categories', category);
      });
    }

    if (options?.limit) {
      params.set('limit', String(options.limit));
    }

    const query = params.toString();
    const response = await apiClient.get<POILayerResponse>(
      `/pois${query ? `?${query}` : ''}`
    );

    return response.data;
  },
};
