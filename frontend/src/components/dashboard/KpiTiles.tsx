'use client';

import { cn } from '@/utils';

interface HeroKpiProps {
  label: string;
  value: string;
  hint?: string;
  icon: React.ComponentType<{ className?: string }>;
  loading: boolean;
}

/**
 * Métrica principal del panel: se lleva el mayor peso tipográfico para que la
 * lectura empiece aquí y no en la fila de tarjetas secundarias.
 */
export function HeroKpi({ label, value, hint, icon: Icon, loading }: HeroKpiProps) {
  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-brand p-5 text-white shadow-elevated">
      <div className="flex items-center gap-2 text-white/80">
        <Icon className="h-4 w-4" />
        <span className="text-xs font-medium uppercase tracking-wider">{label}</span>
      </div>

      {loading ? (
        <div className="mt-2 h-12 w-28 rounded-lg bg-white/20 animate-pulse" />
      ) : (
        <p className="mt-1 text-5xl font-bold leading-none tracking-tight tabular-nums">{value}</p>
      )}

      {hint && <p className="mt-2 text-xs text-white/70">{hint}</p>}

      <div className="pointer-events-none absolute -right-8 -top-10 h-32 w-32 rounded-full bg-white/10" />
      <div className="pointer-events-none absolute -right-4 -bottom-12 h-28 w-28 rounded-full bg-white/5" />
    </div>
  );
}

interface KpiTileProps {
  label: string;
  value: string;
  hint?: string;
  icon: React.ComponentType<{ className?: string }>;
  accent: string;
  loading: boolean;
}

/** Métrica secundaria: compacta, pensada para leerse en cuadrícula. */
export function KpiTile({ label, value, hint, icon: Icon, accent, loading }: KpiTileProps) {
  return (
    <div className="group rounded-xl border border-border bg-card p-3.5 shadow-soft transition-all hover:shadow-elevated hover:-translate-y-0.5">
      <div className="flex items-center gap-2">
        <span className={cn('flex h-7 w-7 items-center justify-center rounded-lg text-white', accent)}>
          <Icon className="h-3.5 w-3.5" />
        </span>
        <span className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground truncate">
          {label}
        </span>
      </div>

      {loading ? (
        <div className="mt-2 h-6 w-16 skeleton rounded" />
      ) : (
        <p className="mt-1.5 text-xl font-bold leading-tight tracking-tight tabular-nums">{value}</p>
      )}

      {hint && <p className="mt-0.5 text-[11px] text-muted-foreground truncate">{hint}</p>}
    </div>
  );
}
