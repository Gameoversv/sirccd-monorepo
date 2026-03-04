'use client';

import { useEffect } from 'react';
import { useUIStore } from '@/store';
import { X, CheckCircle, XCircle, AlertCircle, Info } from 'lucide-react';

export function ToastContainer() {
  const { toasts, removeToast } = useUIStore();

  return (
    <div className="pointer-events-none fixed inset-0 z-50 flex items-end justify-end p-6 sm:items-start sm:justify-end">
      <div className="flex w-full flex-col items-center space-y-4 sm:items-end">
        {toasts.map((toast) => (
          <Toast
            key={toast.id}
            {...toast}
            onClose={() => removeToast(toast.id)}
          />
        ))}
      </div>
    </div>
  );
}

interface ToastProps {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;
  onClose: () => void;
}

function Toast({ id, type, message, duration = 5000, onClose }: ToastProps) {
  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(onClose, duration);
      return () => clearTimeout(timer);
    }
  }, [duration, onClose]);

  const icons = {
    success: <CheckCircle className="h-5 w-5 text-success-500" />,
    error: <XCircle className="h-5 w-5 text-danger-500" />,
    warning: <AlertCircle className="h-5 w-5 text-warning-500" />,
    info: <Info className="h-5 w-5 text-primary-500" />,
  };

  const colors = {
    success: 'bg-success-50 border-success-200',
    error: 'bg-danger-50 border-danger-200',
    warning: 'bg-warning-50 border-warning-200',
    info: 'bg-primary-50 border-primary-200',
  };

  return (
    <div
      className={`pointer-events-auto w-full max-w-sm overflow-hidden rounded-lg border ${colors[type]} shadow-lg`}
    >
      <div className="p-4">
        <div className="flex items-start">
          <div className="flex-shrink-0">{icons[type]}</div>
          <div className="ml-3 w-0 flex-1 pt-0.5">
            <p className="text-sm font-medium text-gray-900">{message}</p>
          </div>
          <div className="ml-4 flex flex-shrink-0">
            <button
              type="button"
              className="inline-flex rounded-md text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
              onClick={onClose}
            >
              <span className="sr-only">Cerrar</span>
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
