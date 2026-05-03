'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ChevronLeft, Loader2, Save, RotateCcw, Settings2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';

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
  clustering_eps_meters: number;
  clustering_min_samples: number;
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
  clustering_eps_meters: 50,
  clustering_min_samples: 2,
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
  const { t } = useTranslation();
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
        clustering_eps_meters: data.clustering_eps_meters,
        clustering_min_samples: data.clustering_min_samples,
      };
      setForm(next);
      setInitialForm(next);
    } catch (err: any) {
      setError(err?.detail || t('settings.errors.load'));
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
      setError(t('settings.errors.weightsTotal'));
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
        clustering_eps_meters: Math.round(form.clustering_eps_meters),
        clustering_min_samples: Math.round(form.clustering_min_samples),
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
        clustering_eps_meters: updated.clustering_eps_meters,
        clustering_min_samples: updated.clustering_min_samples,
      };
      setForm(next);
      setInitialForm(next);
      setNotice(t('settings.notice.saved'));
    } catch (err: any) {
      setError(err?.detail || t('settings.errors.save'));
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
          <h1 className="text-2xl font-bold text-gray-900">{t('settings.title')}</h1>
        </div>
        <div className="rounded-xl border border-amber-200 bg-amber-50 text-amber-800 px-4 py-3 text-sm">
          {t('settings.adminOnly')}
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
              {t('settings.priorityTitle')}
            </h1>
            <p className="text-sm text-gray-500">{t('settings.subtitle')}</p>
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
            {t('settings.actions.reset')}
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={!dirty || saving}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50"
          >
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            {t('settings.actions.save')}
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
        <p className="text-sm text-gray-700 font-medium">{t('settings.weightsTotalTitle')}</p>
        <p className={`text-xl font-bold ${Math.abs(totalWeight - 100) <= 0.01 ? 'text-emerald-700' : 'text-red-600'}`}>
          {totalWeight.toFixed(2)}%
        </p>
        <p className="text-xs text-gray-500 mt-1">{t('settings.weightsTotalHint')}</p>
      </div>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-gray-800 uppercase tracking-wide">{t('settings.sections.weights')}</h2>
        <Field
          label={t('settings.fields.severity.label')}
          description={t('settings.fields.severity.description')}
          value={form.weight_severity}
          min={0}
          max={100}
          step={0.1}
          suffix="%"
          onChange={(v) => setValue('weight_severity', v)}
        />
        <Field
          label={t('settings.fields.age.label')}
          description={t('settings.fields.age.description')}
          value={form.weight_age}
          min={0}
          max={100}
          step={0.1}
          suffix="%"
          onChange={(v) => setValue('weight_age', v)}
        />
        <Field
          label={t('settings.fields.damageType.label')}
          description={t('settings.fields.damageType.description')}
          value={form.weight_damage_type}
          min={0}
          max={100}
          step={0.1}
          suffix="%"
          onChange={(v) => setValue('weight_damage_type', v)}
        />
        <Field
          label={t('settings.fields.location.label')}
          description={t('settings.fields.location.description')}
          value={form.weight_location}
          min={0}
          max={100}
          step={0.1}
          suffix="%"
          onChange={(v) => setValue('weight_location', v)}
        />
        <Field
          label={t('settings.fields.duplicates.label')}
          description={t('settings.fields.duplicates.description')}
          value={form.weight_duplicates}
          min={0}
          max={100}
          step={0.1}
          suffix="%"
          onChange={(v) => setValue('weight_duplicates', v)}
        />
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-gray-800 uppercase tracking-wide">{t('settings.sections.ranges')}</h2>
        <Field
          label={t('settings.fields.poiRadius.label')}
          description={t('settings.fields.poiRadius.description')}
          value={form.poi_radius_meters}
          min={1}
          max={5000}
          step={1}
          suffix="m"
          onChange={(v) => setValue('poi_radius_meters', v)}
        />
        <Field
          label={t('settings.fields.duplicateRadius.label')}
          description={t('settings.fields.duplicateRadius.description')}
          value={form.duplicate_radius_meters}
          min={1}
          max={5000}
          step={1}
          suffix="m"
          onChange={(v) => setValue('duplicate_radius_meters', v)}
        />
        <Field
          label={t('settings.fields.duplicateWindow.label')}
          description={t('settings.fields.duplicateWindow.description')}
          value={form.duplicate_time_window_days}
          min={1}
          max={365}
          step={1}
          suffix="d"
          onChange={(v) => setValue('duplicate_time_window_days', v)}
        />
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-gray-800 uppercase tracking-wide">
          {t('settings.sections.clustering')}
        </h2>
        <div className="rounded-xl border border-blue-100 bg-blue-50 px-4 py-2 text-xs text-blue-700">
          {t('settings.clusteringHint')}
        </div>
        <Field
          label={t('settings.fields.clusteringEps.label')}
          description={t('settings.fields.clusteringEps.description')}
          value={form.clustering_eps_meters}
          min={5}
          max={2000}
          step={5}
          suffix="m"
          onChange={(v) => setValue('clustering_eps_meters', v)}
        />
        <Field
          label={t('settings.fields.clusteringMinSamples.label')}
          description={t('settings.fields.clusteringMinSamples.description')}
          value={form.clustering_min_samples}
          min={2}
          max={20}
          step={1}
          onChange={(v) => setValue('clustering_min_samples', v)}
        />
      </section>
    </div>
  );
}
