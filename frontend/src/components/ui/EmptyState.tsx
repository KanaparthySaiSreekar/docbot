import { cn } from '@/lib/cn';
import type { LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({ icon: Icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-16 text-center', className)}>
      <div className="w-16 h-16 rounded-2xl bg-clinical-100 flex items-center justify-center mb-4">
        <Icon className="w-8 h-8 text-clinical-400" />
      </div>
      <h3 className="text-lg font-semibold text-clinical-700 mb-1">{title}</h3>
      {description && (
        <p className="text-sm text-clinical-500 max-w-sm">{description}</p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
