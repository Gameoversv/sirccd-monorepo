'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { useTranslation } from 'react-i18next';
import {
  ChevronLeft,
  MapPin,
  AlertTriangle,
  Gauge,
  Calendar,
  Image as ImageIcon,
  RefreshCw,
  Edit2,
  ExternalLink,
  Loader2,
  UserCheck,
  Clock,
} from 'lucide-react';
import { incidentsService } from '@/services';
import { StatusTimeline } from '@/components/StatusTimeline';
import { StatusUpdateModal } from '@/components/StatusUpdateModal';
import { useAuthStore } from '@/store';
import { useToast } from '@/hooks';
import type { IncidentDetail } from '@/types';
import { UserRole, STATUS_TRANSITIONS } from '@/types';
import {
  getSeverityLabel,
  getSeverityColor,
  getStatusLabel,
  getStatusColor,
  getPriorityLabel,
  getPriorityColor,
  getDamageClassLabel,
} from '@/utils';

import { MiniMap } from '@/components';

interface PageProps {
  params: { id: string };
}

function formatDate(ts: string | null): string {
  if (!ts) return '—';
  return new Date(ts).toLocaleString('es-ES', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function InfoRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 py-2.5 border-b border-gray-100 last:border-0">
      <span className="text-sm text-gray-500 flex-shrink-0">{label}</span>
      <span className="text-sm text-gray-900 text-right">{value}</span>
    </div>
  );
}

