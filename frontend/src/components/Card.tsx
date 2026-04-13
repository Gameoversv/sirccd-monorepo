import { cn } from '@/utils';

interface CardProps {
  children: React.ReactNode;
  className?: string;
}

export function Card({ children, className }: CardProps) {
  return (
    <div
      className={cn(
        'rounded-xl border border-border bg-card text-card-foreground p-6 shadow-soft transition-shadow hover:shadow-elevated',
        className,
      )}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, className }: CardProps) {
  return <div className={cn('mb-4 flex flex-col gap-1', className)}>{children}</div>;
}

export function CardTitle({ children, className }: CardProps) {
  return (
    <h3 className={cn('text-base font-semibold tracking-tight text-foreground', className)}>
      {children}
    </h3>
  );
}

export function CardContent({ children, className }: CardProps) {
  return <div className={cn('text-sm text-muted-foreground', className)}>{children}</div>;
}
