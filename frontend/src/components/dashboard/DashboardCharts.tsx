'use client';

import {
  Bar,
  BarChart,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

export interface ChartDatum {
  name: string;
  value: number;
  fill: string;
}

const TOOLTIP_STYLE = {
  fontSize: 12,
  borderRadius: 8,
  border: '1px solid hsl(var(--border))',
  background: 'hsl(var(--card))',
} as const;

interface PanelProps {
  title: string;
  children: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}

/** Contenedor común de los bloques del panel: mismo marco, distinto peso. */
export function ChartPanel({ title, children, action, className }: PanelProps) {
  return (
    <section className={`rounded-2xl border border-border bg-card p-5 shadow-soft ${className ?? ''}`}>
      <header className="mb-4 flex items-center justify-between gap-3">
        <h2 className="text-sm font-semibold tracking-tight">{title}</h2>
        {action}
      </header>
      {children}
    </section>
  );
}

interface ChartProps {
  data: ChartDatum[];
  loading: boolean;
  unitLabel: string;
  height?: number;
}

export function StatusBarChart({ data, loading, unitLabel, height = 240 }: ChartProps) {
  if (loading) return <div className="skeleton rounded-lg" style={{ height }} />;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} barSize={30}>
        <XAxis dataKey="name" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
        <YAxis allowDecimals={false} tick={{ fontSize: 11 }} tickLine={false} axisLine={false} width={28} />
        <Tooltip
          cursor={{ fill: 'hsl(var(--muted))', opacity: 0.4 }}
          formatter={(v: number | string | undefined) => [v ?? 0, unitLabel]}
          contentStyle={TOOLTIP_STYLE}
        />
        <Bar dataKey="value" radius={[6, 6, 0, 0]}>
          {data.map((entry, i) => (
            <Cell key={i} fill={entry.fill} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function PriorityBarChart({ data, loading, unitLabel, height = 200 }: ChartProps) {
  if (loading) return <div className="skeleton rounded-lg" style={{ height }} />;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" barSize={24}>
        <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
        <YAxis
          type="category"
          dataKey="name"
          width={64}
          tick={{ fontSize: 11 }}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip
          cursor={{ fill: 'hsl(var(--muted))', opacity: 0.4 }}
          formatter={(v: number | string | undefined) => [v ?? 0, unitLabel]}
          contentStyle={TOOLTIP_STYLE}
        />
        <Bar dataKey="value" radius={[0, 6, 6, 0]}>
          {data.map((entry, i) => (
            <Cell key={i} fill={entry.fill} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

interface DonutProps extends ChartProps {
  /** Total mostrado en el centro; se omite cuando no aporta. */
  centerValue?: string;
  centerLabel?: string;
}

export function DonutChart({
  data,
  loading,
  unitLabel,
  height = 220,
  centerValue,
  centerLabel,
}: DonutProps) {
  if (loading) return <div className="skeleton rounded-lg" style={{ height }} />;

  return (
    <div className="relative">
      <ResponsiveContainer width="100%" height={height}>
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="45%"
            innerRadius={58}
            outerRadius={84}
            paddingAngle={3}
            stroke="none"
          >
            {data.map((entry, i) => (
              <Cell key={i} fill={entry.fill} />
            ))}
          </Pie>
          <Legend iconSize={9} iconType="circle" wrapperStyle={{ fontSize: 12 }} />
          <Tooltip
            formatter={(v: number | string | undefined) => [v ?? 0, unitLabel]}
            contentStyle={TOOLTIP_STYLE}
          />
        </PieChart>
      </ResponsiveContainer>

      {centerValue && (
        <div
          className="pointer-events-none absolute inset-x-0 flex flex-col items-center"
          style={{ top: height * 0.45 - 22 }}
        >
          <span className="text-2xl font-bold tabular-nums leading-none">{centerValue}</span>
          {centerLabel && (
            <span className="mt-1 text-[10px] uppercase tracking-wider text-muted-foreground">
              {centerLabel}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
