'use client';

import Link from 'next/link';
import {
  MapPin,
  AlertTriangle,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  Eye,
} from 'lucide-react';
import type { IncidentStatus, SeverityLevel } from '@/types';
import { getSeverityLabel, getStatusLabel, getSeverityColor, getStatusColor } from '@/utils';

interface IncidentRow {
  id: number;
  report_id: number;
  address?: string;
  city?: string;
  damage_type: string;
  severity: string;
  priority: string;
  priority_score?: number;
  status: string;
  created_at: string;
}

interface IncidentsTableProps {
  incidents: IncidentRow[];
  page: number;
  totalPages: number;
  total: number;
  isLoading: boolean;
  onPageChange: (page: number) => void;
  onSort?: (field: string) => void;
  sortField?: string;
  sortDir?: 'asc' | 'desc';
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('es-ES', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

function getPriorityBadge(priority: string, score?: number) {
  const colors: Record<string, string> = {
    critica: 'bg-red-100 text-red-800 dark:bg-red-500/20 dark:text-red-200',
    alta: 'bg-orange-100 text-orange-800 dark:bg-orange-500/20 dark:text-orange-200',
    media: 'bg-amber-100 text-amber-800 dark:bg-amber-500/20 dark:text-amber-200',
    baja: 'bg-blue-100 text-blue-800 dark:bg-blue-500/20 dark:text-blue-200',
  };
  const cls = colors[priority.toLowerCase()] || 'bg-gray-100 text-gray-700 dark:bg-gray-700/40 dark:text-gray-100';
  return (
    <div className="flex items-center gap-1.5">
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium capitalize ${cls}`}>
        {priority}
      </span>
      {score != null && score > 0 && (
        <span className="text-xs text-gray-500 font-mono">{score.toFixed(1)}</span>
      )}
    </div>
  );
}

export function IncidentsTable({
  incidents,
  page,
  totalPages,
  total,
  isLoading,
  onPageChange,
  onSort,
  sortField,
  sortDir,
}: IncidentsTableProps) {
  const SortHeader = ({
    field,
    children,
  }: {
    field: string;
    children: React.ReactNode;
  }) => (
    <th
      className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider cursor-pointer hover:text-foreground select-none transition-colors"
      onClick={() => onSort?.(field)}
    >
      <span className="inline-flex items-center gap-1">
        {children}
        <ArrowUpDown
          className={`h-3 w-3 ${sortField === field ? 'text-primary-600' : 'text-muted-foreground/40'}`}
        />
      </span>
    </th>
  );

  if (isLoading) {
    return (
      <div className="rounded-xl border border-border bg-card shadow-soft overflow-hidden">
        <div className="p-6 space-y-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-10 skeleton rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  if (incidents.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-card shadow-soft p-10 text-center">
        <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-muted">
          <AlertTriangle className="h-6 w-6 text-muted-foreground" />
        </div>
        <p className="text-sm font-medium">Sin resultados</p>
        <p className="mt-1 text-xs text-muted-foreground">
          No se encontraron incidentes con los filtros seleccionados.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-border bg-card shadow-soft overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-border">
          <thead className="bg-muted/40">
            <tr>
              <SortHeader field="id">ID</SortHeader>
              <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                Ubicación
              </th>
              <SortHeader field="severity">Severidad</SortHeader>
              <SortHeader field="priority_score">Prioridad</SortHeader>
              <SortHeader field="status">Estado</SortHeader>
              <SortHeader field="created_at">Fecha</SortHeader>
              <th className="px-4 py-3 text-right text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                Acciones
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {incidents.map((inc) => (
              <tr
                key={inc.id}
                className="hover:bg-muted/40 transition-colors"
              >
                <td className="px-4 py-3 text-sm font-semibold whitespace-nowrap">
                  <span className="font-mono text-xs text-muted-foreground">#</span>{inc.id}
                </td>
                <td className="px-4 py-3 text-sm">
                  <div className="flex items-start gap-1.5 max-w-[220px]">
                    <MapPin className="h-3.5 w-3.5 text-muted-foreground mt-0.5 flex-shrink-0" />
                    <span className="truncate">{inc.address || 'Sin dirección'}</span>
                  </div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium capitalize ${getSeverityColor(inc.severity as SeverityLevel)}`}
                  >
                    {getSeverityLabel(inc.severity as SeverityLevel)}
                  </span>
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  {getPriorityBadge(inc.priority, inc.priority_score)}
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getStatusColor(inc.status as IncidentStatus)}`}
                  >
                    {getStatusLabel(inc.status as IncidentStatus)}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-muted-foreground whitespace-nowrap">
                  {formatDate(inc.created_at)}
                </td>
                <td className="px-4 py-3 text-right whitespace-nowrap">
                  <Link
                    href={`/dashboard/incidents/${inc.id}`}
                    className="inline-flex items-center gap-1 rounded-md border border-border bg-card px-2 py-1 text-xs text-foreground hover:bg-muted hover:border-primary-500/40 hover:text-primary-600 font-medium transition-colors"
                  >
                    <Eye className="h-3.5 w-3.5" />
                    Ver
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between px-4 py-3 border-t border-border bg-muted/30">
        <p className="text-xs text-muted-foreground">
          Mostrando {(page - 1) * 20 + 1}–{Math.min(page * 20, total)} de{' '}
          <span className="font-semibold text-foreground">{total}</span> incidentes
        </p>
        <div className="flex items-center gap-1">
          <button
            type="button"
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
            className="p-1.5 rounded-md border border-border bg-card text-muted-foreground hover:text-foreground hover:bg-muted disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <span className="px-3 py-1 text-xs font-medium">
            {page} <span className="text-muted-foreground">/</span> {totalPages || 1}
          </span>
          <button
            type="button"
            disabled={page >= totalPages}
            onClick={() => onPageChange(page + 1)}
            className="p-1.5 rounded-md border border-border bg-card text-muted-foreground hover:text-foreground hover:bg-muted disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
