import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  label?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  className,
  label,
}) => {
  const sizeMap = {
    sm: 'h-4 w-4 border-2',
    md: 'h-6 w-6 border-2',
    lg: 'h-8 w-8 border-3',
    xl: 'h-12 w-12 border-4',
  };

  return (
    <div className="flex flex-col items-center justify-center gap-3 p-4">
      <div
        className={twMerge(
          clsx(
            'animate-spin rounded-full border-brand-500 border-t-transparent dark:border-brand-400 dark:border-t-transparent',
            sizeMap[size],
            className
          )
        )}
        role="status"
        aria-label="Loading"
      />
      {label && <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">{label}</p>}
    </div>
  );
};
