'use client';

import { CheckCircle2, Clock, UserCheck, Wrench, ShieldCheck, XCircle, Circle } from 'lucide-react';
import { getStatusLabel } from '@/utils';

export interface TimelineEntry {
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
    assigned_at: string | null;
    started_at: string | null;
    completed_at: string | null;
    verified_at: string | null;
    status: string;
    notes: string | null;
    assigned_brigade_id: number | null;
  };
}

function parseNotesHistory(notes: string | null): TimelineEntry[] {
  if (!notes) return [];
  const entries: TimelineEntry[] = [];

  // Match pattern: [ISO_TIMESTAMP] old_status -> new_status: optional note
  const regex = /\[(\d{4}-\d{2}-\d{2}T[\d:.]+)\]\s+([\w_]+)\s*->\s*([\w_]+)(?::\s*(.+?))?(?=\n\[|\n\n\[|$)/gs;

  let match;
  while ((match = regex.exec(notes)) !== null) {
    entries.push({
      timestamp: match[1],
      from_status: match[2],
      to_status: match[3],
      note: match[4]?.trim() || undefined,
      type: 'status_change',
    });
  }

  return entries;
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

function StatusIcon({ status }: { status: string }) {
  const s = status.toLowerCase();
  const cls = 'h-5 w-5';
  if (s === 'open' || s === 'reportado') return <Circle className={`${cls} text-gray-400`} />;
  if (s === 'assigned') return <UserCheck className={`${cls} text-blue-500`} />;
  if (s === 'in_progress') return <Wrench className={`${cls} text-amber-500`} />;
  if (s === 'resolved' || s === 'completado') return <CheckCircle2 className={`${cls} text-green-500`} />;
  if (s === 'verified') return <ShieldCheck className={`${cls} text-primary-500`} />;
  if (s === 'closed' || s === 'cerrado') return <XCircle className={`${cls} text-gray-500`} />;
  return <Clock className={`${cls} text-gray-400`} />;
}

export function StatusTimeline({ incident }: StatusTimelineProps) {
  // Build timeline from known timestamp fields + parsed notes
  const milestones: TimelineEntry[] = [];

  milestones.push({
    timestamp: incident.created_at,
    status: 'open',
    note: 'Incidente registrado',
    type: 'created',
  });

  if (incident.assigned_at) {
    milestones.push({
      timestamp: incident.assigned_at,
      status: 'assigned',
      note: incident.assigned_brigade_id
        ? `Asignado a brigada #${incident.assigned_brigade_id}`
        : 'Asignado a brigada',
      type: 'assigned',
    });
  }

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

  // Add notes-based changes (deduplicate by timestamp)
  const parsedNotes = parseNotesHistory(incident.notes);
  const existingTs = new Set(milestones.map((m) => m.timestamp.substring(0, 16)));
  for (const entry of parsedNotes) {
    if (!existingTs.has(entry.timestamp.substring(0, 16))) {
      milestones.push(entry);
    }
  }

  // Sort chronologically
  milestones.sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  const current = incident.status;

  return (
    <div className="flow-root">
      <ul className="-mb-8">
        {milestones.map((entry, idx) => {
          const isLast = idx === milestones.length - 1;
          const entryStatus = entry.to_status || entry.status || '';

          return (
            <li key={`${entry.timestamp}-${idx}`}>
              <div className="relative pb-8">
                {/* Connector line */}
                {!isLast && (
                  <span
                    className="absolute left-4 top-4 -ml-px h-full w-0.5 bg-gray-200"
                    aria-hidden="true"
                  />
                )}

                <div className="relative flex items-start gap-3">
                  {/* Icon */}
                  <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-white ring-2 ring-gray-200">
                    <StatusIcon status={entryStatus} />
                  </div>

                  {/* Content */}
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
                        </p>
                      )}
                      {entry.type === 'created' && (
                        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-gray-100 text-gray-600">
                          Creación
                        </span>
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
