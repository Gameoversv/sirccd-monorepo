'use client';

import Link from 'next/link';
import { PlusCircle } from 'lucide-react';
import { useAuthStore } from '@/store';
import { MapView } from '@/components';

export default function DashboardPage() {
  const { user } = useAuthStore();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard Municipal</h1>
          <p className="mt-1 text-gray-600">
            Bienvenido, {user?.full_name || user?.username}
          </p>
        </div>
        <Link
          href="/dashboard/reports/new"
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
        >
          <PlusCircle className="w-4 h-4" />
          Crear Reporte
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
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

      {/* Map Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Mapa de Incidentes</h2>
            <p className="text-sm text-gray-600 mt-1">
              Visualización en tiempo real de reportes y su prioridad
            </p>
          </div>
        </div>
        
        <MapView height="600px" />
      </div>
    </div>
  );
}
