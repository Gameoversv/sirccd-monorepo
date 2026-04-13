'use client';

import { useAuth } from '@/hooks';
import { Sidebar } from '@/components/Sidebar';
import { Topbar } from '@/components/Topbar';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  useAuth();

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
