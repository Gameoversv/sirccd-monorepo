import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store';
import { usersService } from '@/services/usersService';

/**
 * Hook to protect routes that require authentication.
 * Also syncs the user profile (role, etc.) from the backend on mount.
 */
export function useAuth(redirectTo: string = '/login') {
  const router = useRouter();
  const { isAuthenticated, isLoading, token, setUser } = useAuthStore();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push(redirectTo);
      return;
    }
    // Re-fetch profile from backend so role changes are reflected immediately
    if (isAuthenticated && token) {
      usersService.getMe().then((profile) => {
        setUser({
          id: profile.id,
          username: profile.username,
          email: profile.email,
          full_name: profile.full_name ?? '',
          role: profile.role,
          is_active: profile.is_active,
          created_at: profile.created_at,
        });
      }).catch(() => {
        // Silently ignore — token may have expired, redirect will handle it
      });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, isLoading, router, redirectTo]);

  return { isAuthenticated, isLoading };
}
