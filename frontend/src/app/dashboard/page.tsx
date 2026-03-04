'use client';

import { useAuthStore } from '@/store';

export default function DashboardPage() {
  const { user } = useAuthStore();

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900">
        Dashboard
      </h1>
      <p className="mt-2 text-gray-600">
        Bienvenido, {user?.full_name || user?.username}
      </p>

      <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {/* Placeholder cards */}
        <div className="rounded-lg bg-white p-6 shadow">
          <h3 className="text-lg font-semibold text-gray-900">Reportes</h3>
          <p className="mt-2 text-3xl font-bold text-primary-600">-</p>
        </div>

        <div className="rounded-lg bg-white p-6 shadow">
          <h3 className="text-lg font-semibold text-gray-900">Incidentes</h3>
          <p className="mt-2 text-3xl font-bold text-primary-600">-</p>
        </div>

        <div className="rounded-lg bg-white p-6 shadow">
          <h3 className="text-lg font-semibold text-gray-900">En progreso</h3>
          <p className="mt-2 text-3xl font-bold text-warning-600">-</p>
        </div>
      </div>

      <div className="mt-8 text-sm text-gray-500">
        <p>Frontend inicializado correctamente con:</p>
        <ul className="mt-2 list-disc pl-5">
          <li>Next.js 14 con App Router</li>
          <li>TypeScript</li>
          <li>Tailwind CSS</li>
          <li>Zustand (State Management)</li>
          <li>Axios (API Client)</li>
        </ul>
      </div>
    </div>
  );
}
