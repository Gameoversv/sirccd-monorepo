'use client';

import { useRouter } from 'next/navigation';
import { LogOut, ShieldCheck } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '@/store';
import { LanguageSwitcher } from './LanguageSwitcher';
import { ThemeToggle } from './ThemeToggle';

export function PortalTopbar() {
  const { user, logout } = useAuthStore();
  const router = useRouter();
  const { t } = useTranslation();

  const initials = (user?.full_name || user?.username || '?')
    .split(' ')
    .map((s) => s[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

  return (
    <header className="sticky top-0 z-30 h-14 border-b border-border bg-background/80 backdrop-blur-sm">
      <div className="max-w-4xl mx-auto flex h-full items-center gap-3 px-4 sm:px-6">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-brand text-white shadow-sm">
            <ShieldCheck className="h-4 w-4" />
          </div>
          <span className="font-bold text-sm tracking-tight">SIRCCD</span>
        </div>

        <div className="ml-auto flex items-center gap-2">
          <LanguageSwitcher />
          <ThemeToggle />
          <div className="mx-1 h-5 w-px bg-border" />
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-brand text-white text-xs font-semibold shadow-sm flex-shrink-0">
              {initials}
            </div>
            <span className="hidden sm:block text-sm font-medium truncate max-w-32">
              {user?.full_name || user?.username}
            </span>
          </div>
          <button
            onClick={() => { logout(); router.push('/login'); }}
            aria-label={t('nav.logout')}
            title={t('nav.logout')}
            className="inline-flex items-center justify-center w-8 h-8 rounded-lg border border-border text-muted-foreground hover:text-red-600 hover:border-red-300 dark:hover:border-red-800 transition-colors"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
