'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import dynamic from 'next/dynamic';
import { ChevronLeft, Send } from 'lucide-react';
import { useTranslation } from 'react-i18next';

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
  const [isHydrated, setIsHydrated] = useState(false);

  const [image, setImage] = useState<File | null>(null);
  const [coords, setCoords] = useState<Coordinates>({ latitude: null, longitude: null });
  const [description, setDescription] = useState('');
  const [address, setAddress] = useState('');
  const [city, setCity] = useState('');
  const [province, setProvince] = useState('');
  const [errors, setErrors] = useState<FormErrors>({});
  const [submitting, setSubmitting] = useState(false);
  const { t } = useTranslation();

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  useEffect(() => {
    if (isHydrated && !isAuthenticated) {
      router.replace('/login');
    }
  }, [isHydrated, isAuthenticated, router]);

  if (!isHydrated || !isAuthenticated) {
    return null;
  }

  const validate = (): boolean => {
    const newErrors: FormErrors = {};

    if (!image) {
      newErrors.image = t('reports.new.errors.imageRequired');
    }

    if (coords.latitude === null || coords.latitude === undefined || isNaN(coords.latitude)) {
      newErrors.latitude = t('reports.new.errors.latRequired');
    } else if (coords.latitude < -90 || coords.latitude > 90) {
      newErrors.latitude = t('reports.new.errors.latInvalid');
    }

    if (coords.longitude === null || coords.longitude === undefined || isNaN(coords.longitude)) {
      newErrors.longitude = t('reports.new.errors.lngRequired');
    } else if (coords.longitude < -180 || coords.longitude > 180) {
      newErrors.longitude = t('reports.new.errors.lngInvalid');
    }

    if (description.length > 2000) {
      newErrors.description = t('reports.new.errors.descriptionMax');
    }

    if (address.length > 500) {
      newErrors.address = t('reports.new.errors.addressMax');
    }

    if (city.length > 100) {
      newErrors.city = t('reports.new.errors.cityMax');
    }

    if (province.length > 100) {
      newErrors.province = t('reports.new.errors.provinceMax');
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
      toast.error(t('reports.new.formError'));
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
      toast.success(t('reports.new.success'));
      router.push('/dashboard');
    } catch (err: any) {
      const message = err?.detail ?? err?.message ?? t('reports.detail.approveError');
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
        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-gray-700 mb-6"
      >
        <ChevronLeft className="w-4 h-4" />
        {t('nav.backToDashboard')}
      </Link>

      <h1 className="text-3xl font-bold tracking-tight mb-6">{t('reports.new.title')}</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Image */}
        <section className="rounded-xl border border-border bg-card p-6 shadow-soft space-y-2">
          <h2 className="text-base font-semibold tracking-tight">
            {t('reports.new.imageSection')} <span className="text-danger-500">*</span>
          </h2>
          <p className="text-sm text-muted-foreground">{t('reports.new.imageHint')}</p>
          <ImageUpload value={image} onChange={setImage} error={errors.image} />
        </section>

        {/* Location */}
        <section className="rounded-xl border border-border bg-card p-6 shadow-soft space-y-2">
          <h2 className="text-base font-semibold tracking-tight">
            {t('reports.new.locationSection')} <span className="text-danger-500">*</span>
          </h2>
          <p className="text-sm text-muted-foreground">{t('reports.new.locationHint')}</p>
          <LocationPicker
            value={coords}
            onChange={setCoords}
            onAddressResolved={handleAddressResolved}
            latError={errors.latitude}
            lngError={errors.longitude}
          />
          {coords.latitude != null && coords.longitude != null && (
            <div className="mt-3 rounded-lg overflow-hidden border border-border">
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
        <section className="rounded-xl border border-border bg-card p-6 shadow-soft space-y-4">
          <div>
            <h2 className="text-base font-semibold tracking-tight">{t('reports.new.addressSection')}</h2>
            <p className="text-sm text-muted-foreground mt-0.5" dangerouslySetInnerHTML={{ __html: t('reports.new.addressHint') }} />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1.5">{t('reports.new.addressLabel')}</label>
            <input
              type="text"
              maxLength={500}
              placeholder={t('reports.new.addressPlaceholder')}
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              className={`w-full rounded-lg border bg-card px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent transition-shadow ${
                errors.address ? 'border-danger-500/60' : 'border-border'
              }`}
            />
            {errors.address && (
              <p className="text-danger-500 text-xs mt-1">{errors.address}</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium mb-1.5">{t('reports.new.cityLabel')}</label>
              <input
                type="text"
                maxLength={100}
                placeholder="Ciudad"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                className={`w-full rounded-lg border bg-card px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent transition-shadow ${
                  errors.city ? 'border-danger-500/60' : 'border-border'
                }`}
              />
              {errors.city && (
                <p className="text-danger-500 text-xs mt-1">{errors.city}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium mb-1.5">{t('reports.new.provinceLabel')}</label>
              <input
                type="text"
                maxLength={100}
                placeholder="Provincia"
                value={province}
                onChange={(e) => setProvince(e.target.value)}
                className={`w-full rounded-lg border bg-card px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent transition-shadow ${
                  errors.province ? 'border-danger-500/60' : 'border-border'
                }`}
              />
              {errors.province && (
                <p className="text-danger-500 text-xs mt-1">{errors.province}</p>
              )}
            </div>
          </div>
        </section>

        {/* Description */}
        <section className="rounded-xl border border-border bg-card p-6 shadow-soft space-y-2">
          <h2 className="text-base font-semibold tracking-tight">{t('reports.new.descriptionSection')}</h2>
          <div className="relative">
            <textarea
              rows={4}
              maxLength={2000}
              placeholder={t('reports.new.descriptionPlaceholder')}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className={`w-full rounded-lg border bg-card px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent transition-shadow resize-none ${
                errors.description ? 'border-danger-500/60' : 'border-border'
              }`}
            />
            <span
              className={`absolute bottom-2 right-3 text-xs ${
                description.length > 1900 ? 'text-danger-500' : 'text-gray-400'
              }`}
            >
              {description.length}/2000
            </span>
          </div>
          {errors.description && (
            <p className="text-danger-500 text-xs">{errors.description}</p>
          )}
        </section>

        {/* Submit */}
        <div className="flex justify-end gap-3">
          <Link
            href="/dashboard"
            className="px-5 py-2.5 text-sm font-medium text-foreground bg-card border border-border rounded-lg hover:bg-muted transition-colors"
          >
            {t('common.cancel')}
          </Link>
          <button
            type="submit"
            disabled={submitting}
            className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-semibold text-white bg-gradient-brand hover:shadow-elevated shadow-soft rounded-lg transition-all active:scale-[0.99] disabled:opacity-60"
          >
            {submitting ? (
              <>
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                {t('reports.new.submitting')}
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                {t('reports.new.submit')}
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
