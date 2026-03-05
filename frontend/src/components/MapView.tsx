'use client';

import { useEffect, useState, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import { Icon, LatLngExpression } from 'leaflet';
import { incidentsService } from '@/services';
import type { IncidentFilters } from '@/types';
import { Loader2, MapPin, AlertTriangle, Clock } from 'lucide-react';
import 'leaflet/dist/leaflet.css';

// Fix for default marker icons in React-Leaflet
// @ts-ignore
delete Icon.Default.prototype._getIconUrl;
Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface IncidentMarker {
  id: number;
  report_id: number;
  latitude: number;
  longitude: number;
  address?: string;
  city?: string;
  damage_type: string;
  severity: string;
  priority: string;
  priority_score?: number;
  status: string;
  created_at: string;
}

interface MapViewProps {
  height?: string;
  center?: LatLngExpression;
  zoom?: number;
  filters?: IncidentFilters;
  onIncidentsLoaded?: (incidents: IncidentMarker[]) => void;
}

// Component to recenter map when center prop changes
function MapUpdater({ center }: { center: LatLngExpression }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center, map.getZoom());
  }, [center, map]);
  return null;
}

// Helper to get marker color based on priority
function getPriorityColor(priority: string): string {
  switch (priority.toLowerCase()) {
    case 'critica':
      return '#dc2626'; // red-600
    case 'alta':
      return '#ea580c'; // orange-600
    case 'media':
      return '#f59e0b'; // amber-500
    case 'baja':
      return '#3b82f6'; // blue-500
    default:
      return '#6b7280'; // gray-500
  }
}

// Helper to get status badge color
function getStatusColor(status: string): string {
  switch (status.toLowerCase()) {
    case 'reportado':
      return 'bg-blue-100 text-blue-800';
    case 'asignado':
      return 'bg-purple-100 text-purple-800';
    case 'en_progreso':
      return 'bg-yellow-100 text-yellow-800';
    case 'completado':
      return 'bg-green-100 text-green-800';
    case 'verificado':
      return 'bg-emerald-100 text-emerald-800';
    case 'cerrado':
      return 'bg-gray-100 text-gray-800';
    default:
      return 'bg-gray-100 text-gray-600';
  }
}

