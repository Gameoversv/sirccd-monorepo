'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store';
import { authService } from '@/services';
import { useToast } from '@/hooks';
import type { LoginCredentials } from '@/types';

export default function LoginPage() {
  const router = useRouter();
  const { login, setLoading, setError } = useAuthStore();
  const toast = useToast();
  
  const [credentials, setCredentials] = useState<LoginCredentials>({
    username: '',
    password: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setLoading(true);
    setError(null);

    try {
      const response = await authService.login(credentials);
      login(response);
      toast.success('Inicio de sesión exitoso');
      router.push('/dashboard');
    } catch (error: any) {
      const message = typeof error?.detail === 'string' ? error.detail : 'Error al iniciar sesión';
      setError(message);
      toast.error(message);
    } finally {
      setIsSubmitting(false);
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-bold tracking-tight text-gray-900">
            SIRCCD
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Sistema de Reporte de Calles Dañadas
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4 rounded-md shadow-sm">
            <div>
              <label htmlFor="username" className="sr-only">
                Usuario
              </label>
              <input
                id="username"
                name="username"
                type="text"
                required
                className="relative block w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-500 focus:z-10 focus:border-primary-500 focus:outline-none focus:ring-primary-500 sm:text-sm"
                placeholder="Usuario"
                value={credentials.username}
                onChange={(e) =>
                  setCredentials({ ...credentials, username: e.target.value })
                }
              />
            </div>
            
            <div>
              <label htmlFor="password" className="sr-only">
                Contraseña
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                className="relative block w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-500 focus:z-10 focus:border-primary-500 focus:outline-none focus:ring-primary-500 sm:text-sm"
                placeholder="Contraseña"
                value={credentials.password}
                onChange={(e) =>
                  setCredentials({ ...credentials, password: e.target.value })
                }
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={isSubmitting}
              className="group relative flex w-full justify-center rounded-lg bg-primary-600 px-3 py-2 text-sm font-semibold text-white hover:bg-primary-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? 'Iniciando sesión...' : 'Iniciar sesión'}
            </button>
          </div>

          <div className="text-center">
            <a
              href="/register"
              className="text-sm font-medium text-primary-600 hover:text-primary-500"
            >
              ¿No tienes cuenta? Regístrate
            </a>
          </div>
        </form>
      </div>
    </div>
  );
}
