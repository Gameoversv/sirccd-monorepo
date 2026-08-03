'use client';

import { useEffect, useState, useCallback } from 'react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import { useTranslation } from 'react-i18next';
import {
  Camera,
  MapPin,
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  FileText,
  AlertTriangle,
  Plus,
  ArrowRight,
  X,
} from 'lucide-react';
import { useAuthStore } from '@/store';
import apiClient from '@/services/api';

const PortalMap = dynamic(() => import('@/components/PortalMap'), { ssr: false });
const MiniMap = dynamic(() => import('@/components/MiniMap'), { ssr: false });

// ── Types ─────────────────────────────────────────────────────────────────────

interface ReportItem {
  id: number;
  user_id: number;
  latitude: number;
  longitude: number;
  address: string | null;
  city: string | null;
  province: string | null;
  damage_type: string;
  severity: string;
  confidence: number;
  image_url: string;
  status: string;
  description: string | null;
  created_at: string;
}

interface ReportsResponse {
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  items: ReportItem[];
}

// ── Config ────────────────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<string, { classes: string; icon: React.ElementType }> = {
  processing: {
    classes: 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300',
    icon: Clock,
  },
  pending: {
    classes: 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300',
    icon: Clock,
  },
  approved: {
    classes: 'bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-300',
    icon: CheckCircle2,
  },
  rejected: {
    classes: 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-300',
    icon: XCircle,
  },
};

const SEVERITY_COLORS: Record<string, string> = {
  baja: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300',
  media: 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300',
  alta: 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-300',
};

const PER_PAGE = 8;

// ── Helpers ───────────────────────────────────────────────────────────────────

function timeAgo(dateStr: string, lang: string): string {
  const diff = (Date.now() - new Date(dateStr).getTime()) / 1000;
  const isEn = lang.startsWith('en');
  if (diff < 60) return isEn ? 'just now' : 'hace un momento';
  if (diff < 3600) {
    const m = Math.floor(diff / 60);
    return isEn ? `${m}m ago` : `hace ${m} min`;
  }
  if (diff < 86400) {
    const h = Math.floor(diff / 3600);
    return isEn ? `${h}h ago` : `hace ${h}h`;
  }
  const d = Math.floor(diff / 86400);
  return isEn ? `${d}d ago` : `hace ${d} días`;
}

function mediaUrl(url: string): string {
  const base = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1').replace(
    /\/api\/v1\/?$/,
    ''
  );
  return url.startsWith('http') ? url : `${base}${url}`;
}

// ── Report Card ───────────────────────────────────────────────────────────────

function ReportCard({ report, onClick }: { report: ReportItem; onClick: () => void }) {
  const { t, i18n } = useTranslation();
  const lang = i18n.language || 'es';
  const statusCfg = STATUS_CONFIG[report.status] ?? STATUS_CONFIG.pending;
  const StatusIcon = statusCfg.icon;
  const location = [report.address, report.city].filter(Boolean).join(', ') || '—';

  return (
    <button
      onClick={onClick}
      className="w-full text-left bg-card border border-border rounded-xl overflow-hidden hover:shadow-md hover:border-primary-200 dark:hover:border-primary-800 transition-all duration-200 group"
    >
      <div className="flex items-stretch">
        <div className="w-24 sm:w-28 flex-shrink-0 overflow-hidden bg-muted min-h-[80px]">
          <img
            src={mediaUrl(report.image_url)}
            alt=""
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        </div>
        <div className="flex-1 px-4 py-3 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-1.5">
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-sm font-semibold capitalize text-foreground">
                {t(`portal.damage.${report.damage_type}`, { defaultValue: report.damage_type })}
              </span>
              <span
                className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${
                  SEVERITY_COLORS[report.severity] ?? ''
                }`}
              >
                {t(`portal.severity.${report.severity}`, { defaultValue: report.severity })}
              </span>
            </div>
            <span className="text-xs text-muted-foreground flex-shrink-0">#{report.id}</span>
          </div>
          <div className="flex items-center gap-1 text-xs text-muted-foreground mb-2 truncate">
            <MapPin className="w-3 h-3 flex-shrink-0" />
            <span className="truncate">{location}</span>
          </div>
          <div className="flex items-center justify-between">
            <span
              className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium ${statusCfg.classes}`}
            >
              <StatusIcon className="w-3 h-3" />
              {t(`portal.status.${report.status}`, { defaultValue: report.status })}
            </span>
            <span className="text-xs text-muted-foreground">
              {timeAgo(report.created_at, lang)}
            </span>
          </div>
        </div>
      </div>
    </button>
  );
}

