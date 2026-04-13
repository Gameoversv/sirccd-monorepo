'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ShieldCheck, ArrowRight } from 'lucide-react';
import { authService } from '@/services';
import { useToast } from '@/hooks';
import type { RegisterData } from '@/types';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';
import { ThemeToggle } from '@/components/ThemeToggle';

const inputCls =
  'block w-full rounded-lg border border-border bg-card px-3 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent transition-shadow';

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
    <div className="min-h-screen bg-background bg-gradient-mesh">
      <div className="fixed top-4 right-4 z-50 flex items-center gap-2">
        <LanguageSwitcher />
        <ThemeToggle />
      </div>

      <div className="flex min-h-screen items-center justify-center px-4 py-12">
        <div className="w-full max-w-md animate-slide-up">
          <div className="mb-8 flex items-center gap-3 justify-center">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-brand text-white shadow-soft">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <span className="text-lg font-semibold tracking-tight">SIRCCD</span>
          </div>

          <div className="rounded-2xl border border-border bg-card p-8 shadow-elevated">
            <div className="space-y-1 mb-6 text-center">
              <h1 className="text-2xl font-bold tracking-tight">Crear cuenta</h1>
              <p className="text-sm text-muted-foreground">Regístrate en SIRCCD</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label htmlFor="full_name" className="text-sm font-medium">Nombre completo</label>
                <input id="full_name" type="text" required className={inputCls}
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label htmlFor="username" className="text-sm font-medium">Usuario</label>
                  <input id="username" type="text" required className={inputCls}
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value })} />
                </div>
                <div className="space-y-1.5">
                  <label htmlFor="email" className="text-sm font-medium">Email</label>
                  <input id="email" type="email" required className={inputCls}
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })} />
                </div>
              </div>
              <div className="space-y-1.5">
                <label htmlFor="password" className="text-sm font-medium">Contraseña</label>
                <input id="password" type="password" required className={inputCls}
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })} />
              </div>
              <div className="space-y-1.5">
                <label htmlFor="confirm_password" className="text-sm font-medium">Confirmar contraseña</label>
                <input id="confirm_password" type="password" required className={inputCls}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)} />
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="group mt-2 flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-brand px-4 py-2.5 text-sm font-semibold text-white shadow-soft hover:shadow-elevated transition-all active:scale-[0.99] disabled:opacity-60"
              >
                {isSubmitting ? 'Registrando...' : 'Registrarse'}
                {!isSubmitting && <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />}
              </button>

              <p className="text-center text-sm text-muted-foreground">
                ¿Ya tienes cuenta?{' '}
                <a href="/login" className="font-medium text-primary-600 hover:text-primary-500 hover:underline underline-offset-4">
                  Inicia sesión
                </a>
              </p>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
