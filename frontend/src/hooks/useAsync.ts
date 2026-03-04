import { useState, useCallback } from 'react';
import { handleApiError } from '@/services';

interface UseAsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

/**
 * Hook for handling async operations with loading and error states
 */
export function useAsync<T>(
  asyncFunction: (...args: any[]) => Promise<T>
) {
  const [state, setState] = useState<UseAsyncState<T>>({
    data: null,
    loading: false,
    error: null,
  });

  const execute = useCallback(
    async (...args: any[]) => {
      setState({ data: null, loading: true, error: null });

      try {
        const data = await asyncFunction(...args);
        setState({ data, loading: false, error: null });
        return data;
      } catch (error) {
        const errorMessage = handleApiError(error);
        setState({ data: null, loading: false, error: errorMessage });
        throw error;
      }
    },
    [asyncFunction]
  );

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  return { ...state, execute, reset };
}
