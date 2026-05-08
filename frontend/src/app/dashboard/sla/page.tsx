'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { Clock, RefreshCw, AlertTriangle, XCircle, CheckCircle, Settings } from 'lucide-react';
import { SLABadge } from '@/components/SLABadge';
import { incidentsService } from '@/services';
import { useAuthStore } from '@/store';
import { useToast } from '@/hooks';
import type { SLAExpiringResponse, SLAConfig } from '@/types';
import { UserRole } from '@/types';

function StatCard({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string;
  value: number | string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-4 flex items-center gap-3">
      <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${color}`}>
        <Icon className="h-5 w-5" />
      </div>
      <div>
        <p className="text-2xl font-bold">{value}</p>
        <p className="text-xs text-muted-foreground">{label}</p>
      </div>
    </div>
  );
}

function SLAConfigPanel({
  config,
  onSave,
}: {
  config: SLAConfig;
  onSave: (data: Partial<SLAConfig>) => Promise<void>;
}) {
  const [form, setForm] = useState({ ...config });
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave(form);
    } finally {
      setSaving(false);
    }
  };

  const field = (
    key: keyof SLAConfig,
    label: string,
    unit: string,
  ) => (
    <div className="flex items-center gap-3">
      <label className="text-sm text-muted-foreground w-32 flex-shrink-0">{label}</label>
      <input
        type="number"
        min={1}
        step={0.5}
        value={form[key] as number}
        onChange={(e) => setForm((prev) => ({ ...prev, [key]: parseFloat(e.target.value) }))}
        className="w-24 rounded-md border border-border bg-background px-2 py-1 text-sm"
      />
      <span className="text-xs text-muted-foreground">{unit}</span>
    </div>
  );

  return (
    <div className="rounded-xl border border-border bg-card p-4 space-y-4">
      <h3 className="text-sm font-semibold flex items-center gap-1.5">
        <Settings className="h-4 w-4" />
        Configuración de SLA
      </h3>
      <div className="space-y-2">
        {field('sla_hours_critica', 'Crítica', 'horas')}
        {field('sla_hours_alta', 'Alta', 'horas')}
        {field('sla_hours_media', 'Media', 'horas')}
        {field('sla_hours_baja', 'Baja', 'horas')}
        <div className="flex items-center gap-3">
          <label className="text-sm text-muted-foreground w-32 flex-shrink-0">
            Umbral alerta
          </label>
          <input
            type="number"
            min={0.1}
            max={1}
            step={0.05}
            value={form.warning_threshold_pct}
            onChange={(e) =>
              setForm((prev) => ({ ...prev, warning_threshold_pct: parseFloat(e.target.value) }))
            }
            className="w-24 rounded-md border border-border bg-background px-2 py-1 text-sm"
          />
          <span className="text-xs text-muted-foreground">
            ({Math.round((form.warning_threshold_pct ?? 0.8) * 100)}% del SLA consumido)
          </span>
        </div>
      </div>
      <button
        type="button"
        onClick={handleSave}
        disabled={saving}
        className="inline-flex items-center gap-1.5 rounded-md bg-primary-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-primary-700 disabled:opacity-60 transition-colors"
      >
        {saving ? <RefreshCw className="h-3 w-3 animate-spin" /> : null}
        Guardar configuración
      </button>
    </div>
  );
}

export default function SLADashboardPage() {
  const { user } = useAuthStore();
  const toast = useToast();
  const [data, setData] = useState<SLAExpiringResponse | null>(null);
  const [config, setConfig] = useState<SLAConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [withinHours, setWithinHours] = useState(8);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [exp, cfg] = await Promise.all([
        incidentsService.getSLAExpiring(withinHours),
        incidentsService.getSLAConfig(),
      ]);
      setData(exp);
      setConfig(cfg);
    } catch {
      toast.error('Error al cargar datos SLA');
    } finally {
      setLoading(false);
    }
  }, [withinHours, toast]);

  useEffect(() => {
    load();
  }, [load]);

  const handleSaveConfig = async (updates: Partial<SLAConfig>) => {
    try {
      const updated = await incidentsService.updateSLAConfig(updates);
      setConfig(updated);
      toast.success('Configuración SLA guardada');
    } catch {
      toast.error('Error al guardar configuración');
    }
  };

  const overdue = data?.items.filter((i) => i.status === 'overdue') ?? [];
  const warning = data?.items.filter((i) => i.status === 'warning') ?? [];
  const onTrack = data?.items.filter((i) => i.status === 'on_track') ?? [];

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Clock className="h-6 w-6 text-amber-500" />
            Monitoreo de SLAs
          </h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Seguimiento de tiempos de resolución por incidente
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={withinHours}
            onChange={(e) => setWithinHours(Number(e.target.value))}
            className="rounded-md border border-border bg-background px-2 py-1.5 text-sm"
          >
            <option value={4}>Próximas 4h</option>
            <option value={8}>Próximas 8h</option>
            <option value={24}>Próximas 24h</option>
          </select>
          <button
            type="button"
            onClick={load}
            disabled={loading}
            className="inline-flex items-center gap-1.5 rounded-md border border-border bg-card px-3 py-1.5 text-sm hover:bg-muted transition-colors disabled:opacity-60"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Actualizar
          </button>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Vencidos"
          value={data?.overdue_count ?? '—'}
          icon={XCircle}
          color="bg-red-100 text-red-700"
        />
        <StatCard
          label="Por vencer"
          value={data?.expiring_count ?? '—'}
          icon={AlertTriangle}
          color="bg-amber-100 text-amber-700"
        />
        <StatCard
          label="En plazo (ventana)"
          value={onTrack.length}
          icon={CheckCircle}
          color="bg-green-100 text-green-700"
        />
        <StatCard
          label="Ventana de alerta"
          value={`${withinHours}h`}
          icon={Clock}
          color="bg-blue-100 text-blue-700"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Incidents list */}
        <div className="lg:col-span-2 space-y-3">
          {loading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="h-14 skeleton rounded-xl" />
              ))}
            </div>
          ) : (data?.items.length ?? 0) === 0 ? (
            <div className="rounded-xl border border-border bg-card p-10 text-center">
              <CheckCircle className="mx-auto h-10 w-10 text-green-500 mb-2" />
              <p className="text-sm font-medium">Ningún incidente en alerta SLA</p>
              <p className="text-xs text-muted-foreground mt-1">
                Todos los incidentes activos están dentro de su plazo de resolución.
              </p>
            </div>
          ) : (
            <div className="rounded-xl border border-border bg-card overflow-hidden">
              <table className="min-w-full divide-y divide-border">
                <thead className="bg-muted/40">
                  <tr>
                    <th className="px-4 py-2.5 text-left text-[11px] font-semibold text-muted-foreground uppercase">ID</th>
                    <th className="px-4 py-2.5 text-left text-[11px] font-semibold text-muted-foreground uppercase">Ubicación</th>
                    <th className="px-4 py-2.5 text-left text-[11px] font-semibold text-muted-foreground uppercase">Prioridad</th>
                    <th className="px-4 py-2.5 text-left text-[11px] font-semibold text-muted-foreground uppercase">SLA</th>
                    <th className="px-4 py-2.5 text-left text-[11px] font-semibold text-muted-foreground uppercase">Deadline</th>
                    <th className="px-4 py-2.5" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {data!.items.map((item) => (
                    <tr key={item.incident_id} className="hover:bg-muted/30 transition-colors">
                      <td className="px-4 py-2.5 text-sm font-mono font-semibold">
                        <span className="text-muted-foreground">#</span>{item.incident_id}
                      </td>
                      <td className="px-4 py-2.5 text-sm max-w-[180px]">
                        <span className="truncate block">{item.address ?? item.city ?? '—'}</span>
                      </td>
                      <td className="px-4 py-2.5">
                        <span className="text-xs font-semibold uppercase">{item.priority}</span>
                      </td>
                      <td className="px-4 py-2.5">
                        <SLABadge status={item.status} hoursRemaining={item.hours_remaining} />
                      </td>
                      <td className="px-4 py-2.5 text-sm text-muted-foreground whitespace-nowrap">
                        {item.sla_deadline
                          ? new Date(item.sla_deadline).toLocaleString('es-ES', {
                              day: '2-digit',
                              month: 'short',
                              hour: '2-digit',
                              minute: '2-digit',
                            })
                          : '—'}
                      </td>
                      <td className="px-4 py-2.5 text-right">
                        <Link
                          href={`/dashboard/incidents/${item.incident_id}`}
                          className="text-xs text-primary-600 hover:underline font-medium"
                        >
                          Ver →
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Config panel */}
        {user?.role === UserRole.ADMIN && config && (
          <SLAConfigPanel config={config} onSave={handleSaveConfig} />
        )}
      </div>
    </div>
  );
}
