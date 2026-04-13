'use client';

import { useRouter } from 'next/navigation';
import { LogOut, Search } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '@/store';
import { LanguageSwitcher } from './LanguageSwitcher';
import { ThemeToggle } from './ThemeToggle';

export function Topbar() {
  const { user, logout } = useAuthStore();
  const router = useRouter();
  const { t } = useTranslation();

  const initials = (user?.full_name || user?.username || '?')
    .split(' ')
    .map(s => s[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

  return (
    <header className="sticky top-0 z-30 h-16 border-b border-border bg-background/80 glass">
      <div className="flex h-full items-center gap-3 px-4 sm:px-6 lg:px-8">
        <div className="relative hidden md:block flex-1 max-w-md">
          <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="search"
            placeholder={t('nav.search') || 'Buscar...'}
            className="w-full rounded-lg border border-border bg-muted/40 pl-9 pr-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
          />
        </div>

        <div className="ml-auto flex items-center gap-2">
          <LanguageSwitcher />
          <ThemeToggle />
          <div className="mx-1 h-6 w-px bg-border" />
          <div className="flex items-center gap-2 pr-1">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-brand text-white text-xs font-semibold shadow-soft">
              {initials}
            </div>
            <div className="hidden sm:flex flex-col leading-tight">
              <span className="text-sm font-medium">{user?.full_name || user?.username}</span>
              <span className="text-[11px] text-muted-foreground capitalize">{user?.role}</span>
            </div>
          </div>
          <button
            onClick={() => { logout(); router.push('/login'); }}
            aria-label={t('nav.logout') || 'Cerrar sesión'}
            title={t('nav.logout') || 'Cerrar sesión'}
            className="inline-flex items-center justify-center w-9 h-9 rounded-lg border border-border bg-card text-muted-foreground hover:text-danger-600 hover:border-danger-500/40 hover:bg-danger-50 dark:hover:bg-danger-500/10 transition-colors"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
