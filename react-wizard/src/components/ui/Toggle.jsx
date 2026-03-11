import { cn } from '../../utils/helpers';

const Toggle = ({ label, description, checked, onChange, disabled, className }) => {
  return (
    <label className={cn('flex items-center justify-between cursor-pointer', disabled && 'cursor-not-allowed opacity-50', className)}>
      <div className="space-y-0.5">
        {label && <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{label}</span>}
        {description && <p className="text-xs text-gray-500">{description}</p>}
      </div>
      <div className="relative">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onChange?.(e.target.checked)}
          disabled={disabled}
          className="sr-only peer"
        />
        <div className={cn(
          'w-11 h-6 bg-gray-300 dark:bg-gray-700 rounded-full transition-colors duration-200',
          'peer-checked:bg-linear-to-r peer-checked:from-purple-600 peer-checked:to-pink-600',
          'peer-focus:ring-2 peer-focus:ring-purple-500 peer-focus:ring-offset-2 peer-focus:ring-offset-white dark:peer-focus:ring-offset-gray-900'
        )} />
        <div className={cn(
          'absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full transition-transform duration-200',
          'peer-checked:translate-x-5'
        )} />
      </div>
    </label>
  );
};

export default Toggle;
