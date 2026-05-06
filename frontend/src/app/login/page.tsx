'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslation } from 'react-i18next';
import { ShieldCheck, Lock, User2, ArrowRight, MapPin, Activity, BarChart3 } from 'lucide-react';
import { useAuthStore } from '@/store';
import { authService } from '@/services';
import { useToast } from '@/hooks';
import type { LoginCredentials } from '@/types';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';
import { ThemeToggle } from '@/components/ThemeToggle';

export default function LoginPage() {
  const router = useRouter();
  const { login, setLoading, setError } = useAuthStore();
  const toast = useToast();
  const { t } = useTranslation();

  const [credentials, setCredentials] = useState<LoginCredentials>({ username: '', password: '' });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setLoading(true);
    setError(null);
    try {
      const response = await authService.login(credentials);
      login(response);
      toast.success(t('auth.login.success'));
      router.push('/dashboard');
    } catch (error: any) {
      const message = typeof error?.detail === 'string' ? error.detail : t('auth.login.error');
      setError(message);
      toast.error(message);
    } finally {
      setIsSubmitting(false);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="fixed top-4 right-4 z-50 flex items-center gap-2">
        <LanguageSwitcher />
        <ThemeToggle />
      </div>

      <div className="grid min-h-screen lg:grid-cols-2">
        <div className="relative hidden lg:flex flex-col justify-between overflow-hidden bg-gradient-brand text-white p-12">
          <div className="absolute inset-0 bg-gradient-mesh opacity-40" />
          <div className="relative z-10 flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/15 backdrop-blur-sm">
              <ShieldCheck className="h-6 w-6" />
            </div>
            <span className="text-lg font-semibold tracking-tight">SIRCCD</span>
          </div>

          <div className="relative z-10 space-y-6">
            <h2 className="text-4xl font-bold tracking-tight text-balance leading-tight">
              {t('auth.login.heroTitle')}
            </h2>
            <p className="text-white/80 text-lg max-w-md">
              {t('auth.login.heroSubtitle')}
            </p>
            <ul className="space-y-3 text-sm text-white/90">
              <li className="flex items-center gap-3"><MapPin className="h-4 w-4" /> {t('auth.login.featureGeo')}</li>
              <li className="flex items-center gap-3"><Activity className="h-4 w-4" /> {t('auth.login.featureMl')}</li>
              <li className="flex items-center gap-3"><BarChart3 className="h-4 w-4" /> {t('auth.login.featureDashboards')}</li>
            </ul>
          </div>

          <div className="relative z-10 text-xs text-white/60">&copy; {new Date().getFullYear()} SIRCCD</div>
        </div>

        <div className="flex items-center justify-center p-6 sm:p-12">
          <div className="w-full max-w-md animate-slide-up">
            <div className="mb-8 lg:hidden flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-brand text-white shadow-soft">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <span className="text-lg font-semibold tracking-tight">SIRCCD</span>
            </div>

            <div className="space-y-2 mb-8">
              <h1 className="text-3xl font-bold tracking-tight">{t('auth.login.title')}</h1>
              <p className="text-sm text-muted-foreground">{t('auth.login.subtitle')}</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5" aria-label={t('auth.login.submit')}>
              <div className="space-y-1.5">
                <label htmlFor="username" className="text-sm font-medium">
                  {t('auth.login.username')}
                </label>
                <div className="relative">
                  <User2 className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <input
                    id="username"
                    name="username"
                    type="text"
                    autoComplete="username"
                    required
                    className="block w-full rounded-lg border border-border bg-card pl-10 pr-3 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent transition-shadow"
                    placeholder={t('auth.login.username')}
                    value={credentials.username}
                    onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label htmlFor="password" className="text-sm font-medium">
                  {t('auth.login.password')}
                </label>
                <div className="relative">
                  <Lock className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <input
                    id="password"
                    name="password"
                    type="password"
                    autoComplete="current-password"
                    required
                    className="block w-full rounded-lg border border-border bg-card pl-10 pr-3 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent transition-shadow"
                    placeholder={t('auth.login.password')}
                    value={credentials.password}
                    onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="group relative flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-brand px-4 py-2.5 text-sm font-semibold text-white shadow-soft hover:shadow-elevated transition-all duration-150 active:scale-[0.99] disabled:opacity-60 disabled:cursor-not-allowed focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
              >
                {isSubmitting ? t('auth.login.submitting') : t('auth.login.submit')}
                {!isSubmitting && <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />}
              </button>

              <p className="text-center text-sm text-muted-foreground">
                {t('auth.login.noAccount')}{' '}
                <a href="/register" className="font-medium text-primary-600 hover:text-primary-500 hover:underline underline-offset-4">
                  {t('auth.login.registerCta')}
                </a>
              </p>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
