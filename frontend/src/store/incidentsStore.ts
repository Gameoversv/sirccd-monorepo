import { create } from 'zustand';
import type { Incident, IncidentFilters, PaginatedResponse } from '@/types';

interface IncidentsState {
  incidents: Incident[];
  selectedIncident: Incident | null;
  filters: IncidentFilters;
  pagination: {
    page: number;
    per_page: number;
    total: number;
    total_pages: number;
  };
  isLoading: boolean;
  error: string | null;

  // Actions
  setIncidents: (response: PaginatedResponse<Incident>) => void;
  addIncident: (incident: Incident) => void;
  updateIncident: (id: number, incident: Partial<Incident>) => void;
  deleteIncident: (id: number) => void;
  setSelectedIncident: (incident: Incident | null) => void;
  setFilters: (filters: Partial<IncidentFilters>) => void;
  clearFilters: () => void;
  setPage: (page: number) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

const initialFilters: IncidentFilters = {};

export const useIncidentsStore = create<IncidentsState>()((set) => ({
  incidents: [],
  selectedIncident: null,
  filters: initialFilters,
  pagination: {
    page: 1,
    per_page: 20,
    total: 0,
    total_pages: 0,
  },
  isLoading: false,
  error: null,

  setIncidents: (response) => set({
    incidents: response.items,
    pagination: {
      page: response.page,
      per_page: response.per_page,
      total: response.total,
      total_pages: response.total_pages,
    },
    isLoading: false,
  }),

  addIncident: (incident) => set((state) => ({
    incidents: [incident, ...state.incidents],
  })),

  updateIncident: (id, updatedIncident) => set((state) => ({
    incidents: state.incidents.map((i) =>
      i.id === id ? { ...i, ...updatedIncident } : i
    ),
  })),

  deleteIncident: (id) => set((state) => ({
    incidents: state.incidents.filter((i) => i.id !== id),
  })),

  setSelectedIncident: (incident) => set({ selectedIncident: incident }),

  setFilters: (newFilters) => set((state) => ({
    filters: { ...state.filters, ...newFilters },
    pagination: { ...state.pagination, page: 1 },
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
