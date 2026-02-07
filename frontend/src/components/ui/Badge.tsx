import { cn } from '@/lib/cn';

type BadgeVariant = 'confirmed' | 'pending' | 'cancelled' | 'refunded' | 'info' | 'default';

interface BadgeProps {
  variant?: BadgeVariant;
  children: React.ReactNode;
  className?: string;
}

const variantStyles: Record<BadgeVariant, string> = {
  confirmed: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  pending: 'bg-amber-50 text-amber-700 border-amber-200',
  cancelled: 'bg-red-50 text-red-700 border-red-200',
  refunded: 'bg-clinical-100 text-clinical-600 border-clinical-200',
  info: 'bg-accent-50 text-accent-700 border-accent-200',
  default: 'bg-clinical-50 text-clinical-600 border-clinical-200',
};

export function Badge({ variant = 'default', className, children }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border',
        variantStyles[variant],
        className,
      )}
    >
      {children}
    </span>
  );
}

const statusMap: Record<string, BadgeVariant> = {
  CONFIRMED: 'confirmed',
  PENDING_PAYMENT: 'pending',
  CANCELLED: 'cancelled',
  REFUNDED: 'refunded',
};

export function StatusBadge({ status }: { status: string }) {
  const variant = statusMap[status] || 'default';
  const label = status.replace(/_/g, ' ');
  return <Badge variant={variant}>{label}</Badge>;
}
