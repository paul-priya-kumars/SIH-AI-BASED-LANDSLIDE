import React from 'react';
import { ShieldAlert, Activity, CheckCircle2, Clock, Cpu, RefreshCw } from 'lucide-react';
import { RiskPrediction } from '../../types';

interface RiskCardProps {
  prediction: RiskPrediction;
  locationName: string;
  isStale?: boolean;
  lastUpdated?: number | null;
}

export const RiskCard: React.FC<RiskCardProps> = ({ prediction, locationName, isStale = false, lastUpdated }) => {
  const percentage = Math.round(prediction.risk_probability * 100);

  // Determine progress bar styling
  let progressColor = 'from-emerald-500 to-teal-400';
  let badgeBorder = 'border-emerald-500/20';

  if (prediction.risk_level === 'VERY_HIGH') {
    progressColor = 'from-red-600 via-rose-500 to-orange-500';
    badgeBorder = 'border-red-500/30';
  } else if (prediction.risk_level === 'HIGH') {
    progressColor = 'from-orange-500 to-amber-500';
    badgeBorder = 'border-orange-500/30';
  } else if (prediction.risk_level === 'MODERATE') {
    progressColor = 'from-amber-500 to-yellow-400';
    badgeBorder = 'border-amber-500/20';
  }

  const formattedTime = new Date(prediction.updated_at).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className={`p-6 rounded-3xl glass-card ${badgeBorder} relative overflow-hidden shadow-2xl ${isStale ? 'animate-pulse' : ''}`}>
      {/* Background radial glow */}
      <div className="absolute -right-16 -top-16 w-64 h-64 bg-orange-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header section */}
      <div className="flex flex-wrap items-start justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs uppercase tracking-widest font-semibold text-slate-400">
              Assessed Monitoring Sector
            </span>
            {prediction.is_mock && (
              <span className="inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded-md bg-slate-800 text-slate-400 border border-slate-700">
                <Cpu className="w-2.5 h-2.5 text-orange-400" />
                M1 MOCK CONTRACT
              </span>
            )}
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
            {locationName}
          </h2>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-2xl">
            Live terrain saturation monitoring, slope stability analytics, and citizen hazard reporting.
          </p>
        </div>

        <div className="flex flex-col items-end">
          <span className="text-[11px] font-medium text-slate-400 mb-1">CURRENT STATUS</span>
          <div className="flex items-center gap-2">
            <Badge level={prediction.risk_level} size="lg" />
            {isStale && (
              <span className="text-xs text-orange-400 bg-orange-500/20 px-2 py-0.5 rounded">
                <RefreshCw className="w-3 h-3" /> Stale
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Probability Gauge & Big Stat */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 mb-6">
        <div className="md:col-span-5 flex items-baseline gap-3">
          <div className="text-5xl sm:text-6xl font-black tracking-tight text-white font-mono">
            {percentage}%
          </div>
          <div className="flex flex-col">
            <span className="text-xs uppercase font-bold tracking-wider text-slate-400">
              Risk Probability
            </span>
            <span className="text-[11px] text-slate-500">
              Confidence: {Math.round(prediction.confidence * 100)}%
            </span>
          </div>
        </div>

        <div className="md:col-span-7">
          <div className="flex justify-between text-xs font-semibold text-slate-400 mb-2">
            <span>Susceptibility Gauge</span>
            <span className="text-slate-300">{prediction.risk_level.replace('_', ' ')}</span>
          </div>
          <div className="h-3.5 w-full bg-slate-800/90 rounded-full overflow-hidden p-0.5 border border-slate-700/50">
            <div
              className={`h-full rounded-full bg-gradient-to-r ${progressColor} transition-all duration-1000 ease-out`}
              style={{ width: `${Math.max(percentage, 5)}%` }}
            />
          </div>
          <div className="flex justify-between text-[10px] text-slate-500 font-mono mt-1.5 px-0.5">
            <span>0% Safe</span>
            <span>35% Moderate</span>
            <span>75% Critical</span>
            <span>100%</span>
          </div>
        </div>
      </div>

      {/* Contributing Factors */}
      <div>
        <h4 className="text-xs uppercase font-bold tracking-wider text-slate-400 mb-3 flex items-center gap-1.5">
          <Activity className="w-3.5 h-3.5 text-orange-400" />
          Primary Contributing Risk Factors
        </h4>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          {prediction.factors.map((factor, idx) => (
            <div
              key={idx}
              className="flex items-start gap-2.5 p-2.5 rounded-xl bg-slate-900/40 border border-slate-800/60 text-xs text-slate-300"
            >
              <CheckCircle2 className="w-3.5 h-3.5 text-orange-400 mt-0.5 shrink-0" />
              <span className="leading-snug">{factor}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Footer Timestamp */}
      <div className="mt-6 pt-4 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500">
        <div className="flex items-center gap-1.5">
          <Clock className="w-3.5 h-3.5" />
          <span>Last telemetry update: {formattedTime}</span>
          {lastUpdated && !isStale && (
            <span className="ml-3 text-xs font-semibold text-green-400">
              <RefreshCw className="w-3 h-3" /> Fresh
            </span>
          )}
          {lastUpdated && isStale && (
            <span className="ml-3 text-xs font-semibold text-orange-400">
              <RefreshCw className="w-3 h-3" /> Stale
            </span>
          )}
        </div>
        <div className="font-mono text-slate-500">
          GPS: {prediction.latitude.toFixed(4)}°N, {prediction.longitude.toFixed(4)}°E
        </div>
      </div>
    </div>
  );
};

// Helper component for risk badge
interface BadgeProps {
  level: RiskPrediction['risk_level'];
  size?: 'sm' | 'md' | 'lg';
}

const Badge: React.FC<BadgeProps> = ({ level, size = 'md' }) => {
  const sizeMap = {
    sm: 'text-[10px] px-2 py-0.5',
    md: 'text-xs px-2.5 py-0.5',
    lg: 'text-sm px-3 py-1',
  };

  const colorMap: Record<RiskPrediction['risk_level'], string> = {
    LOW: 'bg-emerald-500/20 text-emerald-400 border-emerald-500',
    MODERATE: 'bg-amber-500/20 text-amber-400 border-amber-500',
    HIGH: 'bg-orange-500/20 text-orange-400 border-orange-500',
    VERY_HIGH: 'bg-red-500/20 text-red-400 border-red-500',
    CRITICAL: 'bg-red-500/30 text-red-300 border-red-500/50 animate-pulse',
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full ${sizeMap[size]} ${colorMap[level]}`}>
      {level.replace('_', ' ')}
    </span>
  );
};