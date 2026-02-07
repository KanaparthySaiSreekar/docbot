import type { HTMLAttributes } from 'react';
import { cn } from '@/lib/cn';

type Variant = 'glass' | 'solid' | 'outline';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: Variant;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hover?: boolean;
}

const variantStyles: Record<Variant, string> = {
  glass: 'glass-card',
  solid: 'bg-white border border-clinical-100 shadow-card rounded-2xl',
  outline: 'bg-transparent border border-clinical-200 rounded-2xl',
};

const paddingStyles = {
  none: '',
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
};

export function Card({ className, variant = 'glass', padding = 'md', hover = true, children, ...props }: CardProps) {
  return (
    <div
      className={cn(
        variantStyles[variant],
        paddingStyles[padding],
        hover && 'hover:shadow-card-hover hover:border-primary-200/40 transition-all duration-300',
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}
