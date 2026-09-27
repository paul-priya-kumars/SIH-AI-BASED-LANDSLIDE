import React from 'react';
import { AlertTriangle, Clock, MapPin, ChevronRight, ShieldAlert, RefreshCw } from 'lucide-react';
import { Alert } from '../../types';
import { Link } from 'react-router-dom';

interface AlertCardProps {
  alert: Alert;
  isStale?: boolean;
  lastUpdated?: number | null;
}

export const AlertCard: React.FC<AlertCardProps> = ({ alert, isStale = false, lastUpdated }) => {
  const isCritical = alert.severity === 'CRITICAL';
  const isHigh = alert.severity === 'HIGH';

  const badgeColor = isCritical
    ? 'bg-red-500/20 text-red-400 border-red-500/30'
    : isHigh
    ? 'bg-orange-500/20 text-orange-400 border-orange-500/30'
    : 'bg-amber-500/20 text-amber-400 border-amber-500/30';

  const cardBorder = isCritical
    ? 'border-red-500/30 bg-red-950/10'
    : isHigh
    ? 'border-orange-500/20 bg-orange-950/5'
    : 'border-slate-800 bg-slate-900/40';

  const timeAgo = new Date(alert.issued_at).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className={`p-4 rounded-2xl border ${cardBorder} transition hover:border-slate-700 ${isStale ? 'animate-pulse' : ''}`}>
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center gap-2">
          <span className={`text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full border ${badgeColor}`}>
            {alert.severity} ADVISORY
          </span>
          <span className="text-[11px] text-slate-500 flex items-center gap-1">
            <Clock className="w-3 h-3" />
            Issued {timeAgo}
          </span>
        </div>

        <span className="text-[11px] text-slate-500 font-mono">
          #{alert.alert_id}
        </span>
      </div>

      <h4 className="text-sm font-bold text-white mb-1.5 leading-snug">
        {alert.title}
      </h4>

      <p className="text-xs text-slate-400 mb-3 leading-relaxed">
        {alert.message}
      </p>

      <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800/80 mb-3">
        <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1 flex items-center gap-1">
          <ShieldAlert className="w-3 h-3 text-orange-400" />
          Recommended Safety Action:
        </div>
        <div className="text-xs font-medium text-slate-200">
          {alert.recommended_action}
        </div>
      </div>

      <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
        <div className="flex items-center gap-1 text-[11px] text-slate-400">
          <MapPin className="w-3 h-3 text-orange-400" />
          <span>{alert.location}</span>
        </div>
        <Link
          to="/alerts"
          className="text-orange-400 hover:text-orange-300 font-semibold text-xs flex items-center gap-0.5 transition"
        >
          View Advisory <ChevronRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* Timestamp and stale indicator */}
      {lastUpdated && (
        <div className="mt-2 pt-1 border-t border-slate-800/20 flex justify-between text-xs">
          <span>
            <Clock className="w-3 h-3 mr-1" />
            Last updated: {new Date(lastUpdated).toLocaleTimeString()}
          </span>
          <span>
            {!isStale && (
              <span className="ml-2 text-xs font-semibold text-green-400">
                <RefreshCw className="w-3 h-3" /> Fresh
              </span>
            )}
            {isStale && (
              <span className="ml-2 text-xs font-semibold text-orange-400">
                <RefreshCw className="w-3 h-3" /> Stale
              </span>
            )}
          </span>
        </div>
      )}
    </div>
  );
};