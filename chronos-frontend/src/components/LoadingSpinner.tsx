export default function LoadingSpinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizeClasses = {
    sm: 'w-4 h-4 border-2',
    md: 'w-8 h-8 border-2',
    lg: 'w-12 h-12 border-3',
  };

  return (
    <div className="flex items-center justify-center p-8" role="status" aria-label="Loading">
      <div
        className={`${sizeClasses[size]} border-gray-700 border-t-ps-blue rounded-full animate-spin`}
      />
    </div>
  );
}