function PriorityBar({ score }: { score: number | null }) {
  const { t } = useTranslation();
  const pct = Math.min(100, Math.max(0, score ?? 0));
  const color =
    pct >= 80 ? 'bg-red-500' : pct >= 60 ? 'bg-orange-400' : pct >= 40 ? 'bg-amber-400' : 'bg-blue-400';

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>{t('incidents.detail.priorityScore')}</span>
        <span className="font-mono font-semibold text-gray-900">{pct.toFixed(1)} / 100</span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export default function IncidentDetailPage({ params }: PageProps) {
  const { user } = useAuthStore();
  const toast = useToast();
  const incidentId = Number(params.id);
  const { t } = useTranslation();

  const [incident, setIncident] = useState<IncidentDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [isRecalculating, setIsRecalculating] = useState(false);

  const canUpdateStatus =
    user?.role === UserRole.SUPERVISOR ||
    user?.role === UserRole.ADMIN ||
    user?.role === UserRole.BRIGADA;

  const hasNextStates =
    incident && (STATUS_TRANSITIONS[incident.status.toLowerCase()] || []).length > 0;

  const fetchIncident = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await incidentsService.getIncident(incidentId);
      setIncident(data);
    } catch (err: any) {
      setError(err?.detail || t('incidents.detail.loadError'));
    } finally {
      setIsLoading(false);
    }
  }, [incidentId, t]);

  useEffect(() => {
    fetchIncident();
  }, [fetchIncident]);

  const handleStatusUpdate = async (status: string, notes: string) => {
    await incidentsService.updateStatus(incidentId, status, notes || undefined);
  };

  const handleStatusSuccess = (newStatus: string) => {
    toast.success(`Estado actualizado a "${getStatusLabel(newStatus)}"`);
    fetchIncident();
  };

  const handleRecalculate = async () => {
    setIsRecalculating(true);
    try {
      await incidentsService.recalculatePriority(incidentId);
      toast.success(`${t('incidents.detail.priorityRecalculated')}`);
      fetchIncident();
    } catch {
      toast.error(t('incidents.detail.priorityError'));
    } finally {
      setIsRecalculating(false);
    }
  };

  // ── Loading state ──────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
      </div>
    );
  }

  if (error || !incident) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
        <AlertTriangle className="h-10 w-10 text-red-400" />
        <p className="text-gray-600">{error || t('incidents.detail.notFound')}</p>
        <Link
          href="/dashboard/incidents"
          className="text-sm text-primary-600 hover:underline"
        >
          {t('incidents.detail.backToList')}
        </Link>
      </div>
    );
  }

  // ── Main render ────────────────────────────────────────────
  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Breadcrumb / header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex items-center gap-3">
          <Link
            href="/dashboard/incidents"
            className="p-1.5 rounded-md hover:bg-gray-100 transition-colors"
          >
            <ChevronLeft className="h-5 w-5 text-gray-500" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {t('incidents.detail.title', { id: incident.id })}
            </h1>
            <p className="text-sm text-gray-500">
              {t('incidents.detail.reportRef', { id: incident.report_id })} · {formatDate(incident.created_at)}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {canUpdateStatus && hasNextStates && (
            <button
              type="button"
              onClick={() => setShowStatusModal(true)}
              className="inline-flex items-center gap-1.5 px-4 py-2 text-sm bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-medium transition-colors"
            >
              <Edit2 className="h-4 w-4" />
              {t('incidents.detail.updateStatus')}
            </button>
          )}
        </div>
      </div>

      {/* Content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ── Left / main column ─────────────────────────── */}
        <div className="lg:col-span-2 space-y-6">
          {/* Photo */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-2">
              <ImageIcon className="h-4 w-4 text-gray-500" />
              <h2 className="text-sm font-semibold text-gray-800">{t('incidents.detail.photo')}</h2>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 divide-x divide-gray-100">
              {/* Before */}
              <div className="p-4 space-y-2">
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">{t('incidents.detail.before')}</p>
                {incident.before_image_url ? (
                  <div className="relative">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={incident.before_image_url}
                      alt={t('incidents.detail.before')}
                      className="w-full h-52 object-cover rounded-lg"
                    />
                    <a
                      href={incident.before_image_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="absolute top-2 right-2 p-1.5 bg-white/80 rounded-md hover:bg-white shadow-sm"
                    >
                      <ExternalLink className="h-3.5 w-3.5 text-gray-600" />
                    </a>
                  </div>
                ) : (
                  <div className="h-52 rounded-lg bg-gray-50 border-2 border-dashed border-gray-200 flex items-center justify-center">
                    <div className="text-center text-gray-400">
                      <ImageIcon className="h-8 w-8 mx-auto" />
                      <p className="text-xs mt-1">{t('incidents.detail.noImage')}</p>
                    </div>
                  </div>
                )}
              </div>

              {/* After */}
              <div className="p-4 space-y-2">
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">{t('incidents.detail.after')}</p>
                {incident.after_image_url ? (
                  <div className="relative">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={incident.after_image_url}
                      alt={t('incidents.detail.after')}
                      className="w-full h-52 object-cover rounded-lg"
                    />
                    <a
                      href={incident.after_image_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="absolute top-2 right-2 p-1.5 bg-white/80 rounded-md hover:bg-white shadow-sm"
                    >
                      <ExternalLink className="h-3.5 w-3.5 text-gray-600" />
                    </a>
                  </div>
                ) : (
                  <div className="h-52 rounded-lg bg-gray-50 border-2 border-dashed border-gray-200 flex items-center justify-center">
                    <div className="text-center text-gray-400">
                      <ImageIcon className="h-8 w-8 mx-auto" />
                      <p className="text-xs mt-1">{t('incidents.detail.notAvailable')}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* AI Analysis + Location info */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200">
            <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
              <h2 className="text-sm font-semibold text-gray-800">{t('incidents.detail.analysis')}</h2>
            </div>
            <div className="px-5 py-2">
              <InfoRow
                label={t('incidents.detail.damageType')}
                value={
                  <span className="font-medium">
                    {getDamageClassLabel(incident.damage_type)}
                  </span>
                }
              />
              <InfoRow
                label={t('incidents.detail.severity')}
                value={
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getSeverityColor(incident.severity)}`}>
                    {getSeverityLabel(incident.severity)}
                  </span>
                }
              />
              <InfoRow
                label={t('incidents.detail.status')}
                value={
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getStatusColor(incident.status)}`}>
                    {getStatusLabel(incident.status)}
                  </span>
                }
              />
              <InfoRow
                label={t('incidents.detail.assignedBrigade')}
                value={
                  incident.assigned_brigade_id ? (
                    <span className="flex items-center gap-1">
                      <UserCheck className="h-3.5 w-3.5 text-blue-500" />
                      {t('incidents.detail.brigadeRef', { id: incident.assigned_brigade_id })}
                    </span>
                  ) : (
                    <span className="text-gray-400 italic">{t('incidents.detail.notAssigned')}</span>
                  )
                }
              />
              <InfoRow
                label={t('incidents.detail.estimatedTime')}
                value={
                  incident.estimated_repair_hours
                    ? `${incident.estimated_repair_hours}h`
                    : <span className="text-gray-400 italic">{t('incidents.detail.notEstimated')}</span>
                }
              />
            </div>
          </div>

          {/* Location + Mini Map */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200">
            <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-2">
              <MapPin className="h-4 w-4 text-red-500" />
              <h2 className="text-sm font-semibold text-gray-800">{t('incidents.detail.location')}</h2>
            </div>
            <div className="px-5 py-3 space-y-1">
              {incident.address && (
                <p className="text-sm text-gray-700">{incident.address}</p>
              )}
              <p className="text-xs text-gray-500">
                {[incident.city, incident.province].filter(Boolean).join(', ')}
              </p>
              {incident.latitude !== null && incident.longitude !== null && (
                <p className="text-xs text-gray-400 font-mono">
                  {incident.latitude.toFixed(6)}, {incident.longitude.toFixed(6)}
                </p>
              )}
            </div>
            {incident.latitude !== null && incident.longitude !== null && (
              <MiniMap
                lat={incident.latitude}
                lng={incident.longitude}
                label={incident.address || `#${incident.id}`}
              />
            )}
          </div>
        </div>

        {/* ── Right column ───────────────────────────────── */}
        <div className="space-y-6">
          {/* Priority card */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200">
            <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Gauge className="h-4 w-4 text-primary-500" />
                <h2 className="text-sm font-semibold text-gray-800">{t('incidents.detail.priority')}</h2>
              </div>
              {(user?.role === UserRole.SUPERVISOR || user?.role === UserRole.ADMIN) && (
                <button
                  type="button"
                  onClick={handleRecalculate}
                  disabled={isRecalculating}
                  className="p-1.5 rounded-md hover:bg-gray-100 transition-colors disabled:opacity-50"
                  title={t('incidents.detail.recalculate')}
                >
                  <RefreshCw className={`h-3.5 w-3.5 text-gray-500 ${isRecalculating ? 'animate-spin' : ''}`} />
                </button>
              )}
            </div>
            <div className="px-5 py-4 space-y-4">
              {/* Level badge */}
              <div className="flex items-center justify-center">
                <span
                  className={`text-2xl font-bold px-6 py-2 rounded-xl ${getPriorityColor(incident.priority)}`}
                >
                  {getPriorityLabel(incident.priority)}
                </span>
              </div>
              {/* Bar */}
              <PriorityBar score={incident.priority_score} />
            </div>
          </div>

          {/* Timestamps */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200">
            <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-2">
              <Calendar className="h-4 w-4 text-gray-400" />
              <h2 className="text-sm font-semibold text-gray-800">{t('incidents.detail.keyDates')}</h2>
            </div>
            <div className="px-5 py-2">
              <InfoRow label={t('incidents.detail.reported')} value={formatDate(incident.created_at)} />
              <InfoRow label={t('incidents.detail.assigned')} value={formatDate(incident.assigned_at)} />
              <InfoRow label={t('incidents.detail.started')} value={formatDate(incident.started_at)} />
              <InfoRow label={t('incidents.detail.completed')} value={formatDate(incident.completed_at)} />
              <InfoRow label={t('incidents.detail.verified')} value={formatDate(incident.verified_at)} />
            </div>
          </div>

          {/* Notes */}
          {incident.notes && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200">
              <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-2">
                <Clock className="h-4 w-4 text-gray-400" />
              <h2 className="text-sm font-semibold text-gray-800">{t('incidents.detail.internalNotes')}</h2>
              </div>
              <div className="px-5 py-3">
                <p className="text-xs text-gray-600 whitespace-pre-wrap leading-relaxed">
                  {incident.notes}
                </p>
              </div>
            </div>
          )}

          {/* Historial */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200">
            <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-2">
              <Clock className="h-4 w-4 text-primary-400" />
              <h2 className="text-sm font-semibold text-gray-800">{t('incidents.detail.changeHistory')}</h2>
            </div>
            <div className="px-5 py-4">
              <StatusTimeline incident={incident} />
            </div>
          </div>
        </div>
      </div>

      {/* Status update modal */}
      {showStatusModal && (
        <StatusUpdateModal
          incidentId={incident.id}
          currentStatus={incident.status}
          onClose={() => setShowStatusModal(false)}
          onSuccess={handleStatusSuccess}
          onSubmit={handleStatusUpdate}
        />
      )}
    </div>
  );
}
