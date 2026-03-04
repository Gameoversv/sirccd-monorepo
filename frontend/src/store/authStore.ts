import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { User, AuthResponse } from '@/types';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setUser: (user: User) => void;
  setToken: (token: string) => void;
  login: (authResponse: AuthResponse) => void;
  logout: () => void;
  setError: (error: string | null) => void;
  setLoading: (loading: boolean) => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      setUser: (user) => set({ user, isAuthenticated: true }),
      
      setToken: (token) => set({ token }),
      
      login: (authResponse) => set({
        user: {
          id: authResponse.user_id,
          username: authResponse.username,
          email: authResponse.email,
          full_name: authResponse.full_name || '',
          role: authResponse.role,
          is_active: true,
          created_at: new Date().toISOString(),
        },
        token: authResponse.access_token,
        isAuthenticated: true,
        error: null,
      }),
      
      logout: () => set({
        user: null,
        token: null,
        isAuthenticated: false,
        error: null,
      }),
      
      setError: (error) => set({ error, isLoading: false }),
      
      setLoading: (loading) => set({ isLoading: loading }),
      
      clearError: () => set({ error: null }),
    }),
    {
      name: 'sirccd-auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
