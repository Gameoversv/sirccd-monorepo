'use client';

import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Activity,
  CheckCircle2,
  Clock,
  BarChart3,
  Target,
  TrendingUp,
  RefreshCw,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';
import { useAuthStore } from '@/store';
import { incidentsService } from '@/services/incidentsService';

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

function fmt(value: number | null | undefined, digits = 1): string {
  if (value == null) return '—';
  return value.toFixed(digits);
}

// ── Sub-components ────────────────────────────────────────────────────────────
function KPICard({
  title,
  value,
  subtitle,
  icon: Icon,
  color,
  loading,
}: {
  title: string;
  value: string;
  subtitle?: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  loading: boolean;
}) {
  return (
    <div className="group relative overflow-hidden rounded-xl border border-border bg-card p-5 shadow-soft transition-all hover:shadow-elevated hover:-translate-y-0.5">
      <div className="flex items-start gap-4">
        <div className={`p-3 rounded-lg text-white shadow-sog ${color}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div className="min-w-0">
          <p className="text-xs uppercase tracking-wider text-muted-foreground font-medium">{title}</p>
          {loading ? (
            <div className="h-7 w-20 skeleton rounded mt-1.5" />
          ) : (
            <p className="text-2xl font-bold tracking-tight leading-tight mt-0.5">{value}</p>
          )}
          {subtitle && <p className="text-xs text-muted-foreground mt-0.5">{subtitle}</p>}
        </div>
      </div>
      <div className="pointer-events-none absolute -right-6 -bottom-6 h-24 w-24 rounded-full bg-gradient-to-br from-primary-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
    </div>
  );
}

function SLABar({ pct, loading, t }: { pct: number | null; loading: boolean; t: (key: string) => string }) {
  const val = pct ?? 0;
  const color = val >= 80 ? 'bg-green-500' : val >= 60 ? 'bg-yellow-500' : 'bg-red-500';
  return (
    <div>
      <div className="flex justify-between text-xs text-muted-foreground mb-1">
        <span>{t('dashboard.sla.compliance')}</span>
        <span className="font-semibold">{loading || pct == null ? '—' : `${val}%`}</span>
      </div>
      <div className="h-3 bg-muted rounded-full overflow-hidden">
        {!loading && pct != null && (
          <div
            className={`h-full rounded-full transition-all duration-700 ${color}`}
            style={{ width: `${Math.min(val, 100)}%` }}
          />
        )}
      </div>
    </div>
  );
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
  }, []);

  // Chart data derived from stats
  const statusChartData = stats
    ? Object.entries(stats.by_status).map(([key, count]) => ({
        name: t(`dashboard.statuses.${key}`) || key,
        value: count,
        fill: STATUS_COLORS[key] ?? '#6b7280',
      }))
    : [];

  const priorityChartData = stats
    ? Object.entries(stats.by_priority).map(([key, count]) => ({
        name: t(`dashboard.priorities.${key}`) || key,
        value: count,
        fill: PRIORITY_COLORS[key] ?? '#6b7280',
      }))
    : [];

  const activeResolvedData = stats
    ? [
        { name: t('dashboard.active'), value: stats.active_count, fill: '#3b82f6' },
        { name: t('dashboard.resolvedLabel'), value: stats.resolved_count, fill: '#22c55e' },
      ]
    : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{t('dashboard.title')}</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {t('dashboard.welcome', { name: user?.full_name || user?.username })}
          </p>
        </div>
        <button
          onClick={fetchStats}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-muted transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          {t('nav.refresh')}
        </button>
      </div>

      {error && (
        <div className="rounded-lg border border-danger-500/30 bg-danger-50 dark:bg-danger-500/10 text-danger-700 dark:text-danger-400 px-4 py-3 text-sm">
          {error}
        </div>
      )}

      {/* KPI cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6">
        <KPICard
          title={t('dashboard.kpi.total')}
          value={stats ? String(stats.total_incidents) : '—'}
          icon={BarChart3}
          color="bg-blue-500"
          loading={loading}
        />
        <KPICard
          title={t('dashboard.kpi.active')}
          value={stats ? String(stats.active_count) : '—'}
          subtitle={t('dashboard.kpi.activeSubtitle')}
          icon={Activity}
          color="bg-orange-500"
          loading={loading}
        />
        <KPICard
          title={t('dashboard.kpi.resolved')}
          value={stats ? String(stats.resolved_count) : '—'}
          subtitle={t('dashboard.kpi.resolvedSubtitle')}
          icon={CheckCircle2}
          color="bg-green-500"
          loading={loading}
        />
        <KPICard
          title={t('dashboard.kpi.ttr')}
          value={stats ? `${fmt(stats.avg_ttr_hours)}h` : '—'}
          subtitle={t('dashboard.kpi.ttrSubtitle')}
          icon={Clock}
          color="bg-violet-500"
          loading={loading}
        />
        <KPICard
          title={t('dashboard.kpi.avgScore')}
          value={stats ? fmt(stats.avg_priority_score) : '—'}
          subtitle={t('dashboard.kpi.avgScoreSubtitle')}
          icon={Target}
          color="bg-indigo-500"
          loading={loading}
        />
      </div>

      {/* SLA bar */}
      <div className="rounded-xl border border-border bg-card p-5 shadow-soft">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="w-5 h-5 text-muted-foreground" />
          <h2 className="text-base font-semibold tracking-tight">{t('dashboard.sla.title')}</h2>
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <SLABar pct={stats?.sla_compliance_pct ?? null} loading={loading} t={t} />
          <div>
            <div className="flex justify-between text-xs text-muted-foreground mb-1">
              <span>{t('dashboard.sla.avgResolution')}</span>
              <span className="font-semibold">
                {loading || !stats?.avg_resolution_hours
                  ? '—'
                  : `${fmt(stats.avg_resolution_hours)}h`}
              </span>
            </div>
            <div className="h-3 bg-muted rounded-full overflow-hidden">
              {!loading && stats?.avg_resolution_hours != null && (
                <div
                  className="h-full bg-indigo-400 rounded-full transition-all duration-700"
                  style={{
                    width: `${Math.max(0, Math.min(100, (1 - stats.avg_resolution_hours / 96) * 100))}%`,
                  }}
                />
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Incidents by status */}
        <div className="col-span-2 rounded-xl border border-border bg-card p-5 shadow-soft">
          <h2 className="text-base font-semibold tracking-tight mb-4">{t('dashboard.charts.byStatus')}</h2>
          {loading ? (
            <div className="h-56 skeleton rounded-lg" />
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={statusChartData} barSize={28}>
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip
                  formatter={(v: number | string | undefined) => [v ?? 0, t('dashboard.charts.incidents')]}
                  contentStyle={{ fontSize: 12 }}
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {statusChartData.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Active vs Resolved donut */}
        <div className="rounded-xl border border-border bg-card p-5 shadow-soft">
          <h2 className="text-base font-semibold tracking-tight mb-4">{t('dashboard.charts.activeVsResolved')}</h2>
          {loading ? (
            <div className="h-56 skeleton rounded-lg" />
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={activeResolvedData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="45%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={3}
                >
                  {activeResolvedData.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} />
                  ))}
                </Pie>
                <Legend iconSize={10} wrapperStyle={{ fontSize: 12 }} />
                <Tooltip formatter={(v: number | string | undefined) => [v ?? 0, t('dashboard.charts.incidents')]} contentStyle={{ fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Priority breakdown */}
      <div className="rounded-xl border border-border bg-card p-5 shadow-soft">
        <h2 className="text-base font-semibold tracking-tight mb-4">{t('dashboard.charts.byPriority')}</h2>
        {loading ? (
          <div className="h-44 skeleton rounded-lg" />
        ) : (
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={priorityChartData} layout="vertical" barSize={22}>
              <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="name" width={60} tick={{ fontSize: 11 }} />
              <Tooltip
                formatter={(v: number | string | undefined) => [v ?? 0, t('dashboard.charts.incidents')]}
                contentStyle={{ fontSize: 12 }}
              />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {priorityChartData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}

