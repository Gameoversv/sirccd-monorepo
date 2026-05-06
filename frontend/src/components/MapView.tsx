'use client';

import { useEffect, useState, useMemo, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, Circle, CircleMarker } from 'react-leaflet';
import { Icon, LatLngExpression } from 'leaflet';
import { incidentsService, poisService } from '@/services';
import type { IncidentFilters, POILayerFilters, POILayerCategory, POILayerItem } from '@/types';
import { Loader2, MapPin, AlertTriangle, Clock, Flame } from 'lucide-react';
import { HeatmapLayer } from './HeatmapLayer';
import { useTranslation } from 'react-i18next';
import { getPriorityLabel, getStatusLabel, getSeverityLabel, getDamageClassLabel } from '@/utils';
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
  poiLayerFilters?: POILayerFilters;
  onIncidentsLoaded?: (incidents: IncidentMarker[]) => void;
}

const DEFAULT_POI_LAYER_FILTERS: POILayerFilters = {
  showPOIs: false,
  showRiskBuffers: false,
  bufferRadiusMeters: 120,
  categories: {
    school: true,
    hospital: true,
    fire_station: true,
    community_center: true,
  },
};

const POI_CATEGORY_COLORS: Record<POILayerCategory, string> = {
  school: '#2563eb',
  hospital: '#dc2626',
  fire_station: '#ea580c',
  community_center: '#7c3aed',
};

const POI_CATEGORY_LABELS: Record<POILayerCategory, string> = {
  school: 'filters.poi.school',
  hospital: 'filters.poi.hospital',
  fire_station: 'filters.poi.fire_station',
  community_center: 'filters.poi.community_center',
};

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
    case 'critical':
      return '#dc2626'; // red-600
    case 'alta':
    case 'high':
      return '#ea580c'; // orange-600
    case 'media':
    case 'medium':
      return '#f59e0b'; // amber-500
    case 'baja':
    case 'low':
      return '#3b82f6'; // blue-500
    default:
      return '#6b7280'; // gray-500
  }
}

// Helper to get status badge color
function getStatusColor(status: string): string {
  switch (status.toLowerCase()) {
    case 'reportado':
    case 'open':
      return 'bg-blue-100 text-blue-800';
    case 'asignado':
    case 'assigned':
      return 'bg-purple-100 text-purple-800';
    case 'en_progreso':
    case 'in_progress':
      return 'bg-yellow-100 text-yellow-800';
    case 'completado':
    case 'resolved':
      return 'bg-green-100 text-green-800';
    case 'verificado':
    case 'verified':
      return 'bg-emerald-100 text-emerald-800';
    case 'cerrado':
    case 'closed':
      return 'bg-gray-100 text-gray-800';
    default:
      return 'bg-gray-100 text-gray-600';
  }
}

