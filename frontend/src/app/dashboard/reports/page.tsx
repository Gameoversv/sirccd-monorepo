'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import dynamic from 'next/dynamic';
import { useTranslation } from 'react-i18next';
import {
  FileText,
  ChevronLeft,
  ChevronRight,
  Search,
  CheckCircle,
  XCircle,
  Loader2,
  Eye,
  X,
  MapPin,
} from 'lucide-react';
import { useAuthStore } from '@/store';
import { UserRole } from '@/types';
import apiClient from '@/services/api';

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
  updated_at: string;
}

interface ReportsResponse {
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  items: ReportItem[];
}

// ── Constants ─────────────────────────────────────────────────────────────────

const STATUS_LABELS: Record<string, string> = {
  processing: 'Procesando',
  pending: 'Pendiente',
  approved: 'Aprobado',
  rejected: 'Rechazado',
};

const STATUS_COLORS: Record<string, string> = {
  processing: 'bg-yellow-100 text-yellow-700',
  pending: 'bg-blue-100 text-blue-700',
  approved: 'bg-green-100 text-green-700',
  rejected: 'bg-red-100 text-red-700',
};

const SEVERITY_LABELS: Record<string, string> = {
  baja: 'Baja',
  media: 'Media',
  alta: 'Alta',
};

const SEVERITY_COLORS: Record<string, string> = {
  baja: 'bg-green-100 text-green-700',
  media: 'bg-yellow-100 text-yellow-700',
  alta: 'bg-red-100 text-red-700',
};

const PER_PAGE = 15;

// ── Detail Modal ──────────────────────────────────────────────────────────────