// ── Detail Modal ──────────────────────────────────────────────────────────────

function ReportDetailModal({ report, onClose }: { report: ReportItem; onClose: () => void }) {
  const { t, i18n } = useTranslation();
  const lang = i18n.language || 'es';
  const isEn = lang.startsWith('en');
  const statusCfg = STATUS_CONFIG[report.status] ?? STATUS_CONFIG.pending;
  const StatusIcon = statusCfg.icon;

  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50 p-4"
      onMouseDown={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="w-full max-w-lg bg-card rounded-2xl shadow-2xl overflow-hidden max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-5 py-4 border-b border-border sticky top-0 bg-card z-10">
          <div>
            <h2 className="font-semibold text-foreground">
              {t(`portal.damage.${report.damage_type}`, { defaultValue: report.damage_type })} ·
              #{report.id}
            </h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              {new Date(report.created_at).toLocaleDateString(isEn ? 'en-US' : 'es-DO', {
                dateStyle: 'long',
              })}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-muted text-muted-foreground transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-5 space-y-4">
          <img
            src={mediaUrl(report.image_url)}
            alt=""
            className="w-full rounded-xl object-contain max-h-60 bg-muted"
          />

          <div className={`flex items-start gap-3 px-4 py-3 rounded-xl ${statusCfg.classes}`}>
            <StatusIcon className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-sm">
                {t(`portal.status.${report.status}`, { defaultValue: report.status })}
              </p>
              {(report.status === 'processing' || report.status === 'pending') && (
                <p className="text-xs opacity-80 mt-0.5">
                  {isEn
                    ? 'Our team is reviewing your report'
                    : 'Nuestro equipo está revisando tu reporte'}
                </p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="bg-muted/50 rounded-lg px-3 py-2.5">
              <p className="text-xs text-muted-foreground mb-0.5">
                {isEn ? 'Damage type' : 'Tipo de daño'}
              </p>
              <p className="text-sm font-medium capitalize">
                {t(`portal.damage.${report.damage_type}`, { defaultValue: report.damage_type })}
              </p>
            </div>
            <div className="bg-muted/50 rounded-lg px-3 py-2.5">
              <p className="text-xs text-muted-foreground mb-0.5">
                {isEn ? 'Severity' : 'Gravedad'}
              </p>
              <p className="text-sm font-medium">
                {t(`portal.severity.${report.severity}`, { defaultValue: report.severity })}
              </p>
            </div>
            <div className="col-span-2 bg-muted/50 rounded-lg px-3 py-2.5">
              <p className="text-xs text-muted-foreground mb-0.5">
                {isEn ? 'Location' : 'Ubicación'}
              </p>
              <p className="text-sm font-medium">
                {[report.address, report.city, report.province].filter(Boolean).join(', ') || '—'}
              </p>
            </div>
          </div>

          {report.description && (
            <div className="bg-muted/50 rounded-lg px-3 py-2.5">
              <p className="text-xs text-muted-foreground mb-0.5">
                {isEn ? 'Description' : 'Descripción'}
              </p>
              <p className="text-sm">{report.description}</p>
            </div>
          )}

          <div className="rounded-xl overflow-hidden border border-border">
            <MiniMap
              lat={report.latitude}
              lng={report.longitude}
              label={report.address || undefined}
              height="180px"
              zoom={16}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function PortalPage() {
  const { user } = useAuthStore();
  const { t, i18n } = useTranslation();
  const lang = i18n.language || 'es';

  const [reports, setReports] = useState<ReportItem[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<ReportItem | null>(null);

  const fetchReports = useCallback(
    async (p: number) => {
      if (p === 1) setLoading(true);
      else setLoadingMore(true);
      setError(null);
      try {
        const params = new URLSearchParams();
        params.set('page', String(p));
        params.set('per_page', String(PER_PAGE));
        const { data } = await apiClient.get<ReportsResponse>(`/reportes?${params.toString()}`);
        setReports((prev) => (p === 1 ? data.items : [...prev, ...data.items]));
        setTotal(data.total);
        setTotalPages(data.total_pages);
      } catch {
        setError(
          lang.startsWith('en')
            ? 'Could not load reports'
            : 'No se pudieron cargar los reportes'
        );
      } finally {
        setLoading(false);
        setLoadingMore(false);
      }
    },
    [lang]
  );

  useEffect(() => {
    fetchReports(1);
  }, [fetchReports]);

  const handleLoadMore = () => {
    const next = page + 1;
    setPage(next);
    fetchReports(next);
  };

  const inProgress = reports.filter(
    (r) => r.status === 'processing' || r.status === 'pending'
  ).length;
  const approved = reports.filter((r) => r.status === 'approved').length;
  const rejected = reports.filter((r) => r.status === 'rejected').length;

  const mapMarkers = reports
    .filter((r) => r.latitude && r.longitude)
    .map((r) => ({
      id: r.id,
      lat: r.latitude,
      lng: r.longitude,
      label: [r.address, r.city].filter(Boolean).join(', ') || undefined,
    }));

  const firstName = user?.full_name?.split(' ')[0] || user?.username || '';

  return (
    <div className="space-y-8">
      {/* Welcome */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-foreground">
          {t('portal.welcome', { name: firstName })}
        </h1>
        <p className="text-muted-foreground mt-1 text-sm">{t('portal.subtitle')}</p>
      </div>

      {/* CTA */}
      <Link
        href="/portal/nuevo"
        className="flex items-center gap-4 p-5 sm:p-6 bg-gradient-brand rounded-2xl text-white shadow-elevated hover:shadow-2xl hover:scale-[1.01] transition-all duration-200 group"
      >
        <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl bg-white/20 group-hover:bg-white/30 transition-colors">
          <Camera className="h-6 w-6" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-bold text-lg leading-tight">{t('portal.reportCta')}</p>
          <p className="text-white/80 text-sm mt-0.5">{t('portal.reportCtaHint')}</p>
        </div>
        <ArrowRight className="h-5 w-5 opacity-70 group-hover:translate-x-1 transition-transform flex-shrink-0" />
      </Link>

      {/* Stats */}
      {!loading && total > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            {
              label: t('portal.stats.total'),
              value: total,
              color: 'text-primary-600 dark:text-primary-400',
              bg: 'bg-primary-50 dark:bg-primary-500/10',
            },
            {
              label: t('portal.stats.inProgress'),
              value: inProgress,
              color: 'text-amber-600 dark:text-amber-400',
              bg: 'bg-amber-50 dark:bg-amber-500/10',
            },
            {
              label: t('portal.stats.approved'),
              value: approved,
              color: 'text-green-600 dark:text-green-400',
              bg: 'bg-green-50 dark:bg-green-500/10',
            },
            {
              label: t('portal.stats.rejected'),
              value: rejected,
              color: 'text-red-600 dark:text-red-400',
              bg: 'bg-red-50 dark:bg-red-500/10',
            },
          ].map((s) => (
            <div key={s.label} className={`rounded-xl px-4 py-3 ${s.bg}`}>
              <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
              <p className="text-xs text-muted-foreground mt-0.5">{s.label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Reports list */}
      <div>
        <h2 className="text-lg font-semibold text-foreground mb-3">{t('portal.myReports')}</h2>

        {error && (
          <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-red-50 dark:bg-red-500/10 text-red-700 dark:text-red-300 text-sm mb-3">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-16 text-muted-foreground gap-2">
            <Loader2 className="w-5 h-5 animate-spin" />
            <span className="text-sm">{t('portal.loading')}</span>
          </div>
        ) : reports.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-muted mb-4">
              <FileText className="w-8 h-8 text-muted-foreground" />
            </div>
            <p className="font-semibold text-foreground">{t('portal.noReports')}</p>
            <p className="text-sm text-muted-foreground mt-1 max-w-xs">
              {t('portal.noReportsHint')}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {reports.map((r) => (
              <ReportCard key={r.id} report={r} onClick={() => setSelected(r)} />
            ))}
            {page < totalPages && (
              <button
                onClick={handleLoadMore}
                disabled={loadingMore}
                className="w-full py-3 border border-border rounded-xl text-sm font-medium text-foreground hover:bg-muted transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loadingMore ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    <Plus className="w-4 h-4" />
                    {t('portal.loadMore')}
                  </>
                )}
              </button>
            )}
          </div>
        )}
      </div>

      {/* Map — always at the bottom */}
      {mapMarkers.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-foreground mb-3">{t('portal.mapTitle')}</h2>
          <div className="rounded-2xl overflow-hidden border border-border shadow-soft">
            <PortalMap markers={mapMarkers} height="320px" />
          </div>
        </div>
      )}

      {selected && <ReportDetailModal report={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}
