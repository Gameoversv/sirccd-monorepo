import type { DamageClass, SeverityLevel, IncidentStatus, ReportStatus } from '@/types';

/**
 * Get color class for damage severity
 */
export function getSeverityColor(severity: SeverityLevel): string {
  const colors = {
    baja: 'text-success-700 bg-success-50',
    media: 'text-warning-700 bg-warning-50',
    alta: 'text-danger-700 bg-danger-50',
  };
  return colors[severity] || 'text-gray-700 bg-gray-50';
}

/**
 * Get color class for incident status
 */
export function getStatusColor(status: IncidentStatus): string {
  const colors = {
    reportado: 'text-gray-700 bg-gray-50',
    asignado: 'text-blue-700 bg-blue-50',
    en_progreso: 'text-warning-700 bg-warning-50',
    completado: 'text-success-700 bg-success-50',
    verificado: 'text-primary-700 bg-primary-50',
    cerrado: 'text-gray-700 bg-gray-100',
  };
  return colors[status] || 'text-gray-700 bg-gray-50';
}

/**
 * Get color class for report status
 */
export function getReportStatusColor(status: ReportStatus): string {
  const colors = {
    pendiente: 'text-warning-700 bg-warning-50',
    en_revision: 'text-blue-700 bg-blue-50',
    aprobado: 'text-success-700 bg-success-50',
    rechazado: 'text-danger-700 bg-danger-50',
    duplicado: 'text-gray-700 bg-gray-100',
  };
  return colors[status] || 'text-gray-700 bg-gray-50';
}

/**
 * Get human-readable labels
 */
export function getDamageClassLabel(damageClass: DamageClass): string {
  const labels = {
    bache: 'Bache',
    grieta: 'Grieta',
  };
  return labels[damageClass] || damageClass;
}

export function getSeverityLabel(severity: SeverityLevel): string {
  const labels = {
    baja: 'Baja',
    media: 'Media',
    alta: 'Alta',
  };
  return labels[severity] || severity;
}

export function getStatusLabel(status: IncidentStatus): string {
  const labels = {
    reportado: 'Reportado',
    asignado: 'Asignado',
    en_progreso: 'En Progreso',
    completado: 'Completado',
    verificado: 'Verificado',
    cerrado: 'Cerrado',
  };
  return labels[status] || status;
}

export function getReportStatusLabel(status: ReportStatus): string {
  const labels = {
    pendiente: 'Pendiente',
    en_revision: 'En Revisión',
    aprobado: 'Aprobado',
    rechazado: 'Rechazado',
    duplicado: 'Duplicado',
  };
  return labels[status] || status;
}
