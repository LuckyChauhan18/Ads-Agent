import { cn } from '../../utils/helpers';

const EmptyState = ({
  icon: Icon,
  title,
  description,
  action,
  className,
}) => {
  return (
    <div className={cn('flex flex-col items-center justify-center py-12 px-4 text-center', className)}>
      {Icon && (
        <div className="w-16 h-16 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mb-4">
          <Icon className="w-8 h-8 text-gray-400 dark:text-gray-500" />
        </div>
      )}
      {title && (
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">{title}</h3>
      )}
      {description && (
        <p className="text-gray-500 dark:text-gray-400 max-w-md mb-6">{description}</p>
      )}
      {action && action}
    </div>
  );
};

export default EmptyState;
