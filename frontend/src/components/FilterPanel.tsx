'use client';

import { useState } from 'react';
import {
  Filter,
  X,
  ChevronDown,
  ChevronUp,
  RotateCcw,
  AlertTriangle,
  Activity,
  Calendar,
  Gauge,
} from 'lucide-react';
import type { IncidentFilters, SeverityLevel, IncidentStatus } from '@/types';
import { SeverityLevel as SeverityEnum, IncidentStatus as StatusEnum } from '@/types';
import { getSeverityLabel, getStatusLabel, getSeverityColor, getStatusColor } from '@/utils';

interface FilterPanelProps {
  filters: IncidentFilters;
  onChange: (filters: Partial<IncidentFilters>) => void;
  onClear: () => void;
  total?: number;
  layout?: 'horizontal' | 'sidebar';
}

interface SectionProps {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  defaultOpen?: boolean;
}

function FilterSection({ title, icon, children, defaultOpen = true }: SectionProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="border-b border-gray-100 last:border-b-0">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
      >
        <span className="flex items-center gap-2">
          {icon}
          {title}
        </span>
        {open ? (
          <ChevronUp className="h-4 w-4 text-gray-400" />
        ) : (
          <ChevronDown className="h-4 w-4 text-gray-400" />
        )}
      </button>
      {open && <div className="px-4 pb-3">{children}</div>}
    </div>
  );
}

const SEVERITIES: SeverityLevel[] = [
  SeverityEnum.ALTA,
  SeverityEnum.MEDIA,
  SeverityEnum.BAJA,
];

const STATUSES: IncidentStatus[] = [
  StatusEnum.REPORTADO,
  StatusEnum.ASIGNADO,
  StatusEnum.EN_PROGRESO,
  StatusEnum.COMPLETADO,
  StatusEnum.VERIFICADO,
  StatusEnum.CERRADO,
];

