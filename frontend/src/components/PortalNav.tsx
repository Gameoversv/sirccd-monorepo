'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTranslation } from 'react-i18next';
import { Home, PlusCircle, HelpCircle, ShieldCheck } from 'lucide-react';
import { cn } from '@/utils';

type PortalNavItem = {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
};

function usePortalNavItems(): PortalNavItem[] {
  const { t } = useTranslation();

  return [
    { href: '/portal', label: t('nav.home'), icon: Home },
    { href: '/portal/nuevo', label: t('nav.createReport'), icon: PlusCircle },
    { href: '/guia', label: t('guide.title'), icon: HelpCircle },
  ];
}

function isActive(pathname: string | null, href: string): boolean {
  if (href === '/portal') return pathname === '/portal';
  return pathname === href || Boolean(pathname?.startsWith(`${href}/`));
}

/** Navegación lateral del portal ciudadano (solo desde lg). */
export function PortalSidebar() {
  const pathname = usePathname();
  const items = usePortalNavItems();
  const { t } = useTranslation();

  return (
    <aside className="hidden lg:flex lg:fixed lg:inset-y-0 lg:left-0 lg:z-40 lg:w-60 lg:flex-col border-r border-border bg-card/60 glass">
      <div className="flex h-14 items-center gap-2 px-5 border-b border-border">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-brand text-white shadow-soft">
          <ShieldCheck className="h-4 w-4" />
        </div>
        <div className="flex flex-col leading-tight">
          <span className="text-sm font-semibold tracking-tight">SIRCCD</span>
          <span className="text-[10px] text-muted-foreground uppercase tracking-wider">
            Portal
          </span>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        {items.map(({ href, label, icon: Icon }) => {
          const active = isActive(pathname, href);
          return (
            <Link
              key={href}
              href={href}
              aria-current={active ? 'page' : undefined}
              className={cn(
                'group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                active
                  ? 'bg-primary-600/10 text-primary-700 dark:text-primary-300'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground',
              )}
            >
              <Icon
                className={cn(
                  'h-4 w-4 transition-transform group-hover:scale-110',
                  active && 'text-primary-600 dark:text-primary-400',
                )}
              />
              <span>{label}</span>
              {active && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-primary-600" />}
            </Link>
          );
        })}
      </nav>

      <div className="p-3 border-t border-border">
        <Link
          href="/portal/nuevo"
          className="flex items-center gap-2 rounded-lg bg-gradient-brand px-3 py-2.5 text-sm font-semibold text-white shadow-soft hover:shadow-elevated transition-shadow"
        >
          <PlusCircle className="h-4 w-4" />
          {t('nav.createReport')}
        </Link>
      </div>
    </aside>
  );
}

/** Barra de navegación del portal en pantallas pequeñas. */
export function PortalTabs() {
  const pathname = usePathname();
  const items = usePortalNavItems();

  return (
    <nav
      aria-label="Portal"
      className="lg:hidden sticky top-14 z-20 border-b border-border bg-background/80 backdrop-blur-sm"
    >
      <div className="max-w-4xl mx-auto flex items-center gap-1 px-2 sm:px-4 overflow-x-auto">
        {items.map(({ href, label, icon: Icon }) => {
          const active = isActive(pathname, href);
          return (
            <Link
              key={href}
              href={href}
              aria-current={active ? 'page' : undefined}
              className={cn(
                'flex items-center gap-2 whitespace-nowrap border-b-2 px-3 py-2.5 text-sm font-medium transition-colors',
                active
                  ? 'border-primary-600 text-primary-700 dark:text-primary-300'
                  : 'border-transparent text-muted-foreground hover:text-foreground',
              )}
            >
              <Icon className="h-4 w-4" />
              <span>{label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
