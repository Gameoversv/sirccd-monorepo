'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store';

export default function Home() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    // Redirect based on auth status
    if (isAuthenticated) {
      router.push('/dashboard');
    } else {
      router.push('/login');
    }
  }, [isAuthenticated, router]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900">SIRCCD</h1>
        <p className="mt-2 text-gray-600">Cargando...</p>
      </div>
    </div>
  );
}