function ReportDetailModal({
  report,
  onClose,
  canReview,
  onReviewed,
}: {
  report: ReportItem;
  onClose: () => void;
  canReview: boolean;
  onReviewed: () => void;
}) {
  const [reviewing, setReviewing] = useState(false);
  const [rejectionReason, setRejectionReason] = useState('');
  const [showReject, setShowReject] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { t } = useTranslation();

  const handleApprove = async () => {
    setReviewing(true);
    setError(null);
    try {
      await apiClient.patch(`/reportes/${report.id}/review`, {
        status: 'approved',
      });
      onReviewed();
    } catch (err: any) {
      setError(err?.detail ?? t('reports.detail.approveError'));
    } finally {
      setReviewing(false);
    }
  };

  const handleReject = async () => {
    setReviewing(true);
    setError(null);
    try {
      await apiClient.patch(`/reportes/${report.id}/review`, {
        status: 'rejected',
        rejection_reason: rejectionReason || undefined,
      });
      onReviewed();
    } catch (err: any) {
      setError(err?.detail ?? t('reports.detail.rejectError'));
    } finally {
      setReviewing(false);
    }
  };

  const mediaBase = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1').replace(/\/api\/v1\/?$/, '');
  const imgSrc = report.image_url.startsWith('http')
    ? report.image_url
    : `${mediaBase}${report.image_url}`;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 overflow-y-auto"
      onMouseDown={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="w-full max-w-2xl bg-white rounded-xl shadow-xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b sticky top-0 bg-white z-10">
          <h2 className="text-lg font-semibold text-gray-900">
            {t('reports.detail.title', { id: report.id })}
          </h2>
          <button onClick={onClose} className="p-1.5 rounded hover:bg-gray-100">
            <X className="w-4 h-4 text-gray-500" />
          </button>
        </div>

        <div className="px-6 py-5 space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-3 py-2 text-sm">
              {error}
            </div>
          )}

          {/* Image */}
          <img
            src={imgSrc}
            alt={`Reporte ${report.id}`}
            className="w-full rounded-lg object-cover max-h-72"
          />

          {/* Info grid */}
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-gray-500">{t('reports.detail.status')}</span>
              <div className="mt-0.5">
                <span className={`inline-block px-2 py-0.5 text-xs font-medium rounded-full ${STATUS_COLORS[report.status] ?? 'bg-gray-100 text-gray-700'}`}>
                  {t(`reports.status.${report.status}`) || report.status}
                </span>
              </div>
            </div>
            <div>
              <span className="text-gray-500">{t('reports.detail.severity')}</span>
              <div className="mt-0.5">
                <span className={`inline-block px-2 py-0.5 text-xs font-medium rounded-full ${SEVERITY_COLORS[report.severity] ?? 'bg-gray-100'}`}>
                  {t(`reports.severity.${report.severity}`) || report.severity}
                </span>
              </div>
            </div>
            <div>
              <span className="text-gray-500">{t('reports.detail.damageType')}</span>
              <p className="font-medium text-gray-900 capitalize">{report.damage_type}</p>
            </div>
            <div>
              <span className="text-gray-500">{t('reports.detail.mlConfidence')}</span>
              <p className="font-medium text-gray-900">{(report.confidence * 100).toFixed(0)}%</p>
            </div>
            <div className="col-span-2">
              <span className="text-gray-500">{t('reports.detail.address')}</span>
              <p className="font-medium text-gray-900">
                {[report.address, report.city, report.province].filter(Boolean).join(', ') || '—'}
              </p>
            </div>
            <div>
              <span className="text-gray-500">{t('reports.detail.created')}</span>
              <p className="font-medium text-gray-900">
                {new Date(report.created_at).toLocaleString('es-DO')}
              </p>
            </div>
            <div>
              <span className="text-gray-500">{t('reports.detail.userId')}</span>
              <p className="font-medium text-gray-900">{report.user_id}</p>
            </div>
          </div>

          {/* Description */}
          {report.description && (
            <div>
              <span className="text-sm text-gray-500">{t('reports.detail.description')}</span>
              <p className="text-sm text-gray-800 mt-0.5">{report.description}</p>
            </div>
          )}

          {/* Map */}
          <div className="rounded-lg overflow-hidden border border-gray-200">
            <MiniMap
              lat={report.latitude}
              lng={report.longitude}
              label={report.address || 'Ubicación del reporte'}
              height="180px"
              zoom={16}
            />
          </div>

          {/* Review actions */}
          {canReview && (report.status === 'processing' || report.status === 'pending') && (
            <div className="border-t pt-4 space-y-3">
              <p className="text-sm font-medium text-gray-700">{t('reports.detail.review')}</p>
              {showReject ? (
                <div className="space-y-2">
                  <textarea
                    rows={2}
                    placeholder={t('reports.detail.rejectionReason')}
                    value={rejectionReason}
                    onChange={(e) => setRejectionReason(e.target.value)}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-400 resize-none"
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={handleReject}
                      disabled={reviewing}
                      className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg disabled:opacity-50"
                    >
                      {reviewing && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                    {t('reports.detail.confirmReject')}
                    </button>
                    <button
                      onClick={() => setShowReject(false)}
                      className="px-4 py-2 border border-gray-200 text-sm rounded-lg hover:bg-gray-50"
                    >
                      Cancelar
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex gap-2">
                  <button
                    onClick={handleApprove}
                    disabled={reviewing}
                    className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg disabled:opacity-50"
                  >
                    {reviewing && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                    <CheckCircle className="w-4 h-4" />
                    {t('reports.detail.approve')}
                  </button>
                  <button
                    onClick={() => setShowReject(true)}
                    disabled={reviewing}
                    className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg disabled:opacity-50"
                  >
                    <XCircle className="w-4 h-4" />
                    {t('reports.detail.reject')}
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function ReportsPage() {
  const { user } = useAuthStore();
  const canReview =
    user?.role === UserRole.ADMIN || user?.role === UserRole.SUPERVISOR;
  const { t } = useTranslation();

  const [reports, setReports] = useState<ReportItem[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');

  // Detail modal
  const [selected, setSelected] = useState<ReportItem | null>(null);

  // Toast
  const [toast, setToast] = useState<{ msg: string; ok: boolean } | null>(null);
  const showToast = (msg: string, ok = true) => {
    setToast({ msg, ok });
    setTimeout(() => setToast(null), 3000);
  };

  const fetchReports = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      params.set('page', String(page));
      params.set('per_page', String(PER_PAGE));
      if (statusFilter) params.set('status', statusFilter);
      if (severityFilter) params.set('severity', severityFilter);
      if (search) params.set('search', search);

      const { data } = await apiClient.get<ReportsResponse>(
        `/reportes?${params.toString()}`
      );
      setReports(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch {
      setError(t('incidents.fetchError'));
    } finally {
      setLoading(false);
    }
  }, [page, search, statusFilter, severityFilter, t]);

  useEffect(() => {
    fetchReports();
  }, [fetchReports]);

  useEffect(() => {
    setPage(1);
  }, [search, statusFilter, severityFilter]);

  const fmtDate = (s: string) =>
    new Date(s).toLocaleDateString('es-DO', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });

  return (
    <div className="space-y-5">
      {/* Toast */}
      {toast && (
        <div
          className={`fixed bottom-5 right-5 z-50 px-4 py-3 rounded-lg text-sm font-medium shadow-lg ${
            toast.ok ? 'bg-green-600 text-white' : 'bg-red-600 text-white'
          }`}
        >
          {toast.msg}
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="/dashboard"
            className="p-1.5 rounded-md hover:bg-gray-100 transition-colors"
          >
            <ChevronLeft className="h-5 w-5 text-gray-500" />
          </Link>
          <div className="p-2 bg-blue-100 rounded-lg">
            <FileText className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Reportes</h1>
            <p className="text-sm text-gray-500">
              {total} reporte{total !== 1 ? 's' : ''} en el sistema
            </p>
          </div>
        </div>
        <Link
          href="/dashboard/reports/new"
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
        >
          {t('reports.newReport')}
        </Link>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            placeholder={t('reports.searchPlaceholder')}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">{t('reports.allStatuses')}</option>
          <option value="processing">{t('reports.status.processing')}</option>
          <option value="pending">{t('reports.status.pending')}</option>
          <option value="approved">{t('reports.status.approved')}</option>
          <option value="rejected">{t('reports.status.rejected')}</option>
        </select>
        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">{t('reports.allSeverities')}</option>
          <option value="baja">{t('reports.severity.baja')}</option>
          <option value="media">{t('reports.severity.media')}</option>
          <option value="alta">{t('reports.severity.alta')}</option>
        </select>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
          {error}
        </div>
      )}

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-100">
                {['ID', t('reports.columns.image'), t('reports.columns.type'), t('reports.columns.severity'), t('reports.columns.status'), t('reports.columns.city'), t('reports.columns.created'), ''].map(
                  (h) => (
                    <th
                      key={h}
                      className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider"
                    >
                      {h}
                    </th>
                  )
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-16 text-center text-gray-400">
                    <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2" />
                    {t('common.loading')}
                  </td>
                </tr>
              ) : reports.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-16 text-center text-gray-400">
                    {t('reports.noReports')}
                  </td>
                </tr>
              ) : (
                reports.map((r) => {
                  const mediaBase = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1').replace(/\/api\/v1\/?$/, '');
                  const imgSrc = r.image_url.startsWith('http')
                    ? r.image_url
                    : `${mediaBase}${r.image_url}`;
                  return (
                    <tr
                      key={r.id}
                      className="hover:bg-gray-50 cursor-pointer transition-colors"
                      onClick={() => setSelected(r)}
                    >
                      <td className="px-4 py-3 font-mono text-gray-600">
                        #{r.id}
                      </td>
                      <td className="px-4 py-3">
                        <img
                          src={imgSrc}
                          alt=""
                          className="w-12 h-12 object-cover rounded-md"
                        />
                      </td>
                      <td className="px-4 py-3 capitalize text-gray-800">
                        {r.damage_type}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                            SEVERITY_COLORS[r.severity] ?? 'bg-gray-100'
                          }`}
                        >
                          {t(`reports.severity.${r.severity}`) || r.severity}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                            STATUS_COLORS[r.status] ?? 'bg-gray-100 text-gray-700'
                          }`}
                        >
                          {t(`reports.status.${r.status}`) || r.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {r.city || '—'}
                      </td>
                      <td className="px-4 py-3 text-gray-500 whitespace-nowrap">
                        {fmtDate(r.created_at)}
                      </td>
                      <td className="px-4 py-3">
                        <button
                          title={t('reports.columns.viewDetail')}
                          className="p-1.5 rounded hover:bg-blue-50 text-blue-600 transition-colors"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelected(r);
                          }}
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100 bg-gray-50">
            <p className="text-xs text-gray-500">
              {t('common.showingRange', { from: (page - 1) * PER_PAGE + 1, to: Math.min(page * PER_PAGE, total), total })}
            </p>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                aria-label={t('common.prevPage')}
                className="p-1.5 rounded hover:bg-gray-200 disabled:opacity-40"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-xs text-gray-600 px-2">
                {t('common.page', { current: page, total: totalPages })}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                aria-label={t('common.nextPage')}
                className="p-1.5 rounded hover:bg-gray-200 disabled:opacity-40"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Detail modal */}
      {selected && (
        <ReportDetailModal
          report={selected}
          onClose={() => setSelected(null)}
          canReview={canReview}
          onReviewed={() => {
            setSelected(null);
            showToast(t('reports.updated'));
            fetchReports();
          }}
        />
      )}
    </div>
  );
}
