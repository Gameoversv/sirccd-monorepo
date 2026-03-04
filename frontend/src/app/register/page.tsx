'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/services';
import { useToast } from '@/hooks';
import type { RegisterData } from '@/types';

export default function RegisterPage() {
  const router = useRouter();
  const toast = useToast();
  
  const [formData, setFormData] = useState<RegisterData>({
    username: '',
    email: '',
    password: '',
    full_name: '',
  });
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (formData.password !== confirmPassword) {
      toast.error('Las contraseñas no coinciden');
      return;
    }

    setIsSubmitting(true);

    try {
      await authService.register(formData);
      toast.success('Registro exitoso. Por favor inicia sesión.');
      router.push('/login');
    } catch (error: any) {
      const message = typeof error?.detail === 'string' ? error.detail : 'Error al registrar usuario';
      toast.error(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-bold tracking-tight text-gray-900">
            Crear cuenta
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Regístrate en SIRCCD
          </p>
        </div>
        
        <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="full_name" className="block text-sm font-medium text-gray-700">
              Nombre completo
            </label>
            <input
              id="full_name"
              name="full_name"
              type="text"
              required
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-primary-500 focus:outline-none focus:ring-primary-500"
              value={formData.full_name}
              onChange={(e) =>
                setFormData({ ...formData, full_name: e.target.value })
              }
            />
          </div>

          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700">
              Usuario
            </label>
            <input
              id="username"
              name="username"
              type="text"
              required
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-primary-500 focus:outline-none focus:ring-primary-500"
              value={formData.username}
              onChange={(e) =>
                setFormData({ ...formData, username: e.target.value })
              }
            />
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700">
              Email
            </label>
            <input
              id="email"
              name="email"
              type="email"
              required
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-primary-500 focus:outline-none focus:ring-primary-500"
              value={formData.email}
              onChange={(e) =>
                setFormData({ ...formData, email: e.target.value })
              }
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700">
              Contraseña
            </label>
            <input
              id="password"
              name="password"
              type="password"
              required
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-primary-500 focus:outline-none focus:ring-primary-500"
              value={formData.password}
              onChange={(e) =>
                setFormData({ ...formData, password: e.target.value })
              }
            />
          </div>

          <div>
            <label htmlFor="confirm_password" className="block text-sm font-medium text-gray-700">
              Confirmar contraseña
            </label>
            <input
              id="confirm_password"
              name="confirm_password"
              type="password"
              required
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-primary-500 focus:outline-none focus:ring-primary-500"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-lg bg-primary-600 px-3 py-2 text-sm font-semibold text-white hover:bg-primary-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? 'Registrando...' : 'Registrarse'}
          </button>

          <div className="text-center">
            <a
              href="/login"
              className="text-sm font-medium text-primary-600 hover:text-primary-500"
            >
              ¿Ya tienes cuenta? Inicia sesión
            </a>
          </div>
        </form>
      </div>
    </div>
  );
}
