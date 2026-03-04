'use client';

import { useAuth } from '@/hooks';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  useAuth(); // Protect all dashboard routes

  return (
    <div className="min-h-screen bg-gray-50">
      {/* TODO: Add Sidebar and Header components */}
      <main className="py-6">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          {children}
        </div>
      </main>
    </div>
  );
}
