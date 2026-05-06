'use client';

import { Clock, AlertTriangle, CheckCircle, XCircle, MinusCircle } from 'lucide-react';
import type { SLAStatus } from '@/types';

interface SLABadgeProps {
  status: SLAStatus;
  hoursRemaining?: number | null;
  compact?: boolean;
}

const CONFIG: Record<
  SLAStatus,
  { label: string; Icon: React.ComponentType<{ className?: string }>; cls: string }
> = {
  on_track: {
    label: 'En plazo',
    Icon: CheckCircle,
    cls: 'bg-green-100 text-green-800 dark:bg-green-500/25 dark:text-green-200',
  },
  warning: {
    label: 'Por vencer',
    Icon: AlertTriangle,
    cls: 'bg-amber-100 text-amber-800 dark:bg-amber-500/25 dark:text-amber-200',
  },
  overdue: {
    label: 'Vencido',
    Icon: XCircle,
    cls: 'bg-red-100 text-red-800 dark:bg-red-500/25 dark:text-red-200',
  },
  completed: {
    label: 'Completado',
    Icon: CheckCircle,
    cls: 'bg-blue-100 text-blue-800 dark:bg-blue-500/25 dark:text-blue-200',
  },
  not_started: {
    label: 'Sin iniciar',
    Icon: MinusCircle,
    cls: 'bg-gray-100 text-gray-600 dark:bg-gray-700/40 dark:text-gray-300',
  },
};

function formatHours(hours: number): string {
  if (hours < 1) return `${Math.round(hours * 60)}min`;
  if (hours < 24) return `${hours.toFixed(1)}h`;
  return `${(hours / 24).toFixed(1)}d`;
}

export function SLABadge({ status, hoursRemaining, compact = false }: SLABadgeProps) {
  const { label, Icon, cls } = CONFIG[status] ?? CONFIG.not_started;

  const timeStr =
    hoursRemaining != null && (status === 'warning' || status === 'on_track')
      ? formatHours(Math.max(0, hoursRemaining))
      : null;

  if (compact) {
    return (
      <span
        className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold ${cls}`}
        title={timeStr ? `${label} — ${timeStr} restante` : label}
      >
        <Icon className="h-2.5 w-2.5 flex-shrink-0" />
        {timeStr ?? label}
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium ${cls}`}>
      <Icon className="h-3.5 w-3.5 flex-shrink-0" />
      <span>{label}</span>
      {timeStr && (
        <span className="font-mono opacity-80">
          <Clock className="inline h-2.5 w-2.5 mr-0.5" />
          {timeStr}
        </span>
      )}
    </span>
  );
}
