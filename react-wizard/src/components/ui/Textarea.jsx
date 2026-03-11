import { forwardRef } from 'react';
import { cn } from '../../utils/helpers';

const Textarea = forwardRef(({
  label,
  error,
  className,
  containerClassName,
  rows = 4,
  ...props
}, ref) => {
  return (
    <div className={cn('space-y-1.5', containerClassName)}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          {label}
        </label>
      )}
      <textarea
        ref={ref}
        rows={rows}
        className={cn(
          'w-full bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg px-4 py-2.5',
          'text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 resize-none',
          'focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500',
          'transition-colors duration-200',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          error && 'border-red-500 focus:border-red-500 focus:ring-red-500',
          className
        )}
        {...props}
      />
      {error && (
        <p className="text-sm text-red-500 dark:text-red-400">{error}</p>
      )}
    </div>
  );
});

Textarea.displayName = 'Textarea';

export default Textarea;
