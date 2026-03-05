'use client';

import { useTranslation } from 'react-i18next';
import { STORAGE_KEY_LANG } from '@/i18n/config';

export function LanguageSwitcher({ className }: { className?: string }) {
  const { i18n } = useTranslation();
  const isEs = i18n.language === 'es';

  const toggle = () => {
    const next = isEs ? 'en' : 'es';
    i18n.changeLanguage(next);
    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY_LANG, next);
    }
  };

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={isEs ? 'Switch to English' : 'Cambiar a español'}
      title={isEs ? 'Switch to English' : 'Cambiar a español'}
      className={
        className ??
        'inline-flex items-center justify-center w-9 h-9 rounded-lg border border-gray-300 bg-white hover:bg-gray-50 text-xs font-semibold text-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500'
      }
    >
      {isEs ? 'EN' : 'ES'}
    </button>
  );
}
