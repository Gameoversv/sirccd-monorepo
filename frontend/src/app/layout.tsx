import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { ToastContainer } from '@/components';
import { I18nProvider } from '@/components/I18nProvider';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'SIRCCD - Sistema de Reporte de Calles Dañadas',
  description: 'Sistema Inteligente de Reporte Ciudadano de Calles Dañadas',
  icons: {
    icon: '/favicon.ico',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body className={inter.className}>
        <I18nProvider>
          {children}
          <ToastContainer />
        </I18nProvider>
      </body>
    </html>
  );
}
