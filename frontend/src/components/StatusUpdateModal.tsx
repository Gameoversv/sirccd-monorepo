'use client';

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { X, ChevronRight, Loader2, AlertCircle } from 'lucide-react';
import { STATUS_TRANSITIONS } from '@/types';
import { getStatusLabel, getStatusColor } from '@/utils';

interface StatusUpdateModalProps {
  incidentId: number;
  currentStatus: string;
  onClose: () => void;
  onSuccess: (newStatus: string) => void;
  onSubmit: (status: string, notes: string) => Promise<void>;
}

export function StatusUpdateModal({
  incidentId,
  currentStatus,
  onClose,
  onSuccess,
  onSubmit,
}: StatusUpdateModalProps) {
  const { t } = useTranslation();
  const availableNext = STATUS_TRANSITIONS[currentStatus.toLowerCase()] || [];
  const [selectedStatus, setSelectedStatus] = useState<string>(availableNext[0] || '');
  const [notes, setNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedStatus) return;

    setIsSubmitting(true);
    setError(null);
    try {
      await onSubmit(selectedStatus, notes);
      onSuccess(selectedStatus);
      onClose();
    } catch (err: any) {
      setError(err?.detail || err?.message || t('incidents.statusModal.updateError'));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
      <div className="bg-white dark:bg-card rounded-xl shadow-xl w-full max-w-md border border-gray-200 dark:border-border">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-border">
          <h2 className="text-base font-semibold text-gray-900 dark:text-foreground">
            {t('incidents.statusModal.title', { incidentId })}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-muted transition-colors"
          >
            <X className="h-4 w-4 text-gray-500" />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="px-6 py-4 space-y-4">
            <div>
              <p className="text-xs text-gray-500 mb-1">{t('incidents.statusModal.currentStatus')}</p>
              <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-sm font-medium ${getStatusColor(currentStatus)}`}>
                {getStatusLabel(currentStatus)}
              </span>
            </div>

            {availableNext.length === 0 ? (
              <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-muted-foreground bg-gray-50 dark:bg-muted rounded-lg px-4 py-3">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                {t('incidents.statusModal.finalState')}
              </div>
            ) : (
              <div>
                <p className="text-xs text-gray-500 mb-2">{t('incidents.statusModal.newStatus')}</p>
                <div className="space-y-2">
                  {availableNext.map((st) => (
                    <label
                      key={st}
                      className={`flex items-center gap-3 rounded-lg border-2 px-4 py-3 cursor-pointer transition-colors ${
                        selectedStatus === st
                          ? 'border-primary-500 bg-primary-50 dark:bg-primary-500/15'
                          : 'border-gray-200 dark:border-border hover:border-gray-300 dark:hover:border-primary-500/50'
                      }`}
                    >
                      <input
                        type="radio"
                        name="status"
                        value={st}
                        checked={selectedStatus === st}
                        onChange={() => setSelectedStatus(st)}
                        className="h-4 w-4 text-primary-600 focus:ring-primary-500"
                      />
                      <div className="flex items-center gap-2 flex-1">
                        <span className="text-gray-400 text-xs">{getStatusLabel(currentStatus)}</span>
                        <ChevronRight className="h-3 w-3 text-gray-400" />
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getStatusColor(st)}`}>
                          {getStatusLabel(st)}
                        </span>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {availableNext.length > 0 && (
              <div>
                <label className="block text-xs text-gray-500 mb-1">{t('incidents.statusModal.notesOptional')}</label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={3}
                  maxLength={2000}
                  placeholder={t('incidents.statusModal.notesPlaceholder')}
                  className="w-full rounded-lg border border-gray-300 dark:border-border bg-white dark:bg-background px-3 py-2 text-sm focus:border-primary-500 focus:ring-1 focus:ring-primary-500 focus:outline-none resize-none"
                />
                <p className="text-right text-xs text-gray-400 mt-1">{notes.length}/2000</p>
              </div>
            )}

            {error && (
              <div className="flex items-center gap-2 text-sm text-red-700 dark:text-red-200 bg-red-50 dark:bg-red-500/15 rounded-lg px-4 py-3 border border-red-200 dark:border-red-500/40">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                {error}
              </div>
            )}
          </div>

          <div className="flex justify-end gap-2 px-6 py-4 border-t border-gray-200 dark:border-border">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-border text-gray-700 dark:text-foreground hover:bg-gray-50 dark:hover:bg-muted transition-colors"
            >
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !selectedStatus || availableNext.length === 0}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm rounded-lg bg-primary-600 hover:bg-primary-700 text-white font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
              {t('incidents.statusModal.confirmChange')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
