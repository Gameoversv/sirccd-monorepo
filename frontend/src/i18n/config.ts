import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import es from './locales/es.json';
import en from './locales/en.json';

const STORAGE_KEY = 'sirccd-lang';

if (!i18n.isInitialized) {
  const savedLng =
    typeof window !== 'undefined'
      ? (localStorage.getItem(STORAGE_KEY) ?? 'es')
      : 'es';

  i18n.use(initReactI18next).init({
    resources: {
      es: { translation: es },
      en: { translation: en },
    },
    lng: savedLng,
    fallbackLng: 'es',
    interpolation: { escapeValue: false },
  });
}

export const STORAGE_KEY_LANG = STORAGE_KEY;
export default i18n;
