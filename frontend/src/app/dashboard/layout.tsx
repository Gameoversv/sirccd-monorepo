'use client';

import { useAuth } from '@/hooks';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  useAuth(); // Protect all dashboard routes

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Language toggle — fixed top-right */}
      <div className="fixed top-3 right-4 z-50">
        <LanguageSwitcher />
      </div>
      <main className="py-6">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          {children}
        </div>
      </main>
    </div>
  );
}
