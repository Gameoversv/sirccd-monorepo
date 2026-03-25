'use client';

import { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet.heat';

// Type augmentation for leaflet.heat
declare module 'leaflet' {
  function heatLayer(
    latlngs: Array<[number, number, number?]>,
    options?: HeatMapOptions,
  ): HeatLayer;

  interface HeatMapOptions {
    minOpacity?: number;
    maxZoom?: number;
    max?: number;
    radius?: number;
    blur?: number;
    gradient?: Record<number, string>;
  }

  interface HeatLayer extends L.Layer {
    setLatLngs(latlngs: Array<[number, number, number?]>): this;
    addLatLng(latlng: [number, number, number?]): this;
    setOptions(options: HeatMapOptions): this;
    redraw(): this;
  }
}

interface HeatmapLayerProps {
  /** Array of [lat, lng, intensity] */
  points: Array<[number, number, number]>;
  /** Whether the layer is visible */
  visible: boolean;
}

/**
 * React-Leaflet wrapper for leaflet.heat.
 * Renders a heatmap overlay when `visible` is true.
 */
export function HeatmapLayer({ points, visible }: HeatmapLayerProps) {
  const map = useMap();

  useEffect(() => {
    if (!visible || points.length === 0) return;

    const heat = L.heatLayer(points, {
      radius: 25,
      blur: 20,
      maxZoom: 17,
      minOpacity: 0.4,
      gradient: {
        0.2: '#2563eb', // blue-600
        0.4: '#06b6d4', // cyan-500
        0.6: '#22c55e', // green-500
        0.8: '#f59e0b', // amber-500
        1.0: '#dc2626', // red-600
      },
    });

    heat.addTo(map);

    return () => {
      map.removeLayer(heat);
    };
  }, [map, points, visible]);

  return null;
}
