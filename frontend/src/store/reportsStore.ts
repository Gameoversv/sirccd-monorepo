import { create } from 'zustand';
import type { Report, ReportFilters, PaginatedResponse } from '@/types';

interface ReportsState {
  reports: Report[];
  selectedReport: Report | null;
  filters: ReportFilters;
  pagination: {
    page: number;
    per_page: number;
    total: number;
    total_pages: number;
  };
  isLoading: boolean;
  error: string | null;

  // Actions
  setReports: (response: PaginatedResponse<Report>) => void;
  addReport: (report: Report) => void;
  updateReport: (id: number, report: Partial<Report>) => void;
  deleteReport: (id: number) => void;
  setSelectedReport: (report: Report | null) => void;
  setFilters: (filters: Partial<ReportFilters>) => void;
  clearFilters: () => void;
  setPage: (page: number) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

const initialFilters: ReportFilters = {};

export const useReportsStore = create<ReportsState>()((set) => ({
  reports: [],
  selectedReport: null,
  filters: initialFilters,
  pagination: {
    page: 1,
    per_page: 20,
    total: 0,
    total_pages: 0,
  },
  isLoading: false,
  error: null,

  setReports: (response) => set({
    reports: response.items,
    pagination: {
      page: response.page,
      per_page: response.per_page,
      total: response.total,
      total_pages: response.total_pages,
    },
    isLoading: false,
  }),

  addReport: (report) => set((state) => ({
    reports: [report, ...state.reports],
  })),

  updateReport: (id, updatedReport) => set((state) => ({
    reports: state.reports.map((r) =>
      r.id === id ? { ...r, ...updatedReport } : r
    ),
  })),

  deleteReport: (id) => set((state) => ({
    reports: state.reports.filter((r) => r.id !== id),
  })),

  setSelectedReport: (report) => set({ selectedReport: report }),

  setFilters: (newFilters) => set((state) => ({
    filters: { ...state.filters, ...newFilters },
    pagination: { ...state.pagination, page: 1 }, // Reset to page 1 when filters change
  })),

  clearFilters: () => set({
    filters: initialFilters,
    pagination: { page: 1, per_page: 20, total: 0, total_pages: 0 },
  }),

  setPage: (page) => set((state) => ({
    pagination: { ...state.pagination, page },
  })),

  setLoading: (loading) => set({ isLoading: loading }),

  setError: (error) => set({ error, isLoading: false }),

  clearError: () => set({ error: null }),
}));
