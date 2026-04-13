import type { DamageClass, SeverityLevel, IncidentStatus, ReportStatus } from '@/types';

/**
 * Get color class for damage severity
 */
export function getSeverityColor(severity: SeverityLevel | string): string {
  const colors: Record<string, string> = {
    baja: 'text-success-700 bg-success-50 dark:bg-success-500/20 dark:text-success-200',
    media: 'text-warning-700 bg-warning-50 dark:bg-warning-500/20 dark:text-warning-200',
    alta: 'text-danger-700 bg-danger-50 dark:bg-danger-500/20 dark:text-danger-200',
  };
  return colors[String(severity).toLowerCase()] || 'text-gray-700 bg-gray-50 dark:bg-gray-700/40 dark:text-gray-100';
}

/**
 * Get color class for incident status (Spanish frontend enums)
 */
export function getStatusColor(status: IncidentStatus | string): string {
  const colors: Record<string, string> = {
    // Spanish (legacy frontend enums)
    reportado: 'text-gray-700 bg-gray-50 dark:bg-gray-700/40 dark:text-gray-100',
    asignado: 'text-blue-700 bg-blue-50 dark:bg-blue-500/20 dark:text-blue-200',
    en_progreso: 'text-warning-700 bg-warning-50 dark:bg-warning-500/20 dark:text-warning-200',
    completado: 'text-success-700 bg-success-50 dark:bg-success-500/20 dark:text-success-200',
    verificado: 'text-primary-700 bg-primary-50 dark:bg-primary-500/20 dark:text-primary-200',
    cerrado: 'text-gray-700 bg-gray-100 dark:bg-gray-700/40 dark:text-gray-100',
    // English (backend API values)
    open: 'text-gray-700 bg-gray-50 dark:bg-gray-700/40 dark:text-gray-100',
    assigned: 'text-blue-700 bg-blue-50 dark:bg-blue-500/20 dark:text-blue-200',
    in_progress: 'text-warning-700 bg-warning-50 dark:bg-warning-500/20 dark:text-warning-200',
    resolved: 'text-success-700 bg-success-50 dark:bg-success-500/20 dark:text-success-200',
    verified: 'text-primary-700 bg-primary-50 dark:bg-primary-500/20 dark:text-primary-200',
    closed: 'text-gray-700 bg-gray-100 dark:bg-gray-700/40 dark:text-gray-100',
  };
  return colors[String(status).toLowerCase()] || 'text-gray-700 bg-gray-50 dark:bg-gray-700/40 dark:text-gray-100';
}

/**
 * Get color class for report status
 */
export function getReportStatusColor(status: ReportStatus | string): string {
  const colors: Record<string, string> = {
    pendiente: 'text-warning-700 bg-warning-50 dark:bg-warning-500/20 dark:text-warning-200',
    en_revision: 'text-blue-700 bg-blue-50 dark:bg-blue-500/20 dark:text-blue-200',
    aprobado: 'text-success-700 bg-success-50 dark:bg-success-500/20 dark:text-success-200',
    rechazado: 'text-danger-700 bg-danger-50 dark:bg-danger-500/20 dark:text-danger-200',
    duplicado: 'text-gray-700 bg-gray-100 dark:bg-gray-700/40 dark:text-gray-100',
  };
  return colors[String(status).toLowerCase()] || 'text-gray-700 bg-gray-50 dark:bg-gray-700/40 dark:text-gray-100';
}

/**
 * Get human-readable labels
 */
export function getDamageClassLabel(damageClass: DamageClass | string): string {
  const labels: Record<string, string> = {
    bache: 'Bache',
    grieta: 'Grieta',
  };
  return labels[String(damageClass).toLowerCase()] || String(damageClass);
}

export function getSeverityLabel(severity: SeverityLevel | string): string {
  const labels: Record<string, string> = {
    baja: 'Baja',
    media: 'Media',
    alta: 'Alta',
  };
  return labels[String(severity).toLowerCase()] || String(severity);
}

export function getStatusLabel(status: IncidentStatus | string): string {
  const labels: Record<string, string> = {
    // Spanish
    reportado: 'Reportado',
    asignado: 'Asignado',
    en_progreso: 'En Progreso',
    completado: 'Completado',
    verificado: 'Verificado',
    cerrado: 'Cerrado',
    // English (backend API)
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
  const labels: Record<string, string> = {
    baja: 'Baja',
    media: 'Media',
    alta: 'Alta',
    critica: 'Crítica',
  };
  return labels[String(priority).toLowerCase()] || String(priority);
}

export function getPriorityColor(priority: string): string {
  const colors: Record<string, string> = {
    baja: 'text-blue-700 bg-blue-50 dark:bg-blue-500/20 dark:text-blue-200',
    media: 'text-amber-700 bg-amber-50 dark:bg-amber-500/20 dark:text-amber-200',
    alta: 'text-orange-700 bg-orange-50 dark:bg-orange-500/20 dark:text-orange-200',
    critica: 'text-red-700 bg-red-50 dark:bg-red-500/20 dark:text-red-200',
  };
  return colors[String(priority).toLowerCase()] || 'text-gray-700 bg-gray-50 dark:bg-gray-700/40 dark:text-gray-100';
}

export function getReportStatusLabel(status: ReportStatus | string): string {
  const labels: Record<string, string> = {
    pendiente: 'Pendiente',
    en_revision: 'En Revisión',
    aprobado: 'Aprobado',
    rechazado: 'Rechazado',
    duplicado: 'Duplicado',
  };
  return labels[String(status).toLowerCase()] || String(status);
}
