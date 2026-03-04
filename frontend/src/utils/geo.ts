import type { GeoPoint } from '@/types';

/**
 * Calculate distance between two points using Haversine formula
 * Returns distance in meters
 */
export function calculateDistance(
  point1: GeoPoint,
  point2: GeoPoint
): number {
  const R = 6371e3; // Earth's radius in meters
  const φ1 = (point1.coordinates[1] * Math.PI) / 180;
  const φ2 = (point2.coordinates[1] * Math.PI) / 180;
  const Δφ = ((point2.coordinates[1] - point1.coordinates[1]) * Math.PI) / 180;
  const Δλ = ((point2.coordinates[0] - point1.coordinates[0]) * Math.PI) / 180;

  const a =
    Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
    Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  return R * c;
}

/**
 * Format distance to human-readable string
 */
export function formatDistance(meters: number): string {
  if (meters < 1000) {
    return `${Math.round(meters)}m`;
  }
  return `${(meters / 1000).toFixed(1)}km`;
}

/**
 * Convert GeoPoint to [lat, lng] for Leaflet
 */
export function geoPointToLatLng(point: GeoPoint): [number, number] {
  return [point.coordinates[1], point.coordinates[0]];
}

/**
 * Convert [lat, lng] to GeoPoint
 */
export function latLngToGeoPoint(lat: number, lng: number): GeoPoint {
  return {
    type: 'Point',
    coordinates: [lng, lat],
  };
}
