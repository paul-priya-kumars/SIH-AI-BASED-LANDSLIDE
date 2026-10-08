import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingStateProps {
  message?: string;
  className?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Loading data...',
  className = '',
}) => {
  return (
    <div className={`flex flex-col items-center justify-center p-12 text-center text-slate-400 ${className}`}>
      <div className="relative mb-4">
        <div className="w-12 h-12 rounded-full border-2 border-orange-500/20 border-t-orange-500 animate-spin" />
        <Loader2 className="w-6 h-6 text-orange-400 absolute inset-0 m-auto animate-pulse" />
      </div>
      <p className="text-sm font-medium text-slate-300">{message}</p>
      <span className="text-xs text-slate-500 mt-1">Streaming geospatial telemetry</span>
    </div>
  );
};
