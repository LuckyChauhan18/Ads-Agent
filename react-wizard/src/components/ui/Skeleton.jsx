import { cn } from '../../utils/helpers';

const Skeleton = ({ className, variant = 'rectangular' }) => {
  const variants = {
    rectangular: 'rounded-lg',
    circular: 'rounded-full',
    text: 'rounded h-4',
  };

  return (
    <div
      className={cn(
        'bg-gray-800 animate-pulse',
        variants[variant],
        className
      )}
    />
  );
};

const SkeletonCard = () => {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
      <div className="flex items-center justify-between">
        <Skeleton className="h-6 w-1/3" />
        <Skeleton className="h-6 w-20" />
      </div>
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-2/3" />
      <div className="flex gap-2">
        <Skeleton className="h-8 w-24" />
        <Skeleton className="h-8 w-24" />
      </div>
    </div>
  );
};

Skeleton.Card = SkeletonCard;

export default Skeleton;