// Helper to format status text
// Helper to format date
function formatDate(dateString: string, locale: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString(locale, {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

export function MapView({ 
  height = '500px', 
  center = [19.4517, -70.6970], // Santiago de los Caballeros, RD default
  zoom = 13,
  filters = {},
  poiLayerFilters,
  onIncidentsLoaded,
}: MapViewProps) {
  const { t, i18n } = useTranslation();
  const dateLocale = i18n.language?.startsWith('en') ? 'en-US' : 'es-ES';

  const resolvedPoiLayerFilters = poiLayerFilters ?? DEFAULT_POI_LAYER_FILTERS;
  const [allIncidents, setAllIncidents] = useState<IncidentMarker[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Heatmap state (P-01)
  const [heatmapVisible, setHeatmapVisible] = useState(false);
  const [heatmapPoints, setHeatmapPoints] = useState<[number, number, number][]>([]);
  const [heatmapWeight, setHeatmapWeight] = useState<'frequency' | 'severity' | 'age'>('frequency');
  const [heatmapLoading, setHeatmapLoading] = useState(false);

  // POI layers (P-02)
  const [poiItems, setPoiItems] = useState<POILayerItem[]>([]);
  const [poiLoading, setPoiLoading] = useState(false);

  const activePoiCategories = useMemo(() => {
    return (Object.entries(resolvedPoiLayerFilters.categories) as Array<[POILayerCategory, boolean]>)
      .filter(([, enabled]) => enabled)
      .map(([category]) => category);
  }, [resolvedPoiLayerFilters.categories]);

  const poiLayerEnabled = resolvedPoiLayerFilters.showPOIs && activePoiCategories.length > 0;

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

  // Fetch heatmap data when toggled on or weight changes (P-01)
  const loadHeatmap = useCallback(async () => {
    if (!heatmapVisible) return;
    try {
      setHeatmapLoading(true);
      const svcFilters: { status?: string; damage_type?: string; severity?: string } = {};
      if (filters.status) svcFilters.status = filters.status;
      if (filters.damage_class) svcFilters.damage_type = filters.damage_class;
      if (filters.severity) svcFilters.severity = filters.severity;
      const data = await incidentsService.getHeatmapData(heatmapWeight, svcFilters);
      setHeatmapPoints(data.points);
    } catch {
      console.error('Error loading heatmap data');
    } finally {
      setHeatmapLoading(false);
    }
  }, [heatmapVisible, heatmapWeight, filters.status, filters.damage_class, filters.severity]);

  useEffect(() => {
    loadHeatmap();
  }, [loadHeatmap]);

  const loadPoiLayers = useCallback(async () => {
    if (!poiLayerEnabled) {
      setPoiItems([]);
      return;
    }

    try {
      setPoiLoading(true);
      const response = await poisService.getPOILayers({
        categories: activePoiCategories,
        limit: 1500,
      });
      setPoiItems(response.pois || []);
    } catch {
      console.error('Error loading POI layers');
      setPoiItems([]);
    } finally {
      setPoiLoading(false);
    }
  }, [poiLayerEnabled, activePoiCategories]);

  useEffect(() => {
    loadPoiLayers();
  }, [loadPoiLayers]);

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
      setError(err.response?.data?.detail || t('map.errorLoading'));
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
          <p className="mt-2 text-sm text-gray-600">{t('map.loading')}</p>
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
            {t('common.retry')}
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

        {/* Heatmap overlay (P-01) */}
        <HeatmapLayer points={heatmapPoints} visible={heatmapVisible} />

        {/* Pedestrian risk buffers around POIs (P-02) */}
        {poiLayerEnabled && resolvedPoiLayerFilters.showRiskBuffers &&
          poiItems.map((poi) => (
            <Circle
              key={`buffer-${poi.id}`}
              center={[poi.latitude, poi.longitude]}
              radius={resolvedPoiLayerFilters.bufferRadiusMeters}
              pathOptions={{
                color: POI_CATEGORY_COLORS[poi.category],
                fillColor: POI_CATEGORY_COLORS[poi.category],
                fillOpacity: 0.08,
                weight: 1,
                dashArray: '4 4',
              }}
            />
          ))}

        {/* POI markers (P-02) */}
        {poiLayerEnabled &&
          poiItems.map((poi) => (
            <CircleMarker
              key={`poi-${poi.id}`}
              center={[poi.latitude, poi.longitude]}
              radius={6}
              pathOptions={{
                color: '#ffffff',
                fillColor: POI_CATEGORY_COLORS[poi.category],
                fillOpacity: 0.95,
                weight: 1.5,
              }}
            >
              <Popup>
                <div className="min-w-[230px] p-1.5">
                  <h3 className="text-sm font-semibold text-gray-900">{poi.name}</h3>
                  <p className="text-xs text-gray-500 mt-1">{t(POI_CATEGORY_LABELS[poi.category])}</p>
                  {(poi.address || poi.city) && (
                    <p className="text-xs text-gray-600 mt-2">
                      {[poi.address, poi.city].filter(Boolean).join(' ? ')}
                    </p>
                  )}
                  <div className="mt-2 pt-2 border-t border-gray-200 text-xs text-gray-500">
                    {t('map.pedestrianBuffer')}: {resolvedPoiLayerFilters.bufferRadiusMeters} m
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          ))}
        
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
                        {t('incidents.detail.title', { id: incident.id })}
                      </h3>
                      <p className="text-xs text-gray-500">
                        {t('incidents.detail.reportRef', { id: incident.report_id })}
                      </p>
                    </div>
                    <span className={`px-2 py-1 text-xs font-medium rounded ${getStatusColor(incident.status)}`}>
                      {getStatusLabel(incident.status)}
                    </span>
                  </div>

                  {/* Location */}
                  <div className="flex items-start gap-2 mb-2">
                    <MapPin className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
                    <div className="text-sm">
                      <p className="text-gray-700">{incident.address || t('map.noAddress')}</p>
                      {incident.city && (
                        <p className="text-gray-500 text-xs">{incident.city}</p>
                      )}
                    </div>
                  </div>

                  {/* Damage info */}
                  <div className="grid grid-cols-2 gap-2 mb-3 text-sm">
                    <div>
                      <span className="text-gray-500 text-xs">{t('map.type')}:</span>
                      <p className="font-medium text-gray-700 capitalize">
                        {getDamageClassLabel(incident.damage_type)}
                      </p>
                    </div>
                    <div>
                      <span className="text-gray-500 text-xs">{t('map.severity')}:</span>
                      <p className="font-medium text-gray-700 capitalize">
                        {getSeverityLabel(incident.severity)}
                      </p>
                    </div>
                  </div>

                  {/* Priority */}
                  <div className="flex items-center gap-2 mb-3 pb-3 border-b border-gray-200">
                    <AlertTriangle className="w-4 h-4" style={{ color: priorityColor }} />
                    <div className="flex-1">
                      <span className="text-xs text-gray-500">{t('map.priority')}:</span>
                      <p className="font-semibold capitalize" style={{ color: priorityColor }}>
                        {getPriorityLabel(incident.priority)}
                      </p>
                    </div>
                    {incident.priority_score && (
                      <div className="text-right">
                        <span className="text-xl font-bold text-gray-700">
                          {incident.priority_score.toFixed(1)}
                        </span>
                        <p className="text-xs text-gray-500">{t('map.score')}</p>
                      </div>
                    )}
                  </div>

                  {/* Date */}
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    <Clock className="w-3 h-3" />
                    <span>{t('map.reported')}: {formatDate(incident.created_at, dateLocale)}</span>
                  </div>

                  {/* View details link */}
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <a
                      href={`/dashboard/incidents/${incident.id}`}
                      className="block w-full text-center px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded transition-colors"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {t('map.viewDetails')}
                    </a>
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>

      {/* Heatmap controls (P-01) */}
      <div className="absolute top-4 right-4 bg-white rounded-lg shadow-lg p-3 z-[1000] space-y-2">
        <button
          onClick={() => setHeatmapVisible((v) => !v)}
          className={`flex items-center gap-2 w-full px-3 py-2 text-xs font-medium rounded transition-colors ${
            heatmapVisible
              ? 'bg-orange-100 text-orange-700 border border-orange-300'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200 border border-gray-200'
          }`}
        >
          <Flame className="w-4 h-4" />
          {heatmapLoading
            ? t('map.heatmapLoading')
            : heatmapVisible
              ? t('map.hideHeatmap')
              : t('map.heatmap')}
        </button>

        {heatmapVisible && (
          <div className="space-y-1">
            <label className="text-[10px] font-medium text-gray-500 uppercase tracking-wide">
              {t('map.weightBy')}
            </label>
            <select
              value={heatmapWeight}
              onChange={(e) => setHeatmapWeight(e.target.value as 'frequency' | 'severity' | 'age')}
              className="w-full text-xs border border-gray-200 rounded px-2 py-1.5 bg-white focus:outline-none focus:ring-1 focus:ring-orange-400"
            >
              <option value="frequency">{t('map.frequency')}</option>
              <option value="severity">{t('map.severity')}</option>
              <option value="age">{t('map.age')}</option>
            </select>
            <p className="text-[10px] text-gray-400">
              {t('map.points', { count: heatmapPoints.length })}
            </p>
          </div>
        )}

        {poiLayerEnabled && (
          <div className="pt-2 border-t border-gray-200">
            <p className="text-[10px] text-gray-500 uppercase tracking-wide">POIs</p>
            <p className="text-[10px] text-gray-400">
                {poiLoading
                  ? t('map.loadingLayer')
                  : t('map.layerSummary', {
                    count: poiItems.length,
                    radius: resolvedPoiLayerFilters.bufferRadiusMeters,
                  })}
            </p>
          </div>
        )}
      </div>

      {/* Map legend */}
      <div className="absolute bottom-4 right-4 bg-white rounded-lg shadow-lg p-3 z-[1000]">
        <h4 className="text-xs font-semibold text-gray-700 mb-2">{t('map.priority')}</h4>
        <div className="space-y-1.5">
          {[
            { label: getPriorityLabel('critica'), color: getPriorityColor('critica') },
            { label: getPriorityLabel('alta'), color: getPriorityColor('alta') },
            { label: getPriorityLabel('media'), color: getPriorityColor('media') },
            { label: getPriorityLabel('baja'), color: getPriorityColor('baja') },
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
            <span className="font-semibold text-gray-700">{incidents.length}</span> {t('map.incidents')}
          </p>
        </div>

        {poiLayerEnabled && (
          <div className="mt-3 pt-3 border-t border-gray-200">
            <h4 className="text-xs font-semibold text-gray-700 mb-2">{t('map.poiRisk')}</h4>
            <div className="space-y-1.5">
              {activePoiCategories.map((category) => (
                <div key={category} className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full border border-white shadow-sm"
                    style={{ backgroundColor: POI_CATEGORY_COLORS[category] }}
                  />
                  <span className="text-xs text-gray-600">{t(POI_CATEGORY_LABELS[category])}</span>
                </div>
              ))}
            </div>
            {resolvedPoiLayerFilters.showRiskBuffers && (
              <p className="text-[10px] text-gray-500 mt-2">
                {t('map.activeBuffers')}: {resolvedPoiLayerFilters.bufferRadiusMeters} m
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
