'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import { useTranslation } from 'react-i18next';
import {
  Activity,
  ArrowUpRight,
  BarChart3,
  CheckCircle2,
  Clock,
  RefreshCw,
  Target,
} from 'lucide-react';
import { useAuthStore } from '@/store';
import { incidentsService } from '@/services/incidentsService';
import { HeroKpi, KpiTile } from '@/components/dashboard/KpiTiles';
import { SlaPanel } from '@/components/dashboard/SlaPanel';
import {
  ChartPanel,
  DonutChart,
  PriorityBarChart,
  StatusBarChart,
  type ChartDatum,
} from '@/components/dashboard/DashboardCharts';

const MapView = dynamic(() => import('@/components/MapView').then((m) => m.MapView), {
  ssr: false,
  loading: () => <div className="skeleton h-[460px] rounded-xl" />,
});

// ── Types ────────────────────────────────────────────────────────────────────
type Stats = Awaited<ReturnType<typeof incidentsService.getStats>>;

// ── Helpers ──────────────────────────────────────────────────────────────────
const STATUS_COLORS: Record<string, string> = {
  open: '#ef4444',
  assigned: '#f97316',
  in_progress: '#3b82f6',
  resolved: '#22c55e',
  verified: '#6366f1',
  closed: '#6b7280',
};

const PRIORITY_COLORS: Record<string, string> = {
  baja: '#22c55e',
  media: '#f59e0b',
  alta: '#ef4444',
  critica: '#7c3aed',
};

const DAMAGE_TYPE_COLORS: Record<string, string> = {
  bache: '#f97316',
  grieta: '#06b6d4',
};

function fmt(value: number | null | undefined, digits = 1): string {
  if (value == null) return '—';
  return value.toFixed(digits);
}

/** Convierte un mapa {clave: conteo} en series listas para recharts. */
function toChartData(
  counts: Record<string, number> | undefined,
  colors: Record<string, string>,
  label: (key: string) => string,
): ChartDatum[] {
  if (!counts) return [];
  return Object.entries(counts).map(([key, value]) => ({
    name: label(key),
    value,
    fill: colors[key] ?? '#6b7280',
  }));
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function DashboardPage() {
  const { user } = useAuthStore();
  const { t } = useTranslation();
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await incidentsService.getStats();
      setStats(data);
    } catch {
      setError(t('dashboard.statsError'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const statusChartData = toChartData(stats?.by_status, STATUS_COLORS, (k) =>
    t(`dashboard.statuses.${k}`, { defaultValue: k }),
  );

  const priorityChartData = toChartData(stats?.by_priority, PRIORITY_COLORS, (k) =>
    t(`dashboard.priorities.${k}`, { defaultValue: k }),
  );

  const damageTypeChartData = toChartData(stats?.by_damage_type, DAMAGE_TYPE_COLORS, (k) =>
    t(`dashboard.damageTypes.${k}`, { defaultValue: k }),
  );

  const activeResolvedData: ChartDatum[] = stats
    ? [
        { name: t('dashboard.active'), value: stats.active_count, fill: '#3b82f6' },
        { name: t('dashboard.resolvedLabel'), value: stats.resolved_count, fill: '#22c55e' },
      ]
    : [];

  const damageTotal = damageTypeChartData.reduce((sum, d) => sum + d.value, 0);
  const unitLabel = t('dashboard.charts.incidents');

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{t('dashboard.title')}</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {t('dashboard.welcome', { name: user?.full_name || user?.username })}
          </p>
        </div>
        <button
          onClick={fetchStats}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          {t('nav.refresh')}
        </button>
      </div>

      {error && (
        <div className="rounded-lg border border-danger-500/30 bg-danger-50 px-4 py-3 text-sm text-danger-700 dark:bg-danger-500/10 dark:text-danger-400">
          {error}
        </div>
      )}

      {/* Fila principal: el mapa domina, las métricas lo acompañan */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        <ChartPanel
          title={t('dashboard.map.title')}
          className="lg:col-span-8"
          action={
            <Link
              href="/dashboard/incidents"
              className="inline-flex items-center gap-1 text-xs font-medium text-primary-600 transition-colors hover:text-primary-700 dark:text-primary-400"
            >
              {t('dashboard.map.viewAll')}
              <ArrowUpRight className="h-3.5 w-3.5" />
            </Link>
          }
        >
          {/* MapView ya aporta su propio marco redondeado; envolverlo en otro
              borde duplicaría el contorno. */}
          <MapView height="460px" />
        </ChartPanel>

        <div className="grid grid-cols-2 gap-4 lg:col-span-4 lg:grid-cols-2">
          <div className="col-span-2">
            <HeroKpi
              label={t('dashboard.kpi.total')}
              value={stats ? String(stats.total_incidents) : '—'}
              hint={t('dashboard.kpi.totalHint')}
              icon={BarChart3}
              loading={loading}
            />
          </div>

          <KpiTile
            label={t('dashboard.kpi.active')}
            value={stats ? String(stats.active_count) : '—'}
            hint={t('dashboard.kpi.activeSubtitle')}
            icon={Activity}
            accent="bg-orange-500"
            loading={loading}
          />
          <KpiTile
            label={t('dashboard.kpi.resolved')}
            value={stats ? String(stats.resolved_count) : '—'}
            hint={t('dashboard.kpi.resolvedSubtitle')}
            icon={CheckCircle2}
            accent="bg-green-500"
            loading={loading}
          />
          <KpiTile
            label={t('dashboard.kpi.ttr')}
            value={stats ? `${fmt(stats.avg_ttr_hours)}h` : '—'}
            hint={t('dashboard.kpi.ttrSubtitle')}
            icon={Clock}
            accent="bg-violet-500"
            loading={loading}
          />
          <KpiTile
            label={t('dashboard.kpi.avgScore')}
            value={stats ? fmt(stats.avg_priority_score) : '—'}
            hint={t('dashboard.kpi.avgScoreSubtitle')}
            icon={Target}
            accent="bg-indigo-500"
            loading={loading}
          />

          <div className="col-span-2">
            <SlaPanel
              compliancePct={stats?.sla_compliance_pct ?? null}
              avgResolutionHours={stats?.avg_resolution_hours ?? null}
              loading={loading}
              labels={{
                title: t('dashboard.sla.title'),
                compliance: t('dashboard.sla.compliance'),
                avgResolution: t('dashboard.sla.avgResolution'),
              }}
            />
          </div>
        </div>
      </div>

      {/* Segunda fila: distribuciones */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        <ChartPanel title={t('dashboard.charts.byStatus')} className="lg:col-span-8">
          <StatusBarChart data={statusChartData} loading={loading} unitLabel={unitLabel} />
        </ChartPanel>

        <ChartPanel title={t('dashboard.charts.activeVsResolved')} className="lg:col-span-4">
          <DonutChart data={activeResolvedData} loading={loading} unitLabel={unitLabel} />
        </ChartPanel>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        <ChartPanel title={t('dashboard.charts.byPriority')} className="lg:col-span-7">
          <PriorityBarChart data={priorityChartData} loading={loading} unitLabel={unitLabel} />
        </ChartPanel>

        <ChartPanel title={t('dashboard.charts.byDamageType')} className="lg:col-span-5">
          <DonutChart
            data={damageTypeChartData}
            loading={loading}
            unitLabel={unitLabel}
            height={200}
            centerValue={loading ? undefined : String(damageTotal)}
            centerLabel={t('dashboard.charts.incidents')}
          />
        </ChartPanel>
      </div>
    </div>
  );
}
