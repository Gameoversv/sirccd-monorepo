'use client';

import { useEffect, useState } from 'react';
import { Moon, Sun } from 'lucide-react';

const KEY = 'sirccd-theme';

export function ThemeToggle({ className }: { className?: string }) {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  useEffect(() => {
    const stored = (localStorage.getItem(KEY) as 'light' | 'dark' | null);
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const initial = stored ?? (prefersDark ? 'dark' : 'light');
    setTheme(initial);
    document.documentElement.classList.toggle('dark', initial === 'dark');
  }, []);

  const toggle = () => {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    localStorage.setItem(KEY, next);
    document.documentElement.classList.toggle('dark', next === 'dark');
  };

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={theme === 'dark' ? 'Activar modo claro' : 'Activar modo oscuro'}
      title={theme === 'dark' ? 'Modo claro' : 'Modo oscuro'}
      className={
        className ??
        'inline-flex items-center justify-center w-9 h-9 rounded-lg border border-border bg-card hover:bg-muted text-foreground transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-ring'
      }
    >
      {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
    </button>
  );
}
