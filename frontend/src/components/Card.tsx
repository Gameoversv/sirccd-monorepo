import { cn } from '@/utils';

interface CardProps {
  children: React.ReactNode;
  className?: string;
}

export function Card({ children, className }: CardProps) {
  return (
    <div className={cn('rounded-lg bg-white p-6 shadow', className)}>
      {children}
    </div>
  );
}

export function CardHeader({ children, className }: CardProps) {
  return (
    <div className={cn('mb-4', className)}>
      {children}
    </div>
  );
}

export function CardTitle({ children, className }: CardProps) {
  return (
    <h3 className={cn('text-lg font-semibold text-gray-900', className)}>
      {children}
    </h3>
  );
}

export function CardContent({ children, className }: CardProps) {
  return (
    <div className={cn('', className)}>
      {children}
    </div>
  );
}
