'use client';

import { useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import dynamic from 'next/dynamic';
import { ChevronLeft, Send } from 'lucide-react';

const MiniMap = dynamic(() => import('@/components/MiniMap'), { ssr: false });
import { ImageUpload } from '@/components/ImageUpload';
import { LocationPicker, type Coordinates, type ResolvedAddress } from '@/components/LocationPicker';
import { reportsService } from '@/services/reportsService';
import { useAuthStore } from '@/store';
import { useToast } from '@/hooks';

interface FormErrors {
  image?: string;
  latitude?: string;
  longitude?: string;
  description?: string;
  address?: string;
  city?: string;
  province?: string;
}

export default function NewReportPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const toast = useToast();

  const [image, setImage] = useState<File | null>(null);
  const [coords, setCoords] = useState<Coordinates>({ latitude: null, longitude: null });
  const [description, setDescription] = useState('');
  const [address, setAddress] = useState('');
  const [city, setCity] = useState('');
  const [province, setProvince] = useState('');
  const [errors, setErrors] = useState<FormErrors>({});
  const [submitting, setSubmitting] = useState(false);

  if (!isAuthenticated) {
    router.replace('/auth/login');
    return null;
  }

  const validate = (): boolean => {
    const newErrors: FormErrors = {};

    if (!image) {
      newErrors.image = 'Debes seleccionar una imagen.';
    }

    if (coords.latitude === null || coords.latitude === undefined || isNaN(coords.latitude)) {
      newErrors.latitude = 'La latitud es requerida.';
    } else if (coords.latitude < -90 || coords.latitude > 90) {
      newErrors.latitude = 'La latitud debe estar entre -90 y 90.';
    }

    if (coords.longitude === null || coords.longitude === undefined || isNaN(coords.longitude)) {
      newErrors.longitude = 'La longitud es requerida.';
    } else if (coords.longitude < -180 || coords.longitude > 180) {
      newErrors.longitude = 'La longitud debe estar entre -180 y 180.';
    }

    if (description.length > 2000) {
      newErrors.description = 'La descripción no puede superar 2000 caracteres.';
    }

    if (address.length > 500) {
      newErrors.address = 'La dirección no puede superar 500 caracteres.';
    }

    if (city.length > 100) {
      newErrors.city = 'La ciudad no puede superar 100 caracteres.';
    }

    if (province.length > 100) {
      newErrors.province = 'La provincia no puede superar 100 caracteres.';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleAddressResolved = (resolved: ResolvedAddress) => {
    if (resolved.address) setAddress(resolved.address);
    if (resolved.city) setCity(resolved.city);
    if (resolved.province) setProvince(resolved.province);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) {
      toast.error('Por favor corrija los errores antes de enviar.');
      return;
    }

    setSubmitting(true);
    try {
      const formData = new FormData();
      formData.append('image', image!);
      formData.append('latitude', String(coords.latitude));
      formData.append('longitude', String(coords.longitude));
      if (description) formData.append('description', description);
      if (address) formData.append('address', address);
      if (city) formData.append('city', city);
      if (province) formData.append('province', province);

      await reportsService.createReport(formData);
      toast.success('Reporte creado exitosamente.');
      router.push('/dashboard');
    } catch (err: any) {
      const message = err?.detail ?? err?.message ?? 'Error al crear el reporte.';
      toast.error(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      {/* Back link */}
      <Link
        href="/dashboard"
        className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-6"
      >
        <ChevronLeft className="w-4 h-4" />
        Volver al dashboard
      </Link>

      <h1 className="text-2xl font-bold text-gray-900 mb-6">Crear Reporte</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Image */}
        <section className="bg-white rounded-lg shadow p-6 space-y-2">
          <h2 className="text-base font-semibold text-gray-800">
            Imagen <span className="text-red-500">*</span>
          </h2>
          <p className="text-sm text-gray-500">Captura o sube una foto del bache / daño vial.</p>
          <ImageUpload value={image} onChange={setImage} error={errors.image} />
        </section>

        {/* Location */}
        <section className="bg-white rounded-lg shadow p-6 space-y-2">
          <h2 className="text-base font-semibold text-gray-800">
            Ubicación <span className="text-red-500">*</span>
          </h2>
          <p className="text-sm text-gray-500">Obtén tu ubicación automáticamente o ingrésala manualmente.</p>
          <LocationPicker
            value={coords}
            onChange={setCoords}
            onAddressResolved={handleAddressResolved}
            latError={errors.latitude}
            lngError={errors.longitude}
          />
          {coords.latitude != null && coords.longitude != null && (
            <div className="mt-3 rounded-lg overflow-hidden border border-gray-200">
              <MiniMap
                lat={coords.latitude}
                lng={coords.longitude}
                label={address || 'Ubicación seleccionada'}
                height="200px"
                zoom={16}
              />
            </div>
          )}
        </section>

        {/* Address details */}
        <section className="bg-white rounded-lg shadow p-6 space-y-4">
          <div>
            <h2 className="text-base font-semibold text-gray-800">Detalles de dirección</h2>
            <p className="text-sm text-gray-500 mt-0.5">
              Se rellenan automáticamente al usar <span className="font-medium">Usar mi ubicación</span>. Puedes editarlos.
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Dirección</label>
            <input
              type="text"
              maxLength={500}
              placeholder="Calle, número, referencia…"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.address ? 'border-red-400' : 'border-gray-300'
              }`}
            />
            {errors.address && (
              <p className="text-red-500 text-xs mt-1">{errors.address}</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Ciudad</label>
              <input
                type="text"
                maxLength={100}
                placeholder="Ciudad"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.city ? 'border-red-400' : 'border-gray-300'
                }`}
              />
              {errors.city && (
                <p className="text-red-500 text-xs mt-1">{errors.city}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Provincia</label>
              <input
                type="text"
                maxLength={100}
                placeholder="Provincia"
                value={province}
                onChange={(e) => setProvince(e.target.value)}
                className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.province ? 'border-red-400' : 'border-gray-300'
                }`}
              />
              {errors.province && (
                <p className="text-red-500 text-xs mt-1">{errors.province}</p>
              )}
            </div>
          </div>
        </section>

        {/* Description */}
        <section className="bg-white rounded-lg shadow p-6 space-y-2">
          <h2 className="text-base font-semibold text-gray-800">Descripción</h2>
          <div className="relative">
            <textarea
              rows={4}
              maxLength={2000}
              placeholder="Describe el problema vial: tamaño, profundidad, riesgos…"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none ${
                errors.description ? 'border-red-400' : 'border-gray-300'
              }`}
            />
            <span
              className={`absolute bottom-2 right-3 text-xs ${
                description.length > 1900 ? 'text-red-500' : 'text-gray-400'
              }`}
            >
              {description.length}/2000
            </span>
          </div>
          {errors.description && (
            <p className="text-red-500 text-xs">{errors.description}</p>
          )}
        </section>

        {/* Submit */}
        <div className="flex justify-end gap-3">
          <Link
            href="/dashboard"
            className="px-5 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Cancelar
          </Link>
          <button
            type="submit"
            disabled={submitting}
            className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 rounded-lg transition-colors"
          >
            {submitting ? (
              <>
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Enviando…
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                Crear reporte
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
