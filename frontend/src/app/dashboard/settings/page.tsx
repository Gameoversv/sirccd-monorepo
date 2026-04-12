'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ChevronLeft, Loader2, Save, RotateCcw, Settings2 } from 'lucide-react';

import { prioritySettingsService } from '@/services';
import { useAuthStore } from '@/store';
import { UserRole } from '@/types';

type FormState = {
  weight_severity: number;
  weight_age: number;
  weight_damage_type: number;
  weight_location: number;
  weight_duplicates: number;
  poi_radius_meters: number;
  duplicate_radius_meters: number;
  duplicate_time_window_days: number;
};

const DEFAULT_FORM: FormState = {
  weight_severity: 35,
  weight_age: 20,
  weight_damage_type: 15,
  weight_location: 20,
  weight_duplicates: 10,
  poi_radius_meters: 500,
  duplicate_radius_meters: 100,
  duplicate_time_window_days: 30,
};

function Field({
  label,
  description,
  value,
  min,
  max,
  step = 1,
  suffix,
  onChange,
}: {
  label: string;
  description: string;
  value: number;
  min: number;
  max: number;
  step?: number;
  suffix?: string;
  onChange: (next: number) => void;
}) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-gray-900">{label}</p>
          <p className="text-xs text-gray-500 mt-1">{description}</p>
        </div>
        <div className="flex items-center gap-2">
          <input
            type="number"
            value={Number.isFinite(value) ? value : 0}
            min={min}
            max={max}
            step={step}
            onChange={(e) => onChange(Number(e.target.value))}
            className="w-28 rounded-lg border border-gray-300 px-3 py-2 text-sm text-right focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
          {suffix ? <span className="text-sm text-gray-500 w-8">{suffix}</span> : null}
        </div>
      </div>
    </div>
  );
}

