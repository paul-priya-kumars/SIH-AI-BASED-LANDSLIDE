import React from 'react';
import { ShieldCheck, AlertTriangle, AlertOctagon, Flame } from 'lucide-react';
import { RiskLevel } from '../../types';

interface RiskBadgeProps {
  level: RiskLevel | string;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({
  level,
  size = 'md',
  showIcon = true,
}) => {
  const normLevel = (level || '').toUpperCase();

  let colorClasses = 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
  let label = 'LOW RISK';
  let Icon = ShieldCheck;

  if (normLevel === 'VERY_HIGH' || normLevel === 'CRITICAL') {
    colorClasses = 'bg-red-500/20 text-red-400 border-red-500/40 ring-1 ring-red-500/30 animate-pulse';
    label = normLevel === 'CRITICAL' ? 'CRITICAL RISK' : 'VERY HIGH RISK';
    Icon = Flame;
  } else if (normLevel === 'HIGH') {
    colorClasses = 'bg-orange-500/20 text-orange-400 border-orange-500/40';
    label = 'HIGH RISK';
    Icon = AlertOctagon;
  } else if (normLevel === 'MODERATE' || normLevel === 'MEDIUM') {
    colorClasses = 'bg-amber-500/20 text-amber-400 border-amber-500/30';
    label = 'MODERATE RISK';
    Icon = AlertTriangle;
  }

  const sizeClasses = {
    sm: 'text-[11px] px-2 py-0.5 gap-1.5 font-semibold',
    md: 'text-xs px-2.5 py-1 gap-1.5 font-bold',
    lg: 'text-sm px-3.5 py-1.5 gap-2 font-extrabold tracking-wide',
  }[size];

  const iconSizes = {
    sm: 'w-3 h-3',
    md: 'w-3.5 h-3.5',
    lg: 'w-4 h-4',
  }[size];

  return (
    <span
      className={`inline-flex items-center rounded-full border shadow-sm uppercase tracking-wider ${colorClasses} ${sizeClasses}`}
      role="status"
      aria-label={`Risk Level: ${label}`}
    >
      {showIcon && <Icon className={iconSizes} aria-hidden="true" />}
      <span>{label}</span>
    </span>
  );
};
