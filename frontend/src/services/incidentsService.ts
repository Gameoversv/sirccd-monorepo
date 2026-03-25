import apiClient from './api';
import type { 
  Incident, 
  IncidentDetail,
  IncidentFilters, 
  PaginatedResponse,
  IncidentStatus,
  ExportOptions
} from '@/types';

export const incidentsService = {
  /**
   * Get all incidents with filters and pagination
   */
  async getIncidents(
    filters?: IncidentFilters,
    page: number = 1,
    perPage: number = 20
  ): Promise<PaginatedResponse<Incident>> {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
      ...Object.fromEntries(
        Object.entries(filters || {}).filter(([_, v]) => v != null)
      ),
    });

    const response = await apiClient.get<PaginatedResponse<Incident>>(
      `/incidents?${params.toString()}`
    );
    return response.data;
  },

  /**
   * Get incident by ID (full detail)
   */
  async getIncident(id: number): Promise<IncidentDetail> {
    const response = await apiClient.get<IncidentDetail>(`/incidents/${id}`);
    return response.data;
  },

  /**
   * Update incident status
   */
  async updateStatus(id: number, status: string, notes?: string): Promise<IncidentDetail> {
    const response = await apiClient.patch<IncidentDetail>(
      `/incidents/${id}/status`,
      { status, notes }
    );
    return response.data;
  },

  /**
   * Upload after image (repair evidence)
   */
  async uploadAfterImage(id: number, formData: FormData): Promise<Incident> {
    const response = await apiClient.post<Incident>(
      `/incidents/${id}/after-image`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  /**
   * Export incidents
   */
  async exportIncidents(options: ExportOptions): Promise<Blob> {
    const params = new URLSearchParams({
      format: options.format,
      include_kpis: options.include_kpis?.toString() || 'false',
      ...Object.fromEntries(
        Object.entries(options.filters || {}).filter(([_, v]) => v != null)
      ),
    });

    const response = await apiClient.get(
      `/export/incidents?${params.toString()}`,
      {
        responseType: 'blob',
      }
    );
    return response.data;
  },

  /**
   * Recalculate priority score for an incident
   */
  async recalculatePriority(id: number): Promise<{ incident_id: number; new_priority: string; new_score: number }> {
    const response = await apiClient.post(`/incidents/${id}/recalculate-priority`);
    return response.data;
  },

  /**
   * Get incident statistics (KPI overview)
   */
  async getStats(): Promise<{
    total_incidents: number;
    by_status: Record<string, number>;
    by_priority: Record<string, number>;
    by_damage_type: Record<string, number>;
    avg_priority_score: number | null;
    avg_resolution_hours: number | null;
    pending_assignment: number;
    in_progress: number;
    active_count: number;
    resolved_count: number;
    avg_ttr_hours: number | null;
    sla_compliance_pct: number | null;
  }> {
    const response = await apiClient.get('/incidents/stats/overview');
    return response.data;
  },

  /**
   * Get heatmap data points for the map layer (P-01)
   */
  async getHeatmapData(
    weightBy: 'frequency' | 'severity' | 'age' = 'frequency',
    filters?: { status?: string; damage_type?: string; severity?: string },
  ): Promise<{ points: [number, number, number][]; weight_by: string; count: number }> {
    const params = new URLSearchParams({ weight_by: weightBy });
    if (filters) {
      Object.entries(filters).forEach(([k, v]) => {
        if (v) params.set(k, v);
      });
    }
    const response = await apiClient.get(`/incidents/heatmap?${params.toString()}`);
    return response.data;
  },
};
