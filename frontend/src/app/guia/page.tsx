'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, ShieldCheck, Users2, UserRound } from 'lucide-react';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';
import { ThemeToggle } from '@/components/ThemeToggle';
import { cn } from '@/utils';

type Tab = 'citizen' | 'staff';

function StepList({ tab }: { tab: Tab }) {
  const { t } = useTranslation();
  const steps = Object.keys(
    t(`guide.${tab}.steps`, { returnObjects: true }) as Record<string, unknown>
  );

  return (
    <ol className="space-y-4">
      {steps.map((key) => (
        <li key={key} className="flex gap-4">
          <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gradient-brand text-white text-sm font-semibold shadow-sm">
            {key}
          </div>
          <div>
            <p className="font-semibold text-foreground text-sm">
              {t(`guide.${tab}.steps.${key}.title`)}
            </p>
            <p className="text-sm text-muted-foreground mt-0.5">
              {t(`guide.${tab}.steps.${key}.body`)}
            </p>
          </div>
        </li>
      ))}
    </ol>
  );
}

export default function GuidePage() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<Tab>('citizen');

  return (
    <div className="min-h-screen bg-background bg-gradient-mesh">
      <header className="sticky top-0 z-30 border-b border-border bg-background/80 backdrop-blur-sm">
        <div className="max-w-3xl mx-auto flex h-14 items-center gap-3 px-4 sm:px-6">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            {t('guide.back')}
          </Link>
          <div className="ml-auto flex items-center gap-2">
            <LanguageSwitcher />
            <ThemeToggle />
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-8 sm:px-6 animate-fade-in space-y-8">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-brand text-white shadow-elevated">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-foreground">{t('guide.title')}</h1>
            <p className="text-sm text-muted-foreground">{t('guide.subtitle')}</p>
          </div>
        </div>

        <div className="inline-flex rounded-xl border border-border bg-card/60 p-1 gap-1">
          {(
            [
              { id: 'citizen' as const, label: t('guide.tabs.citizen'), icon: UserRound },
              { id: 'staff' as const, label: t('guide.tabs.staff'), icon: Users2 },
            ]
          ).map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={cn(
                'inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors',
                tab === id
                  ? 'bg-primary-600/10 text-primary-700 dark:text-primary-300'
                  : 'text-muted-foreground hover:text-foreground'
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </div>

        <section className="bg-card border border-border rounded-2xl p-5 sm:p-6 shadow-soft space-y-5">
          <p className="text-sm text-muted-foreground">{t(`guide.${tab}.intro`)}</p>
          <StepList tab={tab} />
        </section>

        <section className="bg-card border border-border rounded-2xl p-5 sm:p-6 shadow-soft">
          <h2 className="text-lg font-semibold text-foreground mb-3">{t('guide.faq.title')}</h2>
          <div className="divide-y divide-border">
            {(['q1', 'q2', 'q3'] as const).map((q) => (
              <details key={q} className="group py-3 first:pt-0 last:pb-0">
                <summary className="flex cursor-pointer items-center justify-between text-sm font-medium text-foreground list-none">
                  {t(`guide.faq.${q}`)}
                  <span className="ml-2 text-muted-foreground group-open:rotate-180 transition-transform">
                    ⌄
                  </span>
                </summary>
                <p className="mt-2 text-sm text-muted-foreground">
                  {t(`guide.faq.${q.replace('q', 'a')}`)}
                </p>
              </details>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
