import { cn } from '../../utils/helpers';

const Card = ({ children, className, hover = false, ...props }) => {
  return (
    <div
      className={cn(
        'rounded-xl transition-colors duration-300',
        'bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800',
        hover && 'hover:border-gray-300 dark:hover:border-gray-700 hover:shadow-lg hover:shadow-purple-500/5 transition-all duration-200 cursor-pointer',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

const CardHeader = ({ children, className }) => {
  return (
    <div className={cn('px-6 py-4 border-b border-gray-200 dark:border-gray-800', className)}>
      {children}
    </div>
  );
};

const CardContent = ({ children, className }) => {
  return (
    <div className={cn('px-6 py-4', className)}>
      {children}
    </div>
  );
};

const CardFooter = ({ children, className }) => {
  return (
    <div className={cn('px-6 py-4 border-t border-gray-200 dark:border-gray-800', className)}>
      {children}
    </div>
  );
};

Card.Header = CardHeader;
Card.Content = CardContent;
Card.Footer = CardFooter;

export default Card;
