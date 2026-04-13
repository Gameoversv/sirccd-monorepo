import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { ToastContainer } from '@/components';
import { I18nProvider } from '@/components/I18nProvider';
import './globals.css';

const inter = Inter({ subsets: ['latin'], variable: '--font-sans' });

export const metadata: Metadata = {
  title: 'SIRCCD — Sistema de Reporte de Calles Dañadas',
  description: 'Sistema Inteligente de Reporte Ciudadano de Calles Dañadas',
  icons: { icon: '/favicon.ico' },
};

const themeScript = `(() => { try {
  const t = localStorage.getItem('sirccd-theme');
  const d = t ? t === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches;
  if (d) document.documentElement.classList.add('dark');
} catch(_) {} })();`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className={`${inter.className} antialiased`}>
        <I18nProvider>
          {children}
          <ToastContainer />
        </I18nProvider>
      </body>
    </html>
  );
}
