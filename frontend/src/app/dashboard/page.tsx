'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useTranslation } from 'react-i18next';
import {
  PlusCircle,
  List,
  Activity,
  CheckCircle2,
  Clock,
  AlertTriangle,
  BarChart3,
  Target,
  TrendingUp,
  RefreshCw,
  Users,
  LogOut,
  FileText,
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
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store';
import { incidentsService } from '@/services/incidentsService';
import { UserRole } from '@/types';

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
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 flex items-start gap-4">
      <div className={`p-3 rounded-lg ${color}`}>
        <Icon className="w-5 h-5 text-white" />
      </div>
      <div className="min-w-0">
        <p className="text-sm text-gray-500 font-medium">{title}</p>
        {loading ? (
          <div className="h-7 w-16 bg-gray-200 animate-pulse rounded mt-1" />
        ) : (
          <p className="text-2xl font-bold text-gray-900 leading-tight">{value}</p>
        )}
        {subtitle && <p className="text-xs text-gray-400 mt-0.5">{subtitle}</p>}
      </div>
    </div>
  );
}

function SLABar({ pct, loading, t }: { pct: number | null; loading: boolean; t: (key: string) => string }) {
  const val = pct ?? 0;
  const color = val >= 80 ? 'bg-green-500' : val >= 60 ? 'bg-yellow-500' : 'bg-red-500';
  return (
    <div>
      <div className="flex justify-between text-xs text-gray-500 mb-1">
        <span>{t('dashboard.sla.compliance')}</span>
        <span className="font-semibold">{loading || pct == null ? '—' : `${val}%`}</span>
      </div>
      <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
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
  const { user, logout } = useAuthStore();
  const router = useRouter();
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{t('dashboard.title')}</h1>
          <p className="mt-1 text-gray-500 text-sm">
            {t('dashboard.welcome', { name: user?.full_name || user?.username })}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchStats}
            disabled={loading}
            className="inline-flex items-center gap-2 px-3 py-2 border border-gray-200 hover:bg-gray-50 text-gray-600 text-sm rounded-lg transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            {t('nav.refresh')}
          </button>
          <Link
            href="/dashboard/incidents"
            className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 hover:bg-gray-50 text-gray-700 text-sm font-medium rounded-lg transition-colors"
          >
            <List className="w-4 h-4" />
            {t('nav.viewIncidents')}
          </Link>
          <Link
            href="/dashboard/reports"
            className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 hover:bg-gray-50 text-gray-700 text-sm font-medium rounded-lg transition-colors"
          >
            <FileText className="w-4 h-4" />
            {t('nav.viewReports')}
          </Link>
          {(user?.role === UserRole.ADMIN || user?.role === UserRole.SUPERVISOR) && (
            <Link
              href="/dashboard/users"
              className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 hover:bg-gray-50 text-gray-700 text-sm font-medium rounded-lg transition-colors"
            >
              <Users className="w-4 h-4" />
              {t('nav.users')}
            </Link>
          )}
          <Link
            href="/dashboard/reports/new"
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
          >
            <PlusCircle className="w-4 h-4" />
            {t('nav.createReport')}
          </Link>
          <button
            onClick={() => { logout(); router.push('/auth/login'); }}
            aria-label={t('nav.logout')}
            className="inline-flex items-center gap-2 px-3 py-2 border border-red-200 hover:bg-red-50 text-red-600 text-sm rounded-lg transition-colors"
          >
            <LogOut className="w-4 h-4" />
            {t('nav.logout')}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
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
          title={t('dashboard.kpi.unassigned')}
          value={stats ? String(stats.pending_assignment) : '—'}
          subtitle={t('dashboard.kpi.unassignedSubtitle')}
          icon={AlertTriangle}
          color="bg-red-500"
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
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="w-5 h-5 text-gray-600" />
          <h2 className="text-base font-semibold text-gray-900">{t('dashboard.sla.title')}</h2>
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <SLABar pct={stats?.sla_compliance_pct ?? null} loading={loading} t={t} />
          <div>
            <div className="flex justify-between text-xs text-gray-500 mb-1">
              <span>{t('dashboard.sla.avgResolution')}</span>
              <span className="font-semibold">
                {loading || !stats?.avg_resolution_hours
                  ? '—'
                  : `${fmt(stats.avg_resolution_hours)}h`}
              </span>
            </div>
            <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
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
        <div className="col-span-2 bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <h2 className="text-base font-semibold text-gray-900 mb-4">{t('dashboard.charts.byStatus')}</h2>
          {loading ? (
            <div className="h-56 bg-gray-50 animate-pulse rounded-lg" />
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={statusChartData} barSize={28}>
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip
                  formatter={(v: number) => [v, t('dashboard.charts.incidents')]}
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
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <h2 className="text-base font-semibold text-gray-900 mb-4">{t('dashboard.charts.activeVsResolved')}</h2>
          {loading ? (
            <div className="h-56 bg-gray-50 animate-pulse rounded-lg" />
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
                <Tooltip formatter={(v: number) => [v, t('dashboard.charts.incidents')]} contentStyle={{ fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Priority breakdown */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
        <h2 className="text-base font-semibold text-gray-900 mb-4">{t('dashboard.charts.byPriority')}</h2>
        {loading ? (
          <div className="h-44 bg-gray-50 animate-pulse rounded-lg" />
        ) : (
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={priorityChartData} layout="vertical" barSize={22}>
              <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="name" width={60} tick={{ fontSize: 11 }} />
              <Tooltip
                formatter={(v: number) => [v, t('dashboard.charts.incidents')]}
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

