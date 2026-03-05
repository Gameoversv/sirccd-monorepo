import apiClient from './api';
import type { 
  Report, 
  ReportFilters, 
  PaginatedResponse 
} from '@/types';

export const reportsService = {
  /**
   * Get all reports with filters and pagination
   */
  async getReports(
    filters?: ReportFilters,
    page: number = 1,
    perPage: number = 20
  ): Promise<PaginatedResponse<Report>> {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
      ...Object.fromEntries(
        Object.entries(filters || {}).filter(([_, v]) => v != null)
      ),
    });

    const response = await apiClient.get<PaginatedResponse<Report>>(
      `/reportes?${params.toString()}`
    );
    return response.data;
  },

  async getReport(id: number): Promise<Report> {
    const response = await apiClient.get<Report>(`/reportes/${id}`);
    return response.data;
  },

  async createReport(formData: FormData): Promise<Report> {
    const response = await apiClient.post<Report>('/reportes', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async updateReport(id: number, data: Partial<Report>): Promise<Report> {
    const response = await apiClient.patch<Report>(`/reportes/${id}`, data);
    return response.data;
  },

  /**
   * Delete report
   */
  async deleteReport(id: number): Promise<void> {
    await apiClient.delete(`/reports/${id}`);
  },

  /**
   * Check for duplicates
   */
  async checkDuplicate(formData: FormData): Promise<{
    is_duplicate: boolean;
    similar_reports: Report[];
    confidence: number;
  }> {
    const response = await apiClient.post(
      '/deduplication/check',
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
   * Verify image privacy before uploading (W-03)
   * Detects faces/plates that will be blurred server-side on create.
   */
  async verifyImage(file: File): Promise<{
    is_clean: boolean;
    faces_detected: number;
    plates_detected: number;
    regions: { type: string; x: number; y: number; w: number; h: number }[];
    warnings: string[];
    message: string;
    error?: string;
  }> {
    const form = new FormData();
    form.append('image', file);
    const response = await apiClient.post('/reportes/verify-image', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
};
