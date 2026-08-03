'use client';

/** Horas a partir de las cuales la barra de resolución se considera vacía. */
const RESOLUTION_SCALE_HOURS = 96;

interface MeterProps {
  label: string;
  display: string;
  pct: number | null;
  barClass: string;
  loading: boolean;
}

function Meter({ label, display, pct, barClass, loading }: MeterProps) {
  return (
    <div>
      <div className="mb-1.5 flex items-baseline justify-between gap-2">
        <span className="text-xs text-muted-foreground">{label}</span>
        <span className="text-sm font-semibold tabular-nums">{display}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-muted">
        {!loading && pct != null && (
          <div
            className={`h-full rounded-full transition-all duration-700 ${barClass}`}
            style={{ width: `${Math.max(0, Math.min(pct, 100))}%` }}
          />
        )}
      </div>
    </div>
  );
}

interface SlaPanelProps {
  compliancePct: number | null;
  avgResolutionHours: number | null;
  loading: boolean;
  labels: { title: string; compliance: string; avgResolution: string };
}

export function SlaPanel({ compliancePct, avgResolutionHours, loading, labels }: SlaPanelProps) {
  const complianceClass =
    (compliancePct ?? 0) >= 80
      ? 'bg-green-500'
      : (compliancePct ?? 0) >= 60
        ? 'bg-yellow-500'
        : 'bg-red-500';

  // La barra representa cuánto margen queda frente a la escala de referencia:
  // menos horas de resolución, barra más llena.
  const resolutionPct =
    avgResolutionHours == null ? null : (1 - avgResolutionHours / RESOLUTION_SCALE_HOURS) * 100;

  return (
    <div className="rounded-2xl border border-border bg-card p-5 shadow-soft">
      <h2 className="mb-4 text-sm font-semibold tracking-tight">{labels.title}</h2>
      <div className="space-y-4">
        <Meter
          label={labels.compliance}
          display={loading || compliancePct == null ? '—' : `${compliancePct}%`}
          pct={compliancePct}
          barClass={complianceClass}
          loading={loading}
        />
        <Meter
          label={labels.avgResolution}
          display={loading || avgResolutionHours == null ? '—' : `${avgResolutionHours.toFixed(1)}h`}
          pct={resolutionPct}
          barClass="bg-indigo-400"
          loading={loading}
        />
      </div>
    </div>
  );
}
