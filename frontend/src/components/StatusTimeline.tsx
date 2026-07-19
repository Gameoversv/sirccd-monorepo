'use client';

import { CheckCircle2, Clock, UserCheck, Wrench, ShieldCheck, XCircle, Circle, RefreshCw, Upload, Edit3 } from 'lucide-react';
import { getStatusLabel } from '@/utils';
import type { AuditLogEntry } from '@/types';

interface TimelineEntry {
  timestamp: string;
  status?: string;
  from_status?: string;
  to_status?: string;
  note?: string;
  author?: string;
  type: 'created' | 'status_change' | 'assigned' | 'note';
}

interface StatusTimelineProps {
  incident: {
    created_at: string;
    assigned_at?: string | null;
    started_at: string | null;
    completed_at: string | null;
    verified_at: string | null;
    status: string;
    notes?: string | null;
  };
  auditLog?: AuditLogEntry[];
}

function formatTs(ts: string): string {
  return new Date(ts).toLocaleString('es-ES', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function StatusIcon({ eventType, status }: { eventType?: string; status?: string }) {
  const cls = 'h-5 w-5';
  if (eventType === 'priority_recalculated') return <RefreshCw className={`${cls} text-primary-400`} />;
  if (eventType === 'image_uploaded') return <Upload className={`${cls} text-blue-400`} />;
  if (eventType === 'manual_update') return <Edit3 className={`${cls} text-gray-400`} />;

  const s = (status || '').toLowerCase();
  if (s === 'open' || s === 'reportado') return <Circle className={`${cls} text-gray-400`} />;
  if (s === 'assigned') return <UserCheck className={`${cls} text-blue-500`} />;
  if (s === 'in_progress') return <Wrench className={`${cls} text-amber-500`} />;
  if (s === 'resolved' || s === 'completado') return <CheckCircle2 className={`${cls} text-green-500`} />;
  if (s === 'verified') return <ShieldCheck className={`${cls} text-primary-500`} />;
  if (s === 'closed' || s === 'cerrado') return <XCircle className={`${cls} text-gray-500`} />;
  return <Clock className={`${cls} text-gray-400`} />;
}

const EVENT_LABELS: Record<string, string> = {
  status_change: 'Cambio de estado',
  priority_recalculated: 'Prioridad recalculada',
  manual_update: 'Actualización manual',
  image_uploaded: 'Imagen subida',
};

const FIELD_LABELS: Record<string, string> = {
  status: 'Estado',
  priority: 'Prioridad',
  estimated_repair_hours: 'Tiempo estimado',
  after_image_url: 'Foto posterior',
};

function AuditEntryContent({ entry }: { entry: AuditLogEntry }) {
  if (entry.event_type === 'status_change') {
    return (
      <p className="text-sm text-gray-900">
        <span className="font-medium text-gray-500 line-through text-xs">
          {getStatusLabel(entry.old_value || '')}
        </span>{' '}
        →{' '}
        <span className="font-semibold">{getStatusLabel(entry.new_value || '')}</span>
        {entry.notes && (
          <span className="block mt-0.5 text-sm text-gray-600">{entry.notes}</span>
        )}
      </p>
    );
  }

  if (entry.event_type === 'priority_recalculated') {
    return (
      <p className="text-sm text-gray-900">
        <span className="font-semibold">Prioridad recalculada</span>
        {entry.old_value && entry.new_value && (
          <span className="block mt-0.5 text-xs text-gray-500">
            {entry.old_value} → {entry.new_value}
          </span>
        )}
      </p>
    );
  }

  if (entry.event_type === 'manual_update') {
    const fieldLabel = FIELD_LABELS[entry.field_name || ''] || entry.field_name;
    return (
      <p className="text-sm text-gray-900">
        <span className="font-semibold">{fieldLabel}</span> actualizado
        {entry.old_value && entry.new_value && (
          <span className="block mt-0.5 text-xs text-gray-500">
            {entry.old_value} → {entry.new_value}
          </span>
        )}
      </p>
    );
  }

  if (entry.event_type === 'image_uploaded') {
    return <p className="text-sm font-semibold text-gray-900">Foto posterior subida</p>;
  }

  return (
    <p className="text-sm text-gray-900">
      <span className="font-semibold">{EVENT_LABELS[entry.event_type] || entry.event_type}</span>
      {entry.new_value && (
        <span className="block mt-0.5 text-xs text-gray-500">{entry.new_value}</span>
      )}
    </p>
  );
}

export function StatusTimeline({ incident, auditLog }: StatusTimelineProps) {
  // Use real audit log when available
  if (auditLog && auditLog.length > 0) {
    // Prepend incident creation entry
    const creationEntry: AuditLogEntry = {
      id: -1,
      incident_id: -1,
      user_id: null,
      event_type: 'created',
      field_name: null,
      old_value: null,
      new_value: 'open',
      notes: 'Incidente registrado',
      created_at: incident.created_at,
    };

    const entries = [creationEntry, ...auditLog];

    return (
      <div className="flow-root">
        <ul className="-mb-8">
          {entries.map((entry, idx) => {
            const isLast = idx === entries.length - 1;
            const displayStatus = entry.event_type === 'status_change'
              ? entry.new_value || ''
              : entry.new_value || '';

            return (
              <li key={`${entry.id}-${idx}`}>
                <div className="relative pb-8">
                  {!isLast && (
                    <span
                      className="absolute left-4 top-4 -ml-px h-full w-0.5 bg-gray-200"
                      aria-hidden="true"
                    />
                  )}
                  <div className="relative flex items-start gap-3">
                    <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-white ring-2 ring-gray-200">
                      <StatusIcon eventType={entry.event_type} status={displayStatus} />
                    </div>
                    <div className="min-w-0 flex-1 pt-0.5">
                      {entry.event_type === 'created' ? (
                        <p className="text-sm font-semibold text-gray-900">
                          Incidente registrado
                          <span className="ml-2 inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-gray-100 text-gray-600">
                            Creación
                          </span>
                        </p>
                      ) : (
                        <AuditEntryContent entry={entry} />
                      )}
                      <p className="mt-1 text-xs text-gray-400">{formatTs(entry.created_at)}</p>
                    </div>
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      </div>
    );
  }

  // Fallback: build timeline from milestone timestamps
  const milestones: TimelineEntry[] = [];

  milestones.push({
    timestamp: incident.created_at,
    status: 'open',
    note: 'Incidente registrado',
    type: 'created',
  });

  if (incident.started_at) {
    milestones.push({
      timestamp: incident.started_at,
      status: 'in_progress',
      note: 'Trabajo iniciado en campo',
      type: 'status_change',
    });
  }

  if (incident.completed_at) {
    milestones.push({
      timestamp: incident.completed_at,
      status: 'resolved',
      note: 'Reparación completada',
      type: 'status_change',
    });
  }

  if (incident.verified_at) {
    milestones.push({
      timestamp: incident.verified_at,
      status: 'verified',
      note: 'Verificado por supervisor',
      type: 'status_change',
    });
  }

  milestones.sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  return (
    <div className="flow-root">
      <ul className="-mb-8">
        {milestones.map((entry, idx) => {
          const isLast = idx === milestones.length - 1;
          const entryStatus = entry.to_status || entry.status || '';

          return (
            <li key={`${entry.timestamp}-${idx}`}>
              <div className="relative pb-8">
                {!isLast && (
                  <span
                    className="absolute left-4 top-4 -ml-px h-full w-0.5 bg-gray-200"
                    aria-hidden="true"
                  />
                )}
                <div className="relative flex items-start gap-3">
                  <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-white ring-2 ring-gray-200">
                    <StatusIcon status={entryStatus} />
                  </div>
                  <div className="min-w-0 flex-1 pt-0.5">
                    <div className="flex items-center gap-2 flex-wrap">
                      {entry.from_status && entry.to_status ? (
                        <p className="text-sm text-gray-900">
                          <span className="font-medium text-gray-500 line-through text-xs">
                            {getStatusLabel(entry.from_status)}
                          </span>{' '}
                          →{' '}
                          <span className="font-semibold">
                            {getStatusLabel(entry.to_status)}
                          </span>
                        </p>
                      ) : (
                        <p className="text-sm font-semibold text-gray-900">
                          {getStatusLabel(entryStatus)}
                          {entry.type === 'created' && (
                            <span className="ml-2 inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-gray-100 text-gray-600">
                              Creación
                            </span>
                          )}
                        </p>
                      )}
                    </div>
                    {entry.note && (
                      <p className="mt-0.5 text-sm text-gray-600">{entry.note}</p>
                    )}
                    <p className="mt-1 text-xs text-gray-400">{formatTs(entry.timestamp)}</p>
                  </div>
                </div>
              </div>
            </li>
          );
        })}
      </ul>
      {milestones.length === 0 && (
        <p className="text-sm text-gray-400 text-center py-4">Sin historial disponible.</p>
      )}
    </div>
  );
}
