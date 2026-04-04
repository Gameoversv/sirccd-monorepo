'use client';

import { useState, useCallback, useEffect, useMemo } from 'react';
import Link from 'next/link';
import { useTranslation } from 'react-i18next';
import {
  List,
  Map as MapIcon,
  Download,
  ChevronLeft,
  SlidersHorizontal,
} from 'lucide-react';
import dynamic from 'next/dynamic';
import { FilterPanel } from '@/components/FilterPanel';
import { IncidentsTable } from '@/components/IncidentsTable';
const MapView = dynamic(() => import('@/components/MapView').then(m => m.MapView), { ssr: false });
import { incidentsService } from '@/services';
import { useIncidentsStore } from '@/store';
import type {
  IncidentFilters,
  IncidentStatus,
  SeverityLevel,
  POILayerFilters,
} from '@/types';

type ViewMode = 'split' | 'table' | 'map';

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
  latitude?: number;
  longitude?: number;
}

export default function IncidentsPage() {
  const { filters, setFilters, clearFilters, pagination, setPage } =
    useIncidentsStore();
  const [view, setView] = useState<ViewMode>('split');
  const { t } = useTranslation();
  const [incidents, setIncidents] = useState<IncidentRow[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [sortField, setSortField] = useState<string>('created_at');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [showFilters, setShowFilters] = useState(true);
  const [poiLayerFilters, setPoiLayerFilters] = useState<POILayerFilters>({
    showPOIs: false,
    showRiskBuffers: false,
    bufferRadiusMeters: 120,
    categories: {
      school: true,
      hospital: true,
      fire_station: true,
      community_center: true,
    },
  });

  // Filters without priority_ fields for API
  const apiFilters: IncidentFilters = useMemo(() => {
    const f: IncidentFilters = {};
    if (filters.severity) f.severity = filters.severity;
    if (filters.status) f.status = filters.status;
    if (filters.date_from) f.date_from = filters.date_from;
    if (filters.date_to) f.date_to = filters.date_to;
    if (filters.damage_class) f.damage_class = filters.damage_class;
    return f;
  }, [filters.severity, filters.status, filters.date_from, filters.date_to, filters.damage_class]);

  // Fetch incidents for table
  const fetchIncidents = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await incidentsService.getIncidents(
        apiFilters,
        pagination.page,
        pagination.per_page
      );
      const data = (response as any).incidents || response.items || [];
      let rows: IncidentRow[] = data.map((inc: any) => ({
        id: inc.id,
        report_id: inc.report_id,
        address: inc.address,
        city: inc.city,
        damage_type: inc.damage_type,
        severity: inc.severity,
        priority: inc.priority,
        priority_score: inc.priority_score,
        status: inc.status,
        created_at: inc.created_at,
        latitude: inc.latitude,
        longitude: inc.longitude,
      }));

      // Client-side priority score filter
      if (filters.priority_min != null) {
        rows = rows.filter(
          (r) => (r.priority_score ?? 0) >= filters.priority_min!
        );
      }
      if (filters.priority_max != null) {
        rows = rows.filter(
          (r) => (r.priority_score ?? 0) <= filters.priority_max!
        );
      }

      // Client-side sort
      rows.sort((a: any, b: any) => {
        const va = a[sortField] ?? '';
        const vb = b[sortField] ?? '';
        const cmp = typeof va === 'number' ? va - vb : String(va).localeCompare(String(vb));
        return sortDir === 'asc' ? cmp : -cmp;
      });

      setIncidents(rows);
      setTotal((response as any).total || rows.length);
      setTotalPages(
        (response as any).total_pages ||
          Math.ceil(((response as any).total || rows.length) / pagination.per_page)
      );
    } catch (err) {
      console.error('Error fetching incidents:', err);
      setIncidents([]);
      setTotal(0);
      setTotalPages(0);
    } finally {
      setIsLoading(false);
    }
  }, [apiFilters, pagination.page, pagination.per_page, filters.priority_min, filters.priority_max, sortField, sortDir]);

  useEffect(() => {
    fetchIncidents();
  }, [fetchIncidents]);

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDir('desc');
    }
  };

  const handleExport = async () => {
    try {
      const blob = await incidentsService.exportIncidents({
        format: 'csv',
        filters: apiFilters,
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `incidentes_${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // silently fail
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex items-center gap-3">
          <Link
            href="/dashboard"
            className="p-1.5 rounded-md hover:bg-gray-100 transition-colors"
          >
            <ChevronLeft className="h-5 w-5 text-gray-500" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{t('incidents.title')}</h1>
            <p className="text-sm text-gray-500">
              {t('incidents.count', { count: total })}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Toggle filters */}
          <button
            type="button"
            onClick={() => setShowFilters(!showFilters)}
            className={`inline-flex items-center gap-1.5 px-3 py-2 text-sm rounded-lg border transition-colors ${
              showFilters
                ? 'bg-primary-50 border-primary-200 text-primary-700'
                : 'border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
          >
            <SlidersHorizontal className="h-4 w-4" />
            {t('incidents.filters')}
          </button>

          {/* View mode toggles */}
          <div className="flex rounded-lg border border-gray-300 overflow-hidden">
            {[
              { mode: 'split' as ViewMode, icon: <SlidersHorizontal className="h-4 w-4" />, label: t('incidents.split') },
              { mode: 'table' as ViewMode, icon: <List className="h-4 w-4" />, label: t('incidents.table') },
              { mode: 'map' as ViewMode, icon: <MapIcon className="h-4 w-4" />, label: t('incidents.map') },
            ].map(({ mode, icon, label }) => (
              <button
                key={mode}
                type="button"
                onClick={() => setView(mode)}
                className={`inline-flex items-center gap-1 px-3 py-2 text-sm transition-colors ${
                  view === mode
                    ? 'bg-primary-600 text-white'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
                title={label}
              >
                {icon}
                <span className="hidden sm:inline">{label}</span>
              </button>
            ))}
          </div>

          {/* Export */}
          <button
            type="button"
            onClick={handleExport}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <Download className="h-4 w-4" />
            <span className="hidden sm:inline">{t('incidents.export')}</span>
          </button>
        </div>
      </div>

      {/* Main content */}
      <div className="flex gap-4">
        {/* Filter panel */}
        {showFilters && (
          <FilterPanel
            filters={filters}
            onChange={setFilters}
            onClear={clearFilters}
            total={total}
            poiLayerFilters={poiLayerFilters}
            onPoiLayerFiltersChange={setPoiLayerFilters}
          />
        )}

        {/* Content area */}
        <div className="flex-1 min-w-0 space-y-4">
          {/* Map (shown in split and map view) */}
          {(view === 'split' || view === 'map') && (
            <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
              <h2 className="text-sm font-semibold text-gray-700 mb-2">
                {t('incidents.mapTitle')}
              </h2>
              <MapView
                height={view === 'map' ? '600px' : '350px'}
                filters={filters}
                poiLayerFilters={poiLayerFilters}
              />
            </div>
          )}

          {/* Table (shown in split and table view) */}
          {(view === 'split' || view === 'table') && (
            <IncidentsTable
              incidents={incidents}
              page={pagination.page}
              totalPages={totalPages}
              total={total}
              isLoading={isLoading}
              onPageChange={setPage}
              onSort={handleSort}
              sortField={sortField}
              sortDir={sortDir}
            />
          )}
        </div>
      </div>
    </div>
  );
}
