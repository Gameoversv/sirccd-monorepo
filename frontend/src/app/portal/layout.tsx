'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store';
import { UserRole } from '@/types';
import { PortalTopbar } from '@/components/PortalTopbar';
import { PortalSidebar, PortalTabs } from '@/components/PortalNav';

export default function PortalLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, user, hasHydrated } = useAuthStore();

  const isCitizen = user?.role === UserRole.CIUDADANO;

  useEffect(() => {
    // Sin rehidratar aún no se sabe si hay sesión: redirigir aquí expulsaría
    // al usuario a /login en cada refresco.
    if (!hasHydrated) return;
    if (!isAuthenticated) {
      router.replace('/login');
      return;
    }
    if (user && !isCitizen) {
      router.replace('/dashboard');
    }
  }, [hasHydrated, isAuthenticated, isCitizen, user, router]);

  if (!hasHydrated || !isAuthenticated || !user || !isCitizen) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <span className="h-2 w-2 rounded-full bg-primary-500 animate-pulse" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <PortalSidebar />
      <div className="lg:pl-60">
        <PortalTopbar />
        <PortalTabs />
        <main className="max-w-4xl mx-auto px-4 py-8 sm:px-6 animate-fade-in">
          {children}
        </main>
      </div>
    </div>
  );
}