export function FilterPanel({
  filters,
  onChange,
  onClear,
  total,
  layout = 'sidebar',
}: FilterPanelProps) {
  const activeCount = Object.values(filters).filter(
    (v) => v !== undefined && v !== null && v !== ''
  ).length;

  const isHorizontal = layout === 'horizontal';

  return (
    <div
      className={
        isHorizontal
          ? 'bg-white rounded-lg shadow border border-gray-200'
          : 'bg-white rounded-lg shadow border border-gray-200 w-72 flex-shrink-0'
      }
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-primary-600" />
          <span className="text-sm font-semibold text-gray-900">Filtros</span>
          {activeCount > 0 && (
            <span className="inline-flex items-center justify-center h-5 min-w-[20px] px-1.5 text-xs font-bold text-white bg-primary-600 rounded-full">
              {activeCount}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {total !== undefined && (
            <span className="text-xs text-gray-500">{total} resultados</span>
          )}
          {activeCount > 0 && (
            <button
              type="button"
              onClick={onClear}
              className="flex items-center gap-1 text-xs text-gray-500 hover:text-danger-600 transition-colors"
              title="Limpiar filtros"
            >
              <RotateCcw className="h-3 w-3" />
              Limpiar
            </button>
          )}
        </div>
      </div>

      <div className={isHorizontal ? 'grid grid-cols-4 divide-x divide-gray-100' : ''}>
        {/* Severity */}
        <FilterSection
          title="Severidad"
          icon={<AlertTriangle className="h-4 w-4 text-warning-500" />}
        >
          <div className="space-y-1.5">
            {SEVERITIES.map((sev) => (
              <label
                key={sev}
                className="flex items-center gap-2 cursor-pointer group"
              >
                <input
                  type="radio"
                  name="severity"
                  checked={filters.severity === sev}
                  onChange={() =>
                    onChange({
                      severity: filters.severity === sev ? undefined : sev,
                    })
                  }
                  className="h-3.5 w-3.5 text-primary-600 border-gray-300 focus:ring-primary-500"
                />
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getSeverityColor(sev)} group-hover:ring-1 ring-gray-300 transition-shadow`}
                >
                  {getSeverityLabel(sev)}
                </span>
              </label>
            ))}
          </div>
        </FilterSection>

        {/* Priority Score */}
        <FilterSection
          title="Score de Prioridad"
          icon={<Gauge className="h-4 w-4 text-primary-500" />}
        >
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <div className="flex-1">
                <label className="block text-xs text-gray-500 mb-1">Mín</label>
                <input
                  type="number"
                  min={0}
                  max={100}
                  step={0.1}
                  placeholder="0"
                  value={filters.priority_min ?? ''}
                  onChange={(e) =>
                    onChange({
                      priority_min: e.target.value ? Number(e.target.value) : undefined,
                    })
                  }
                  className="w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm focus:border-primary-500 focus:ring-1 focus:ring-primary-500 focus:outline-none"
                />
              </div>
              <span className="text-gray-400 pt-5">–</span>
              <div className="flex-1">
                <label className="block text-xs text-gray-500 mb-1">Máx</label>
                <input
                  type="number"
                  min={0}
                  max={100}
                  step={0.1}
                  placeholder="100"
                  value={filters.priority_max ?? ''}
                  onChange={(e) =>
                    onChange({
                      priority_max: e.target.value ? Number(e.target.value) : undefined,
                    })
                  }
                  className="w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm focus:border-primary-500 focus:ring-1 focus:ring-primary-500 focus:outline-none"
                />
              </div>
            </div>
            {/* Quick-pick buttons */}
            <div className="flex flex-wrap gap-1">
              {[
                { label: 'Crítica (≥80)', min: 80, max: undefined },
                { label: 'Alta (60-80)', min: 60, max: 80 },
                { label: 'Media (40-60)', min: 40, max: 60 },
                { label: 'Baja (<40)', min: undefined, max: 40 },
              ].map((preset) => {
                const isActive =
                  filters.priority_min === preset.min &&
                  filters.priority_max === preset.max;
                return (
                  <button
                    key={preset.label}
                    type="button"
                    onClick={() =>
                      onChange(
                        isActive
                          ? { priority_min: undefined, priority_max: undefined }
                          : { priority_min: preset.min, priority_max: preset.max }
                      )
                    }
                    className={`px-2 py-1 text-xs rounded-md border transition-colors ${
                      isActive
                        ? 'bg-primary-50 border-primary-300 text-primary-700 font-medium'
                        : 'border-gray-200 text-gray-600 hover:bg-gray-50'
                    }`}
                  >
                    {preset.label}
                  </button>
                );
              })}
            </div>
          </div>
        </FilterSection>

        {/* Status */}
        <FilterSection
          title="Estado"
          icon={<Activity className="h-4 w-4 text-success-500" />}
        >
          <div className="space-y-1.5">
            {STATUSES.map((st) => (
              <label
                key={st}
                className="flex items-center gap-2 cursor-pointer group"
              >
                <input
                  type="radio"
                  name="status"
                  checked={filters.status === st}
                  onChange={() =>
                    onChange({
                      status: filters.status === st ? undefined : st,
                    })
                  }
                  className="h-3.5 w-3.5 text-primary-600 border-gray-300 focus:ring-primary-500"
                />
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getStatusColor(st)} group-hover:ring-1 ring-gray-300 transition-shadow`}
                >
                  {getStatusLabel(st)}
                </span>
              </label>
            ))}
          </div>
        </FilterSection>

        {/* Date Range */}
        <FilterSection
          title="Rango de Fechas"
          icon={<Calendar className="h-4 w-4 text-gray-500" />}
          defaultOpen={false}
        >
          <div className="space-y-2">
            <div>
              <label className="block text-xs text-gray-500 mb-1">Desde</label>
              <input
                type="date"
                value={filters.date_from ?? ''}
                onChange={(e) =>
                  onChange({ date_from: e.target.value || undefined })
                }
                className="w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm focus:border-primary-500 focus:ring-1 focus:ring-primary-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Hasta</label>
              <input
                type="date"
                value={filters.date_to ?? ''}
                onChange={(e) =>
                  onChange({ date_to: e.target.value || undefined })
                }
                className="w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm focus:border-primary-500 focus:ring-1 focus:ring-primary-500 focus:outline-none"
              />
            </div>
            {/* Quick-pick buttons */}
            <div className="flex flex-wrap gap-1">
              {[
                { label: 'Hoy', days: 0 },
                { label: '7 días', days: 7 },
                { label: '30 días', days: 30 },
                { label: '90 días', days: 90 },
              ].map((preset) => (
                <button
                  key={preset.label}
                  type="button"
                  onClick={() => {
                    const to = new Date();
                    const from = new Date();
                    from.setDate(from.getDate() - preset.days);
                    onChange({
                      date_from: from.toISOString().split('T')[0],
                      date_to: to.toISOString().split('T')[0],
                    });
                  }}
                  className="px-2 py-1 text-xs rounded-md border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
                >
                  {preset.label}
                </button>
              ))}
            </div>
          </div>
        </FilterSection>
      </div>
    </div>
  );
}
