import { cn } from '../../utils/helpers';
import { STATUS_COLORS, STATUS_LABELS } from '../../utils/constants';

const Badge = ({ status, size = 'md', className }) => {
  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-xs',
    lg: 'px-3 py-1.5 text-sm',
  };

  const bgColor = STATUS_COLORS[status] || 'bg-gray-500';
  const label = STATUS_LABELS[status] || status;

  return (
    <span
      className={cn(
        'inline-flex items-center font-medium rounded-full',
        bgColor,
        sizes[size],
        'text-white',
        className
      )}
    >
      {['APPROVED', 'SCRIPTING', 'GENERATING_IMAGES', 'COMPOSING_VIDEO', 'GENERATING_VIDEO'].includes(status) && (
        <span className="w-1.5 h-1.5 mr-1.5 bg-white rounded-full animate-pulse" />
      )}
      {label}
    </span>
  );
};

export default Badge;
