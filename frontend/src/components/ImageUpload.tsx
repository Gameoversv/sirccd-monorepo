'use client';

import { useRef, useState, useCallback } from 'react';
import { ImageIcon, X, AlertCircle, ShieldAlert, ShieldCheck, Loader2 } from 'lucide-react';
import { reportsService } from '@/services';

const MAX_FILE_SIZE_MB = 10;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
const ALLOWED_EXTENSIONS = 'JPG, PNG, WEBP';

type PrivacyStatus = 'idle' | 'checking' | 'clean' | 'warning' | 'unavailable';

interface PrivacyResult {
  faces_detected: number;
  plates_detected: number;
  warnings: string[];
  message: string;
}

interface ImageUploadProps {
  value: File | null;
  onChange: (file: File | null) => void;
  error?: string;
}

export function ImageUpload({ value, onChange, error }: ImageUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [privacyStatus, setPrivacyStatus] = useState<PrivacyStatus>('idle');
  const [privacyResult, setPrivacyResult] = useState<PrivacyResult | null>(null);

  const validate = (file: File): string | null => {
    if (!ALLOWED_TYPES.includes(file.type)) {
      return `Formato no permitido. Solo ${ALLOWED_EXTENSIONS}.`;
    }
    if (file.size > MAX_FILE_SIZE_BYTES) {
      return `La imagen supera el tamaño máximo de ${MAX_FILE_SIZE_MB}MB.`;
    }
    return null;
  };

  const checkPrivacy = useCallback(async (file: File) => {
    setPrivacyStatus('checking');
    setPrivacyResult(null);
    try {
      const result = await reportsService.verifyImage(file);
      setPrivacyResult(result);
      if (result.error) {
        setPrivacyStatus('unavailable');
      } else if (result.is_clean) {
        setPrivacyStatus('clean');
      } else {
        setPrivacyStatus('warning');
      }
    } catch {
      // Verification endpoint unreachable — allow upload, server will anonymize anyway
      setPrivacyStatus('unavailable');
      setPrivacyResult(null);
    }
  }, []);

  const handleFile = useCallback(
    (file: File) => {
      const validationError = validate(file);
      if (validationError) {
        setLocalError(validationError);
        return;
      }
      setLocalError(null);
      onChange(file);
      const reader = new FileReader();
      reader.onload = (e) => setPreview(e.target?.result as string);
      reader.readAsDataURL(file);
      // Run privacy check in background after setting preview
      checkPrivacy(file);
    },
    [onChange, checkPrivacy]
  );

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  };

  const handleRemove = () => {
    onChange(null);
    setPreview(null);
    setLocalError(null);
    setPrivacyStatus('idle');
    setPrivacyResult(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  const displayError = error || localError;

  if (preview && value) {
    return (
      <div className="space-y-2">
        <div className="relative inline-block w-full">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={preview}
            alt="Previsualización"
            className="w-full max-h-96 object-contain rounded-lg border border-gray-200 bg-gray-50"
          />
          <button
            type="button"
            onClick={handleRemove}
            className="absolute top-2 right-2 bg-white rounded-full p-1 shadow-md hover:bg-red-50 transition-colors"
            aria-label="Eliminar imagen"
          >
            <X className="w-4 h-4 text-red-500" />
          </button>
          <div className="absolute bottom-2 left-2 bg-black/50 text-white text-xs px-2 py-1 rounded">
            {value.name} · {(value.size / 1024 / 1024).toFixed(2)}MB
          </div>
          {/* Privacy check badge overlaid on image */}
          {privacyStatus === 'checking' && (
            <div className="absolute top-2 left-2 bg-white/90 text-gray-700 text-xs px-2 py-1 rounded flex items-center gap-1 shadow">
              <Loader2 className="w-3 h-3 animate-spin" />
              Verificando privacidad...
            </div>
          )}
          {privacyStatus === 'clean' && (
            <div className="absolute top-2 left-2 bg-green-100/90 text-green-700 text-xs px-2 py-1 rounded flex items-center gap-1 shadow">
              <ShieldCheck className="w-3 h-3" />
              Sin elementos sensibles
            </div>
          )}
          {privacyStatus === 'warning' && (
            <div className="absolute top-2 left-2 bg-amber-100/90 text-amber-700 text-xs px-2 py-1 rounded flex items-center gap-1 shadow">
              <ShieldAlert className="w-3 h-3" />
              Elementos sensibles detectados
            </div>
          )}
        </div>

        {/* Privacy warning banner */}
        {privacyStatus === 'warning' && privacyResult && (
          <div className="rounded-lg border border-amber-300 bg-amber-50 p-3 space-y-1">
            <div className="flex items-center gap-2 text-amber-800 font-medium text-sm">
              <ShieldAlert className="w-4 h-4 shrink-0" />
              Aviso de privacidad
            </div>
            <ul className="text-amber-700 text-xs space-y-0.5 pl-6 list-disc">
              {privacyResult.warnings.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
            <p className="text-amber-600 text-xs pt-1">
              Puedes continuar — el servidor anonimizará estos elementos automáticamente antes de guardar.
            </p>
          </div>
        )}

        {displayError && (
          <p className="text-red-500 text-sm flex items-center gap-1">
            <AlertCircle className="w-4 h-4" />
            {displayError}
          </p>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          dragOver
            ? 'border-blue-500 bg-blue-50'
            : displayError
            ? 'border-red-400 bg-red-50'
            : 'border-gray-300 hover:border-blue-400 hover:bg-blue-50'
        }`}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
      >
        <ImageIcon className="w-10 h-10 mx-auto text-gray-400 mb-3" />
        <p className="text-sm font-medium text-gray-700">
          Arrastra una imagen aquí o{' '}
          <span className="text-blue-600 underline">selecciona un archivo</span>
        </p>
        <p className="text-xs text-gray-500 mt-1">
          {ALLOWED_EXTENSIONS} · Máximo {MAX_FILE_SIZE_MB}MB
        </p>
        <input
          ref={inputRef}
          type="file"
          accept={ALLOWED_TYPES.join(',')}
          className="hidden"
          onChange={handleInputChange}
        />
      </div>
      {displayError && (
        <p className="text-red-500 text-sm flex items-center gap-1">
          <AlertCircle className="w-4 h-4" />
          {displayError}
        </p>
      )}
    </div>
  );
}
