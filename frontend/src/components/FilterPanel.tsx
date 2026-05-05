'use client';

import { useState, useEffect } from 'react';
import {
  Filter,
  ChevronDown,
  ChevronUp,
  RotateCcw,
  AlertTriangle,
  Activity,
  Calendar,
  Gauge,
  Layers,
  MapPin,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type {
  IncidentFilters,
  SeverityLevel,
  IncidentStatus,
  POILayerFilters,
  POILayerCategory,
} from '@/types';
import { zonesService } from '@/services/zonesService';
import type { Zone } from '@/services/zonesService';
import { SeverityLevel as SeverityEnum, IncidentStatus as StatusEnum } from '@/types';
import { getSeverityLabel, getStatusLabel, getSeverityColor, getStatusColor } from '@/utils';

interface FilterPanelProps {
  filters: IncidentFilters;
  onChange: (filters: Partial<IncidentFilters>) => void;
  onClear: () => void;
  total?: number;
  layout?: 'horizontal' | 'sidebar';
  poiLayerFilters?: POILayerFilters;
  onPoiLayerFiltersChange?: (filters: POILayerFilters) => void;
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
    <div className="border-b border-border last:border-b-0">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-4 py-3 text-sm font-medium text-foreground hover:bg-muted transition-colors"
      >
        <span className="flex items-center gap-2">
          {icon}
          {title}
        </span>
        {open ? (
          <ChevronUp className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
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
  StatusEnum.EN_PROGRESO,
  StatusEnum.COMPLETADO,
  StatusEnum.VERIFICADO,
  StatusEnum.CERRADO,
];

const POI_CATEGORY_I18N: Record<POILayerCategory, string> = {
  school: 'filters.poi.school',
  hospital: 'filters.poi.hospital',
  fire_station: 'filters.poi.fire_station',
  community_center: 'filters.poi.community_center',
};

export function FilterPanel({
  filters,
  onChange,
  onClear,
  total,
  layout = 'sidebar',
  poiLayerFilters,
  onPoiLayerFiltersChange,
}: FilterPanelProps) {
  const { t } = useTranslation();

  const activeCount = [
    filters.severity,
    filters.status,
    filters.damage_class,
    filters.zone_id,
    filters.date_from ?? filters.date_to,
    filters.priority_min != null || filters.priority_max != null ? true : undefined,
  ].filter((v) => v !== undefined && v !== null && v !== '').length;

  const isHorizontal = layout === 'horizontal';

  const updatePoiLayerFilters = (changes: Partial<POILayerFilters>) => {
    if (!poiLayerFilters || !onPoiLayerFiltersChange) return;
    onPoiLayerFiltersChange({ ...poiLayerFilters, ...changes });
  };

  const updatePoiCategory = (category: POILayerCategory, enabled: boolean) => {
    if (!poiLayerFilters || !onPoiLayerFiltersChange) return;
    onPoiLayerFiltersChange({
      ...poiLayerFilters,
      categories: {
        ...poiLayerFilters.categories,
        [category]: enabled,
      },
    });
  };

  const priorityPresets = [
    { label: t('filters.presets.critical'), min: 80, max: undefined },
    { label: t('filters.presets.high'), min: 60, max: 80 },
    { label: t('filters.presets.medium'), min: 40, max: 60 },
    { label: t('filters.presets.low'), min: undefined, max: 40 },
  ];

  const datePresets = [
    { label: t('filters.quick.today'), days: 0 },
    { label: t('filters.quick.days7'), days: 7 },
    { label: t('filters.quick.days30'), days: 30 },
    { label: t('filters.quick.days90'), days: 90 },
  ];

  const [zones, setZones] = useState<Zone[]>([]);
  useEffect(() => {
    zonesService.getZones().then(setZones).catch(() => setZones([]));
  }, []);

  return (
    <div
      className={
        isHorizontal
          ? 'rounded-xl border border-border bg-card shadow-soft'
          : 'rounded-xl border border-border bg-card shadow-soft w-72 flex-shrink-0'
      }
    >
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-primary-600" />
          <span className="text-sm font-semibold text-foreground">{t('filters.title')}</span>
          {activeCount > 0 && (
            <span className="inline-flex items-center justify-center h-5 min-w-[20px] px-1.5 text-xs font-bold text-white bg-primary-600 rounded-full">
              {activeCount}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {total !== undefined && (
            <span className="text-xs text-muted-foreground">{t('filters.results', { count: total })}</span>
          )}
          {activeCount > 0 && (
            <button
              type="button"
              onClick={onClear}
              className="flex items-center gap-1 text-xs text-muted-foreground hover:text-danger-600 transition-colors"
              title={t('filters.clear')}
            >
              <RotateCcw className="h-3 w-3" />
              {t('filters.clear')}
            </button>
          )}
        </div>
      </div>

      <div className={isHorizontal ? 'grid grid-cols-4 divide-x divide-gray-100' : ''}>
        <FilterSection
          title={t('filters.severity')}
          icon={<AlertTriangle className="h-4 w-4 text-warning-500" />}
          defaultOpen={false}
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
                  className="h-3.5 w-3.5 text-primary-600 border-border focus:ring-primary-500"
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

        <FilterSection
          title={t('filters.priorityScore')}
          icon={<Gauge className="h-4 w-4 text-primary-500" />}
          defaultOpen={false}
        >
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <div className="flex-1">
                <label className="block text-xs text-muted-foreground mb-1">{t('filters.min')}</label>
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
                  className="w-full rounded-md border border-border px-2 py-1.5 text-sm focus:border-primary-500 focus:ring-1 focus:ring-primary-500 focus:outline-none"
                />
              </div>
              <span className="text-muted-foreground pt-5">-</span>
              <div className="flex-1">
                <label className="block text-xs text-muted-foreground mb-1">{t('filters.max')}</label>
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
                  className="w-full rounded-md border border-border px-2 py-1.5 text-sm focus:border-primary-500 focus:ring-1 focus:ring-primary-500 focus:outline-none"
                />
              </div>
            </div>

            <div className="flex flex-wrap gap-1">
              {priorityPresets.map((preset) => {
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
                        ? 'bg-primary-500/10 border-primary-500/40 text-primary-700 dark:text-primary-300 font-medium'
                        : 'border-border text-muted-foreground hover:bg-muted'
                    }`}
                  >
                    {preset.label}
                  </button>
                );
              })}
            </div>
          </div>
        </FilterSection>

        <FilterSection
          title={t('filters.status')}
          icon={<Activity className="h-4 w-4 text-success-500" />}
          defaultOpen={false}
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
                  className="h-3.5 w-3.5 text-primary-600 border-border focus:ring-primary-500"
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

        <FilterSection
          title={t('filters.poiLayers')}
          icon={<Layers className="h-4 w-4 text-indigo-500" />}
          defaultOpen={false}
        >
          <div className="space-y-3">
            <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
              <input
                type="checkbox"
                checked={poiLayerFilters?.showPOIs ?? false}
                onChange={(e) => {
                  const enabled = e.target.checked;
                  updatePoiLayerFilters({
                    showPOIs: enabled,
                    showRiskBuffers: enabled ? (poiLayerFilters?.showRiskBuffers ?? false) : false,
                  });
                }}
                className="h-4 w-4 text-primary-600 border-border rounded focus:ring-primary-500"
              />
              {t('filters.showPoiLayer')}
            </label>

            <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
              <input
                type="checkbox"
                checked={poiLayerFilters?.showRiskBuffers ?? false}
                disabled={!(poiLayerFilters?.showPOIs ?? false)}
                onChange={(e) => updatePoiLayerFilters({ showRiskBuffers: e.target.checked })}
                className="h-4 w-4 text-primary-600 border-border rounded focus:ring-primary-500 disabled:opacity-50"
              />
              {t('filters.showRiskZones')}
            </label>

            <div>
              <p className="text-xs text-muted-foreground mb-1">{t('filters.poiCategories')}</p>
              <div className="grid grid-cols-2 gap-1.5">
                {(Object.keys(POI_CATEGORY_I18N) as POILayerCategory[]).map((category) => (
                  <label
                    key={category}
                    className="flex items-center gap-2 text-xs text-foreground cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={poiLayerFilters?.categories?.[category] ?? false}
                      disabled={!(poiLayerFilters?.showPOIs ?? false)}
                      onChange={(e) => updatePoiCategory(category, e.target.checked)}
                      className="h-3.5 w-3.5 text-primary-600 border-border rounded focus:ring-primary-500 disabled:opacity-50"
                    />
                    {t(POI_CATEGORY_I18N[category])}
                  </label>
                ))}
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
                <span>{t('filters.bufferRadius')}</span>
                <span>{poiLayerFilters?.bufferRadiusMeters ?? 120} m</span>
              </div>
              <input
                type="range"
                min={50}
                max={200}
                step={10}
                value={poiLayerFilters?.bufferRadiusMeters ?? 120}
                disabled={!(poiLayerFilters?.showPOIs ?? false)}
                onChange={(e) =>
                  updatePoiLayerFilters({ bufferRadiusMeters: Number(e.target.value) })
                }
                className="w-full accent-primary-600 disabled:opacity-50"
              />
            </div>
          </div>
        </FilterSection>

        {zones.length > 0 && (
          <FilterSection
            title={t('filters.zone')}
            icon={<MapPin className="h-4 w-4 text-emerald-500" />}
            defaultOpen={false}
          >
            <div className="space-y-1.5">
              <select
                value={filters.zone_id ?? ''}
                onChange={(e) =>
                  onChange({ zone_id: e.target.value ? Number(e.target.value) : undefined })
                }
                className="w-full rounded-md border border-border px-2 py-1.5 text-sm focus:border-primary-500 focus:ring-1 focus:ring-primary-500 focus:outline-none bg-background"
              >
                <option value="">{t('filters.allZones')}</option>
                {zones.map((z) => (
                  <option key={z.id} value={z.id}>
                    {z.name}
                  </option>
                ))}
              </select>
            </div>
          </FilterSection>
        )}

        <FilterSection
          title={t('filters.dateRange')}
          icon={<Calendar className="h-4 w-4 text-muted-foreground" />}
          defaultOpen={false}
        >
          <div className="space-y-2">
            <div>
              <label className="block text-xs text-muted-foreground mb-1">{t('filters.from')}</label>
              <input
                type="date"
                value={filters.date_from ?? ''}
                onChange={(e) =>
                  onChange({ date_from: e.target.value || undefined })
                }
                className="w-full rounded-md border border-border px-2 py-1.5 text-sm focus:border-primary-500 focus:ring-1 focus:ring-primary-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs text-muted-foreground mb-1">{t('filters.to')}</label>
              <input
                type="date"
                value={filters.date_to ?? ''}
                onChange={(e) =>
                  onChange({ date_to: e.target.value || undefined })
                }
                className="w-full rounded-md border border-border px-2 py-1.5 text-sm focus:border-primary-500 focus:ring-1 focus:ring-primary-500 focus:outline-none"
              />
            </div>

            <div className="flex flex-wrap gap-1">
              {datePresets.map((preset) => (
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
                  className="px-2 py-1 text-xs rounded-md border border-border text-muted-foreground hover:bg-muted transition-colors"
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
