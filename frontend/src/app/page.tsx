'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ShieldCheck } from 'lucide-react';
import { useAuthStore } from '@/store';
import { UserRole } from '@/types';

export default function Home() {
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    router.push(user?.role === UserRole.CIUDADANO ? '/portal' : '/dashboard');
  }, [isAuthenticated, user, router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background bg-gradient-mesh">
      <div className="flex flex-col items-center gap-4 animate-fade-in">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-brand text-white shadow-elevated">
          <ShieldCheck className="h-7 w-7" />
        </div>
        <h1 className="text-3xl font-bold tracking-tight">SIRCCD</h1>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span className="h-2 w-2 rounded-full bg-primary-500 animate-pulse" />
          Cargando...
        </div>
      </div>
    </div>
  );
}
