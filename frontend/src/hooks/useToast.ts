import { useEffect } from 'react';
import { useUIStore } from '@/store';

interface ToastOptions {
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;
}

/**
 * Hook to show toast notifications
 */
export function useToast() {
  const { addToast, removeToast } = useUIStore();

  const showToast = ({ type, message, duration = 5000 }: ToastOptions) => {
    const id = `${Date.now()}-${Math.random()}`;
    
    addToast({
      type,
      message,
      duration,
    });

    // Auto-remove after duration
    if (duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, duration);
    }

    return id;
  };

  return {
    success: (message: string, duration?: number) =>
      showToast({ type: 'success', message, duration }),
    error: (message: string, duration?: number) =>
      showToast({ type: 'error', message, duration }),
    warning: (message: string, duration?: number) =>
      showToast({ type: 'warning', message, duration }),
    info: (message: string, duration?: number) =>
      showToast({ type: 'info', message, duration }),
  };
}
