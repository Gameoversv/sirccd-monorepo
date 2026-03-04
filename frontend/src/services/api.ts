import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import type { ApiError } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Get token from localStorage
    const authStorage = localStorage.getItem('sirccd-auth-storage');
    if (authStorage) {
      try {
        const { state } = JSON.parse(authStorage);
        if (state?.token) {
          config.headers.Authorization = `Bearer ${state.token}`;
        }
      } catch (error) {
        console.error('Error parsing auth storage:', error);
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle errors
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    if (error.response) {
      // Server responded with error
      // Handle validation errors (Pydantic returns detail as array)
      let detail = error.response.data?.detail || 'Error desconocido';
      if (Array.isArray(detail)) {
        detail = detail.map((err: any) => err.msg || String(err)).join('. ');
      } else if (typeof detail === 'object') {
        detail = JSON.stringify(detail);
      }

      const apiError: ApiError = {
        detail,
        status_code: error.response.status,
      };

      // Handle 401 - unauthorized
      if (error.response.status === 401) {
        // Clear auth and redirect to login
        localStorage.removeItem('sirccd-auth-storage');
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
      }

      return Promise.reject(apiError);
    } else if (error.request) {
      // Request made but no response
      return Promise.reject({
        detail: 'No se pudo conectar con el servidor',
        status_code: 0,
      });
    } else {
      // Something else happened
      return Promise.reject({
        detail: error.message || 'Error al procesar la petición',
        status_code: 0,
      });
    }
  }
);

export default apiClient;

// Helper functions
export const handleApiError = (error: unknown): string => {
  if (typeof error === 'object' && error !== null && 'detail' in error) {
    return (error as ApiError).detail;
  }
  return 'Error desconocido';
};

export const isApiError = (error: unknown): error is ApiError => {
  return typeof error === 'object' && error !== null && 'detail' in error;
};
