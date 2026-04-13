'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTranslation } from 'react-i18next';
import {
  LayoutDashboard,
  List,
  FileText,
  Users,
  Settings2,
  PlusCircle,
  ShieldCheck,
} from 'lucide-react';
import { useAuthStore } from '@/store';
import { UserRole } from '@/types';
import { cn } from '@/utils';

type Item = {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  roles?: UserRole[];
};

export function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuthStore();
  const { t } = useTranslation();

  const items: Item[] = [
    { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { href: '/dashboard/incidents', label: t('nav.viewIncidents') || 'Incidentes', icon: List },
    { href: '/dashboard/reports', label: t('nav.viewReports') || 'Reportes', icon: FileText },
    { href: '/dashboard/users', label: t('nav.users') || 'Usuarios', icon: Users, roles: [UserRole.ADMIN, UserRole.SUPERVISOR] },
    { href: '/dashboard/settings', label: 'Ajustes', icon: Settings2, roles: [UserRole.ADMIN] },
  ];

  const visible = items.filter(i => !i.roles || (user?.role && i.roles.includes(user.role)));

  return (
    <aside className="hidden lg:flex lg:fixed lg:inset-y-0 lg:left-0 lg:z-40 lg:w-64 lg:flex-col border-r border-border bg-card/60 glass">
      <div className="flex h-16 items-center gap-2 px-6 border-b border-border">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-brand text-white shadow-soft">
          <ShieldCheck className="h-5 w-5" />
        </div>
        <div className="flex flex-col leading-tight">
          <span className="text-sm font-semibold tracking-tight">SIRCCD</span>
          <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Panel</span>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        {visible.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || (href !== '/dashboard' && pathname?.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                'group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                active
                  ? 'bg-primary-600/10 text-primary-700 dark:text-primary-300'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground',
              )}
            >
              <Icon className={cn('h-4 w-4 transition-transform group-hover:scale-110', active && 'text-primary-600 dark:text-primary-400')} />
              <span>{label}</span>
              {active && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-primary-600" />}
            </Link>
          );
        })}
      </nav>

      <div className="p-3 border-t border-border">
        <Link
          href="/dashboard/reports/new"
          className="flex items-center gap-2 rounded-lg bg-gradient-brand px-3 py-2.5 text-sm font-semibold text-white shadow-soft hover:shadow-elevated transition-shadow"
        >
          <PlusCircle className="h-4 w-4" />
          {t('nav.createReport') || 'Nuevo reporte'}
        </Link>
      </div>
    </aside>
  );
}
