'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks';
import { useAuthStore } from '@/store';
import { UserRole } from '@/types';
import { Sidebar } from '@/components/Sidebar';
import { Topbar } from '@/components/Topbar';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  useAuth();
  const router = useRouter();
  const { user, hasHydrated } = useAuthStore();

  const isCitizen = user?.role === UserRole.CIUDADANO;

  useEffect(() => {
    // El panel es solo para staff: un ciudadano nunca debe ver el menú admin.
    if (hasHydrated && isCitizen) {
      router.replace('/portal');
    }
  }, [hasHydrated, isCitizen, router]);

  if (!hasHydrated || isCitizen) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <span className="h-2 w-2 rounded-full bg-primary-500 animate-pulse" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background bg-gradient-mesh">
      <Sidebar />
      <div className="lg:pl-64">
        <Topbar />
        <main className="px-4 py-6 sm:px-6 lg:px-8 animate-fade-in">
          <div className="mx-auto max-w-7xl">{children}</div>
        </main>
      </div>
    </div>
  );
}
