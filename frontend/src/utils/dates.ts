import { format, formatDistanceToNow, parseISO } from 'date-fns';
import { es } from 'date-fns/locale';

/**
 * Format date to readable string
 */
export function formatDate(date: string | Date, formatStr: string = 'PPP'): string {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return format(dateObj, formatStr, { locale: es });
}

/**
 * Format date to relative time (e.g., "hace 2 horas")
 */
export function formatRelativeTime(date: string | Date): string {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return formatDistanceToNow(dateObj, { addSuffix: true, locale: es });
}

/**
 * Format date to ISO string for API
 */
export function toISOString(date: Date): string {
  return date.toISOString();
}
