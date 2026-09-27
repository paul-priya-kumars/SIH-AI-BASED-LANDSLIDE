import React from 'react';
import { Clock, Eye, CheckCircle2, XCircle, CheckSquare } from 'lucide-react';
import { ReportStatus } from '../../types';

interface StatusBadgeProps {
  status: ReportStatus | string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const normStatus = (status || '').toUpperCase();

  let colorClasses = 'bg-slate-800 text-slate-300 border-slate-700';
  let Icon = Clock;
  let label = 'PENDING';

  switch (normStatus) {
    case 'UNDER_REVIEW':
      colorClasses = 'bg-blue-500/15 text-blue-400 border-blue-500/30';
      Icon = Eye;
      label = 'UNDER REVIEW';
      break;
    case 'VERIFIED':
      colorClasses = 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
      Icon = CheckCircle2;
      label = 'VERIFIED';
      break;
    case 'REJECTED':
      colorClasses = 'bg-red-500/15 text-red-400 border-red-500/30';
      Icon = XCircle;
      label = 'REJECTED';
      break;
    case 'RESOLVED':
      colorClasses = 'bg-teal-500/15 text-teal-400 border-teal-500/30';
      Icon = CheckSquare;
      label = 'RESOLVED';
      break;
    case 'PENDING':
    default:
      colorClasses = 'bg-amber-500/15 text-amber-400 border-amber-500/30';
      Icon = Clock;
      label = 'PENDING';
      break;
  }

  const sizeClasses = size === 'sm' ? 'text-[10px] px-2 py-0.5 gap-1' : 'text-xs px-2.5 py-1 gap-1.5 font-semibold';

  return (
    <span
      className={`inline-flex items-center rounded-full border shadow-xs tracking-wider uppercase ${colorClasses} ${sizeClasses}`}
    >
      <Icon className={size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5'} />
      <span>{label}</span>
    </span>
  );
};