export default function SettingsPage() {
  const { user } = useAuthStore();
  const [form, setForm] = useState<FormState>(DEFAULT_FORM);
  const [initialForm, setInitialForm] = useState<FormState>(DEFAULT_FORM);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const isAdmin = user?.role === UserRole.ADMIN;

  const totalWeight = useMemo(
    () =>
      form.weight_severity +
      form.weight_age +
      form.weight_damage_type +
      form.weight_location +
      form.weight_duplicates,
    [form]
  );

  const dirty = useMemo(() => JSON.stringify(form) !== JSON.stringify(initialForm), [form, initialForm]);

  const loadSettings = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await prioritySettingsService.getPrioritySettings();
      const next: FormState = {
        weight_severity: Number((data.weight_severity * 100).toFixed(2)),
        weight_age: Number((data.weight_age * 100).toFixed(2)),
        weight_damage_type: Number((data.weight_damage_type * 100).toFixed(2)),
        weight_location: Number((data.weight_location * 100).toFixed(2)),
        weight_duplicates: Number((data.weight_duplicates * 100).toFixed(2)),
        poi_radius_meters: data.poi_radius_meters,
        duplicate_radius_meters: data.duplicate_radius_meters,
        duplicate_time_window_days: data.duplicate_time_window_days,
      };
      setForm(next);
      setInitialForm(next);
    } catch (err: any) {
      setError(err?.detail || 'No se pudieron cargar los ajustes.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!isAdmin) {
      setLoading(false);
      return;
    }
    loadSettings();
  }, [isAdmin]);

  const setValue = (key: keyof FormState, value: number) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleReset = () => {
    setForm(initialForm);
    setNotice(null);
    setError(null);
  };

  const handleSave = async () => {
    setError(null);
    setNotice(null);

    if (Math.abs(totalWeight - 100) > 0.01) {
      setError('La suma de pesos debe ser exactamente 100%.');
      return;
    }

    setSaving(true);
    try {
      const updated = await prioritySettingsService.updatePrioritySettings({
        weight_severity: Number((form.weight_severity / 100).toFixed(4)),
        weight_age: Number((form.weight_age / 100).toFixed(4)),
        weight_damage_type: Number((form.weight_damage_type / 100).toFixed(4)),
        weight_location: Number((form.weight_location / 100).toFixed(4)),
        weight_duplicates: Number((form.weight_duplicates / 100).toFixed(4)),
        poi_radius_meters: Math.round(form.poi_radius_meters),
        duplicate_radius_meters: Math.round(form.duplicate_radius_meters),
        duplicate_time_window_days: Math.round(form.duplicate_time_window_days),
      });

      const next: FormState = {
        weight_severity: Number((updated.weight_severity * 100).toFixed(2)),
        weight_age: Number((updated.weight_age * 100).toFixed(2)),
        weight_damage_type: Number((updated.weight_damage_type * 100).toFixed(2)),
        weight_location: Number((updated.weight_location * 100).toFixed(2)),
        weight_duplicates: Number((updated.weight_duplicates * 100).toFixed(2)),
        poi_radius_meters: updated.poi_radius_meters,
        duplicate_radius_meters: updated.duplicate_radius_meters,
        duplicate_time_window_days: updated.duplicate_time_window_days,
      };
      setForm(next);
      setInitialForm(next);
      setNotice('Ajustes guardados correctamente.');
    } catch (err: any) {
      setError(err?.detail || 'No se pudieron guardar los ajustes.');
    } finally {
      setSaving(false);
    }
  };

  if (!isAdmin) {
    return (
      <div className="max-w-3xl mx-auto space-y-4">
        <div className="flex items-center gap-3">
          <Link href="/dashboard" className="p-1.5 rounded-md hover:bg-gray-100 transition-colors">
            <ChevronLeft className="h-5 w-5 text-gray-500" />
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">Ajustes</h1>
        </div>
        <div className="rounded-xl border border-amber-200 bg-amber-50 text-amber-800 px-4 py-3 text-sm">
          Esta seccion es solo para administradores.
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-[320px] flex items-center justify-center">
        <Loader2 className="h-7 w-7 animate-spin text-primary-600" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-5">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Link href="/dashboard" className="p-1.5 rounded-md hover:bg-gray-100 transition-colors">
            <ChevronLeft className="h-5 w-5 text-gray-500" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Settings2 className="w-6 h-6 text-primary-600" />
              Ajustes de Prioridad
            </h1>
            <p className="text-sm text-gray-500">Configura los pesos y radios usados para calcular el score.</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleReset}
            disabled={!dirty || saving}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            <RotateCcw className="w-4 h-4" />
            Restablecer
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={!dirty || saving}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50"
          >
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            Guardar cambios
          </button>
        </div>
      </div>

      {error ? (
        <div className="rounded-lg border border-red-200 bg-red-50 text-red-700 px-4 py-3 text-sm">{error}</div>
      ) : null}
      {notice ? (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 text-emerald-700 px-4 py-3 text-sm">{notice}</div>
      ) : null}

      <div className="rounded-xl border border-gray-200 bg-gray-50 p-4">
        <p className="text-sm text-gray-700 font-medium">Suma de pesos</p>
        <p className={`text-xl font-bold ${Math.abs(totalWeight - 100) <= 0.01 ? 'text-emerald-700' : 'text-red-600'}`}>
          {totalWeight.toFixed(2)}%
        </p>
        <p className="text-xs text-gray-500 mt-1">Debe sumar 100% para mantener el score en escala 0-100.</p>
      </div>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-gray-800 uppercase tracking-wide">Pesos del score</h2>
        <Field
          label="Severidad"
          description="Define cuanto impacta la gravedad del daño detectado."
          value={form.weight_severity}
          min={0}
          max={100}
          step={0.1}
          suffix="%"
          onChange={(v) => setValue('weight_severity', v)}
        />
        <Field
          label="Antiguedad"
          description="Aumenta prioridad segun el tiempo transcurrido sin resolver."
          value={form.weight_age}
          min={0}
          max={100}
          step={0.1}
          suffix="%"
          onChange={(v) => setValue('weight_age', v)}
        />
        <Field
          label="Tipo de daño"
          description="Peso del tipo de daño (por ejemplo bache vs grieta)."
          value={form.weight_damage_type}
          min={0}
          max={100}
          step={0.1}
          suffix="%"
          onChange={(v) => setValue('weight_damage_type', v)}
        />
        <Field
          label="Ubicacion"
          description="Cuanto influyen los puntos de interes cercanos."
          value={form.weight_location}
          min={0}
          max={100}
          step={0.1}
          suffix="%"
          onChange={(v) => setValue('weight_location', v)}
        />
        <Field
          label="Duplicados"
          description="Peso de reportes visualmente similares en el area."
          value={form.weight_duplicates}
          min={0}
          max={100}
          step={0.1}
          suffix="%"
          onChange={(v) => setValue('weight_duplicates', v)}
        />
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-gray-800 uppercase tracking-wide">Radios y ventana</h2>
        <Field
          label="Radio de POIs"
          description="Distancia maxima para contar POIs y calcular el factor de ubicacion."
          value={form.poi_radius_meters}
          min={1}
          max={5000}
          step={1}
          suffix="m"
          onChange={(v) => setValue('poi_radius_meters', v)}
        />
        <Field
          label="Radio de duplicados"
          description="Radio geografico para buscar reportes candidatos a duplicado."
          value={form.duplicate_radius_meters}
          min={1}
          max={5000}
          step={1}
          suffix="m"
          onChange={(v) => setValue('duplicate_radius_meters', v)}
        />
        <Field
          label="Ventana de duplicados"
          description="Cantidad de dias hacia atras para considerar reportes similares."
          value={form.duplicate_time_window_days}
          min={1}
          max={365}
          step={1}
          suffix="d"
          onChange={(v) => setValue('duplicate_time_window_days', v)}
        />
      </section>
    </div>
  );
}