// Helper to format status text
function formatStatus(status: string): string {
  return status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

// Helper to format date
function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('es-ES', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

export function MapView({ 
  height = '500px', 
  center = [18.4861, -69.9312], // Santo Domingo, RD default
  zoom = 13,
  filters = {},
  onIncidentsLoaded,
}: MapViewProps) {
  const [allIncidents, setAllIncidents] = useState<IncidentMarker[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Build API-level filters (severity, status, dates)
  const apiFilters: IncidentFilters = useMemo(() => {
    const f: IncidentFilters = {};
    if (filters.severity) f.severity = filters.severity;
    if (filters.status) f.status = filters.status;
    if (filters.date_from) f.date_from = filters.date_from;
    if (filters.date_to) f.date_to = filters.date_to;
    if (filters.damage_class) f.damage_class = filters.damage_class;
    return f;
  }, [filters.severity, filters.status, filters.date_from, filters.date_to, filters.damage_class]);

  useEffect(() => {
    loadIncidents();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [apiFilters]);

  // Client-side priority score filtering
  const incidents = useMemo(() => {
    let result = allIncidents;
    if (filters.priority_min != null) {
      result = result.filter((i) => (i.priority_score ?? 0) >= filters.priority_min!);
    }
    if (filters.priority_max != null) {
      result = result.filter((i) => (i.priority_score ?? 0) <= filters.priority_max!);
    }
    return result;
  }, [allIncidents, filters.priority_min, filters.priority_max]);

  // Notify parent of filtered incidents
  useEffect(() => {
    onIncidentsLoaded?.(incidents);
  }, [incidents, onIncidentsLoaded]);

  const loadIncidents = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Get incidents from API with applied filters
      const response = await incidentsService.getIncidents(apiFilters, 1, 500);
      
      // Access the incidents array (backend returns .incidents, not .items)
      const incidentsData = (response as any).incidents || [];
      
      // Transform to marker format
      const markers: IncidentMarker[] = incidentsData
        .filter((inc: any) => inc.latitude && inc.longitude)
        .map((inc: any) => ({
          id: inc.id,
          report_id: inc.report_id,
          latitude: inc.latitude,
          longitude: inc.longitude,
          address: inc.address,
          city: inc.city,
          damage_type: inc.damage_type,
          severity: inc.severity,
          priority: inc.priority,
          priority_score: inc.priority_score,
          status: inc.status,
          created_at: inc.created_at,
        }));
      
      setAllIncidents(markers);
    } catch (err: any) {
      console.error('Error loading incidents:', err);
      setError(err.response?.data?.detail || 'Error al cargar incidentes');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div 
        className="flex items-center justify-center bg-gray-100 rounded-lg"
        style={{ height }}
      >
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto" />
          <p className="mt-2 text-sm text-gray-600">Cargando mapa...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div 
        className="flex items-center justify-center bg-red-50 rounded-lg border border-red-200"
        style={{ height }}
      >
        <div className="text-center px-4">
          <AlertTriangle className="w-8 h-8 text-red-600 mx-auto" />
          <p className="mt-2 text-sm text-red-600">{error}</p>
          <button
            onClick={loadIncidents}
            className="mt-3 px-4 py-2 bg-red-600 text-white text-sm rounded hover:bg-red-700 transition-colors"
          >
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="relative rounded-lg overflow-hidden shadow-lg" style={{ height }}>
      <MapContainer
        center={center}
        zoom={zoom}
        scrollWheelZoom={true}
        className="w-full h-full z-0"
      >
        <MapUpdater center={center} />
        
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {incidents.map((incident) => {
          const position: LatLngExpression = [incident.latitude, incident.longitude];
          const priorityColor = getPriorityColor(incident.priority);
          
          // Create custom colored marker
          const customIcon = new Icon({
            iconUrl: `data:image/svg+xml;base64,${btoa(`
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 36" width="24" height="36">
                <path fill="${priorityColor}" stroke="#fff" stroke-width="2" 
                  d="M12 0C7.03 0 3 4.03 3 9c0 7.5 9 18 9 18s9-10.5 9-18c0-4.97-4.03-9-9-9z"/>
                <circle cx="12" cy="9" r="4" fill="#fff"/>
              </svg>
            `)}`,
            iconSize: [24, 36],
            iconAnchor: [12, 36],
            popupAnchor: [0, -36],
          });

          return (
            <Marker 
              key={incident.id} 
              position={position}
              icon={customIcon}
            >
              <Popup>
                <div className="min-w-[250px] p-2">
                  {/* Header */}
                  <div className="flex items-start justify-between gap-2 mb-3">
                    <div>
                      <h3 className="font-semibold text-gray-900">
                        Incidente #{incident.id}
                      </h3>
                      <p className="text-xs text-gray-500">
                        Reporte #{incident.report_id}
                      </p>
                    </div>
                    <span className={`px-2 py-1 text-xs font-medium rounded ${getStatusColor(incident.status)}`}>
                      {formatStatus(incident.status)}
                    </span>
                  </div>

                  {/* Location */}
                  <div className="flex items-start gap-2 mb-2">
                    <MapPin className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
                    <div className="text-sm">
                      <p className="text-gray-700">{incident.address || 'Dirección no disponible'}</p>
                      {incident.city && (
                        <p className="text-gray-500 text-xs">{incident.city}</p>
                      )}
                    </div>
                  </div>

                  {/* Damage info */}
                  <div className="grid grid-cols-2 gap-2 mb-3 text-sm">
                    <div>
                      <span className="text-gray-500 text-xs">Tipo:</span>
                      <p className="font-medium text-gray-700 capitalize">
                        {incident.damage_type}
                      </p>
                    </div>
                    <div>
                      <span className="text-gray-500 text-xs">Severidad:</span>
                      <p className="font-medium text-gray-700 capitalize">
                        {incident.severity}
                      </p>
                    </div>
                  </div>

                  {/* Priority */}
                  <div className="flex items-center gap-2 mb-3 pb-3 border-b border-gray-200">
                    <AlertTriangle className="w-4 h-4" style={{ color: priorityColor }} />
                    <div className="flex-1">
                      <span className="text-xs text-gray-500">Prioridad:</span>
                      <p className="font-semibold capitalize" style={{ color: priorityColor }}>
                        {incident.priority}
                      </p>
                    </div>
                    {incident.priority_score && (
                      <div className="text-right">
                        <span className="text-xl font-bold text-gray-700">
                          {incident.priority_score.toFixed(1)}
                        </span>
                        <p className="text-xs text-gray-500">score</p>
                      </div>
                    )}
                  </div>

                  {/* Date */}
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    <Clock className="w-3 h-3" />
                    <span>Reportado: {formatDate(incident.created_at)}</span>
                  </div>

                  {/* View details link */}
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <a
                      href={`/dashboard/incidents/${incident.id}`}
                      className="block w-full text-center px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded transition-colors"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Ver detalles
                    </a>
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>

      {/* Map legend */}
      <div className="absolute bottom-4 right-4 bg-white rounded-lg shadow-lg p-3 z-[1000]">
        <h4 className="text-xs font-semibold text-gray-700 mb-2">Prioridad</h4>
        <div className="space-y-1.5">
          {[
            { label: 'Crítica', color: getPriorityColor('critica') },
            { label: 'Alta', color: getPriorityColor('alta') },
            { label: 'Media', color: getPriorityColor('media') },
            { label: 'Baja', color: getPriorityColor('baja') },
          ].map((item) => (
            <div key={item.label} className="flex items-center gap-2">
              <div 
                className="w-3 h-3 rounded-full border border-white shadow-sm"
                style={{ backgroundColor: item.color }}
              />
              <span className="text-xs text-gray-600">{item.label}</span>
            </div>
          ))}
        </div>
        
        {/* Incident count */}
        <div className="mt-3 pt-3 border-t border-gray-200">
          <p className="text-xs text-gray-500">
            <span className="font-semibold text-gray-700">{incidents.length}</span> incidentes
          </p>
        </div>
      </div>
    </div>
  );
}
