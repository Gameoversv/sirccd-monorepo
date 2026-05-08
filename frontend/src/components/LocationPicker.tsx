'use client';

import { useState } from 'react';
import { MapPin, Loader2, AlertCircle, CheckCircle2, Camera } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { reverseGeocode, type ResolvedAddress } from '@/lib/geocode';

export interface Coordinates {
  latitude: number | null;
  longitude: number | null;
}

export type { ResolvedAddress };

interface LocationPickerProps {
  value: Coordinates;
  onChange: (coords: Coordinates) => void;
  onAddressResolved?: (address: ResolvedAddress) => void;
  latError?: string;
  lngError?: string;
  locationSource?: 'exif' | 'gps' | null;
}

export function LocationPicker({
  value,
  onChange,
  onAddressResolved,
  latError,
  lngError,
  locationSource,
}: LocationPickerProps) {
  const { t, i18n } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [geoError, setGeoError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [geocoding, setGeocoding] = useState(false);

  const handleGeolocate = () => {
    if (!navigator.geolocation) {
      setGeoError(t('reports.new.geo.unsupported'));
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
            const lang = i18n.language?.toLowerCase().startsWith('en') ? 'en' : 'es';
            const resolved = await reverseGeocode(lat, lon, lang);
            onAddressResolved(resolved);
          } catch {
            // Keep fields editable if reverse geocode fails.
          } finally {
            setGeocoding(false);
          }
        }
      },
      (err) => {
        setLoading(false);
        switch (err.code) {
          case err.PERMISSION_DENIED:
            setGeoError(t('reports.new.geo.permissionDenied'));
            break;
          case err.POSITION_UNAVAILABLE:
            setGeoError(t('reports.new.geo.positionUnavailable'));
            break;
          case err.TIMEOUT:
            setGeoError(t('reports.new.geo.timeout'));
            break;
          default:
            setGeoError(t('reports.new.geo.genericError'));
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
        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <MapPin className="w-4 h-4" />}
        {loading ? t('reports.new.geo.gettingLocation') : t('reports.new.geo.useMyLocation')}
      </button>

      {success && !geoError && locationSource !== 'exif' && (
        <p className="text-green-600 text-sm flex items-center gap-1">
          <CheckCircle2 className="w-4 h-4" />
          {geocoding ? t('reports.new.geo.gettingAddress') : t('reports.new.geo.success')}
        </p>
      )}

      {locationSource === 'exif' && (
        <p className="text-blue-600 text-sm flex items-center gap-1">
          <Camera className="w-4 h-4" />
          {t('reports.new.geo.exifLocation')}
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
            {t('reports.new.geo.latitudeLabel')} <span className="text-red-500">*</span>
          </label>
          <input
            type="number"
            step="any"
            min="-90"
            max="90"
            placeholder={t('reports.new.geo.latitudePlaceholder')}
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
            {t('reports.new.geo.longitudeLabel')} <span className="text-red-500">*</span>
          </label>
          <input
            type="number"
            step="any"
            min="-180"
            max="180"
            placeholder={t('reports.new.geo.longitudePlaceholder')}
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

      <p className="text-xs text-gray-500">{t('reports.new.geo.helpText')}</p>
    </div>
  );
}
