'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store';
import { UserRole } from '@/types';
import { PortalTopbar } from '@/components/PortalTopbar';

export default function PortalLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, isLoading, user } = useAuthStore();

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    if (user && user.role !== UserRole.CIUDADANO) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, isLoading, user, router]);

  if (!isAuthenticated || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <span className="h-2 w-2 rounded-full bg-primary-500 animate-pulse" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <PortalTopbar />
      <main className="max-w-4xl mx-auto px-4 py-8 sm:px-6 animate-fade-in">
        {children}
      </main>
    </div>
  );
}
