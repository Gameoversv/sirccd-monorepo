import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store';

/**
 * Hook to protect routes that require authentication
 */
export function useAuth(redirectTo: string = '/login') {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuthStore();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push(redirectTo);
    }
  }, [isAuthenticated, isLoading, router, redirectTo]);

  return { isAuthenticated, isLoading };
}
