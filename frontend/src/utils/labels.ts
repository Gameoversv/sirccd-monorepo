import type { DamageClass, SeverityLevel, IncidentStatus } from '@/types';
import i18n from '@/i18n/config';

function isEnglish(): boolean {
  return String(i18n.language || '').toLowerCase().startsWith('en');
}

/**
 * Get color class for damage severity
 */
export function getSeverityColor(severity: SeverityLevel | string): string {
  const colors: Record<string, string> = {
    baja: 'text-success-700 bg-success-50 dark:bg-success-500/35 dark:text-success-100',
    media: 'text-warning-700 bg-warning-50 dark:bg-warning-500/35 dark:text-warning-100',
    alta: 'text-danger-700 bg-danger-50 dark:bg-danger-500/35 dark:text-danger-100',
  };
  return colors[String(severity).toLowerCase()] || 'text-gray-700 bg-gray-50 dark:bg-gray-700/40 dark:text-gray-100';
}

/**
 * Get color class for incident status
 */
export function getStatusColor(status: IncidentStatus | string): string {
  const colors: Record<string, string> = {
    reportado: 'text-gray-700 bg-gray-50 dark:bg-gray-700/40 dark:text-gray-100',
    asignado: 'text-blue-700 bg-blue-50 dark:bg-blue-500/35 dark:text-blue-100',
    en_progreso: 'text-warning-700 bg-warning-50 dark:bg-warning-500/35 dark:text-warning-100',
    completado: 'text-success-700 bg-success-50 dark:bg-success-500/35 dark:text-success-100',
    verificado: 'text-primary-700 bg-primary-50 dark:bg-primary-500/35 dark:text-primary-100',
    cerrado: 'text-gray-700 bg-gray-100 dark:bg-gray-700/40 dark:text-gray-100',
    open: 'text-gray-700 bg-gray-50 dark:bg-gray-700/40 dark:text-gray-100',
    assigned: 'text-blue-700 bg-blue-50 dark:bg-blue-500/35 dark:text-blue-100',
    in_progress: 'text-warning-700 bg-warning-50 dark:bg-warning-500/35 dark:text-warning-100',
    resolved: 'text-success-700 bg-success-50 dark:bg-success-500/35 dark:text-success-100',
    verified: 'text-primary-700 bg-primary-50 dark:bg-primary-500/35 dark:text-primary-100',
    closed: 'text-gray-700 bg-gray-100 dark:bg-gray-700/40 dark:text-gray-100',
  };
  return colors[String(status).toLowerCase()] || 'text-gray-700 bg-gray-50 dark:bg-gray-700/40 dark:text-gray-100';
}

/**
 * Get human-readable labels
 */
export function getDamageClassLabel(damageClass: DamageClass | string): string {
  const labels: Record<string, string> = isEnglish()
    ? {
        bache: 'Pothole',
        grieta: 'Crack',
      }
    : {
        bache: 'Bache',
        grieta: 'Grieta',
      };
  return labels[String(damageClass).toLowerCase()] || String(damageClass);
}

export function getSeverityLabel(severity: SeverityLevel | string): string {
  const labels: Record<string, string> = isEnglish()
    ? {
        baja: 'Low',
        media: 'Medium',
        alta: 'High',
      }
    : {
        baja: 'Baja',
        media: 'Media',
        alta: 'Alta',
      };
  return labels[String(severity).toLowerCase()] || String(severity);
}

export function getStatusLabel(status: IncidentStatus | string): string {
  const labels: Record<string, string> = isEnglish()
    ? {
        reportado: 'Reported',
        asignado: 'Assigned',
        en_progreso: 'In Progress',
        completado: 'Completed',
        verificado: 'Verified',
        cerrado: 'Closed',
        open: 'Open',
        assigned: 'Assigned',
        in_progress: 'In Progress',
        resolved: 'Resolved',
        verified: 'Verified',
        closed: 'Closed',
      }
    : {
        reportado: 'Reportado',
        asignado: 'Asignado',
        en_progreso: 'En Progreso',
        completado: 'Completado',
        verificado: 'Verificado',
        cerrado: 'Cerrado',
        open: 'Abierto',
        assigned: 'Asignado',
        in_progress: 'En Progreso',
        resolved: 'Resuelto',
        verified: 'Verificado',
        closed: 'Cerrado',
      };
  return labels[String(status).toLowerCase()] || String(status);
}

export function getPriorityLabel(priority: string): string {
  const labels: Record<string, string> = isEnglish()
    ? {
        baja: 'Low',
        media: 'Medium',
        alta: 'High',
        critica: 'Critical',
      }
    : {
        baja: 'Baja',
        media: 'Media',
        alta: 'Alta',
        critica: 'Crítica',
      };
  return labels[String(priority).toLowerCase()] || String(priority);
}

export function getPriorityColor(priority: string): string {
  const colors: Record<string, string> = {
    baja: 'text-blue-700 bg-blue-50 dark:bg-blue-500/35 dark:text-blue-100',
    media: 'text-amber-700 bg-amber-50 dark:bg-amber-500/35 dark:text-amber-100',
    alta: 'text-orange-700 bg-orange-50 dark:bg-orange-500/35 dark:text-orange-100',
    critica: 'text-red-700 bg-red-50 dark:bg-red-500/35 dark:text-red-100',
  };
  return colors[String(priority).toLowerCase()] || 'text-gray-700 bg-gray-50 dark:bg-gray-700/40 dark:text-gray-100';
}
