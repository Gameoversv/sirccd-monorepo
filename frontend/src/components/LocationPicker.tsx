'use client';

import { useState } from 'react';
import { MapPin, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';

export interface Coordinates {
  latitude: number | null;
  longitude: number | null;
}

export interface ResolvedAddress {
  address: string;
  city: string;
  province: string;
}

interface LocationPickerProps {
  value: Coordinates;
  onChange: (coords: Coordinates) => void;
  onAddressResolved?: (address: ResolvedAddress) => void;
  latError?: string;
  lngError?: string;
}

async function reverseGeocode(lat: number, lon: number): Promise<ResolvedAddress> {
  const url = `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json&addressdetails=1`;
  const res = await fetch(url, {
    headers: { 'Accept-Language': 'es', 'User-Agent': 'sirccd-app' },
  });
  if (!res.ok) throw new Error('No se pudo consultar la dirección.');
  const data = await res.json();
  const a = data.address ?? {};

  const road = [a.road, a.house_number].filter(Boolean).join(' ');
  const suburb = a.suburb || a.neighbourhood || '';
  const addressStr = [road, suburb].filter(Boolean).join(', ') || data.display_name?.split(',')[0] || '';

  const city =
    a.city || a.town || a.village || a.municipality || a.county || '';
  const province =
    a.state || a.region || a.province || '';

  return { address: addressStr, city, province };
}

export function LocationPicker({
  value,
  onChange,
  onAddressResolved,
  latError,
  lngError,
}: LocationPickerProps) {
  const [loading, setLoading] = useState(false);
  const [geoError, setGeoError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [geocoding, setGeocoding] = useState(false);

  const handleGeolocate = () => {
    if (!navigator.geolocation) {
      setGeoError('Tu navegador no soporta geolocalización.');
      return;
    }
    setLoading(true);
    setGeoError(null);
    setSuccess(false);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const lat = parseFloat(pos.coords.latitude.toFixed(6));
        const lon = parseFloat(pos.coords.longitude.toFixed(6));
        onChange({ latitude: lat, longitude: lon });
        setLoading(false);
        setSuccess(true);

        if (onAddressResolved) {
          setGeocoding(true);
          try {
            const resolved = await reverseGeocode(lat, lon);
            onAddressResolved(resolved);
          } catch {
            // silently ignore — fields remain editable
          } finally {
            setGeocoding(false);
          }
        }
      },
      (err) => {
        setLoading(false);
        switch (err.code) {
          case err.PERMISSION_DENIED:
            setGeoError('Permiso de ubicación denegado. Ingrésala manualmente.');
            break;
          case err.POSITION_UNAVAILABLE:
            setGeoError('Ubicación no disponible. Ingrésala manualmente.');
            break;
          case err.TIMEOUT:
            setGeoError('Tiempo de espera agotado. Ingrésala manualmente.');
            break;
          default:
            setGeoError('Error al obtener ubicación. Ingrésala manualmente.');
        }
      },
      { timeout: 10000, maximumAge: 60000 }
    );
  };

  const handleLatChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value === '' ? null : parseFloat(e.target.value);
    onChange({ ...value, latitude: v });
    setSuccess(false);
  };

  const handleLngChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value === '' ? null : parseFloat(e.target.value);
    onChange({ ...value, longitude: v });
    setSuccess(false);
  };

  return (
    <div className="space-y-3">
      <button
        type="button"
        onClick={handleGeolocate}
        disabled={loading}
        className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white text-sm font-medium rounded-lg transition-colors"
      >
        {loading ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <MapPin className="w-4 h-4" />
        )}
        {loading ? 'Obteniendo ubicación…' : 'Usar mi ubicación'}
      </button>

      {success && !geoError && (
        <p className="text-green-600 text-sm flex items-center gap-1">
          <CheckCircle2 className="w-4 h-4" />
          {geocoding
            ? 'Obteniendo dirección…'
            : 'Ubicación y dirección obtenidas exitosamente.'}
        </p>
      )}

      {geoError && (
        <p className="text-red-500 text-sm flex items-center gap-1">
          <AlertCircle className="w-4 h-4" />
          {geoError}
        </p>
      )}

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Latitud <span className="text-red-500">*</span>
          </label>
          <input
            type="number"
            step="any"
            min="-90"
            max="90"
            placeholder="-90 a 90"
            value={value.latitude ?? ''}
            onChange={handleLatChange}
            className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              latError ? 'border-red-400' : 'border-gray-300'
            }`}
          />
          {latError && (
            <p className="text-red-500 text-xs mt-1 flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />
              {latError}
            </p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Longitud <span className="text-red-500">*</span>
          </label>
          <input
            type="number"
            step="any"
            min="-180"
            max="180"
            placeholder="-180 a 180"
            value={value.longitude ?? ''}
            onChange={handleLngChange}
            className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              lngError ? 'border-red-400' : 'border-gray-300'
            }`}
          />
          {lngError && (
            <p className="text-red-500 text-xs mt-1 flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />
              {lngError}
            </p>
          )}
        </div>
      </div>

      <p className="text-xs text-gray-500">
        El botón detecta tu ubicación y rellena la dirección automáticamente. También puedes
        ingresar las coordenadas manualmente.
      </p>
    </div>
  );
}
