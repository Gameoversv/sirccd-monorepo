'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { AlertTriangle, XCircle, Clock } from 'lucide-react';
import { SLABadge } from '@/components/SLABadge';
import type { SLAExpiringResponse } from '@/types';
import { incidentsService } from '@/services';

export function SLAPanel() {
  const [data, setData] = useState<SLAExpiringResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    incidentsService
      .getSLAExpiring(4)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  const critical = (data?.items ?? []).filter((i) => i.status === 'overdue');
  const warning = (data?.items ?? []).filter((i) => i.status === 'warning');

  if (loading) {
    return (
      <div className="rounded-xl border border-border bg-card p-4 space-y-2">
        <div className="h-4 skeleton rounded w-40" />
        <div className="h-20 skeleton rounded" />
      </div>
    );
  }

  if (!data || data.items.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-card p-4">
        <p className="text-xs text-muted-foreground flex items-center gap-1.5">
          <Clock className="h-3.5 w-3.5" />
          Todos los SLAs están en plazo.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-border bg-card shadow-soft overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-muted/30">
        <span className="text-sm font-semibold flex items-center gap-1.5">
          <Clock className="h-4 w-4 text-amber-500" />
          Alertas SLA
        </span>
        <div className="flex items-center gap-2">
          {critical.length > 0 && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold bg-red-100 text-red-700">
              <XCircle className="h-3 w-3" />
              {critical.length} vencido{critical.length !== 1 ? 's' : ''}
            </span>
          )}
          {warning.length > 0 && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-700">
              <AlertTriangle className="h-3 w-3" />
              {warning.length} por vencer
            </span>
          )}
        </div>
      </div>

      <ul className="divide-y divide-border max-h-64 overflow-y-auto">
        {data.items.map((item) => (
          <li key={item.incident_id} className="flex items-center gap-3 px-4 py-2.5 hover:bg-muted/30 transition-colors">
            <SLABadge status={item.status} hoursRemaining={item.hours_remaining} compact />
            <div className="flex-1 min-w-0">
              <Link
                href={`/dashboard/incidents/${item.incident_id}`}
                className="text-sm font-medium text-foreground hover:text-primary-600 transition-colors"
              >
                #{item.incident_id}
              </Link>
              {item.address && (
                <p className="text-xs text-muted-foreground truncate">{item.address}</p>
              )}
            </div>
            <span className="text-xs uppercase font-semibold text-muted-foreground">{item.priority}</span>
          </li>
        ))}
      </ul>

      <div className="px-4 py-2 bg-muted/20 border-t border-border">
        <Link href="/dashboard/sla" className="text-xs text-primary-600 hover:underline">
          Ver panel SLA completo →
        </Link>
      </div>
    </div>
  );
}
