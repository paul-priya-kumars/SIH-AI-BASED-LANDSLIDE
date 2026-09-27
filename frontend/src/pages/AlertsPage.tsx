import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Alert } from '../types';
import { AlertCard } from '../components/dashboard/AlertCard';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import { EmptyState } from '../components/common/EmptyState';
import { Bell, ShieldAlert, Filter, Radio, Volume2, Info } from 'lucide-react';

export const AlertsPage: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSeverity, setSelectedSeverity] = useState<string>('ALL');

  const loadAlerts = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getAlerts(selectedSeverity !== 'ALL' ? selectedSeverity : undefined);
      setAlerts(data);
    } catch (err) {
      setError('Unable to load disaster warning bulletins.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, [selectedSeverity]);

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs uppercase tracking-widest font-bold text-orange-400">
            Official Civil Defense Advisories
          </span>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-red-500/20 text-red-400 border border-red-500/30 flex items-center gap-1">
            <Radio className="w-2.5 h-2.5 animate-pulse" />
            LIVE WARNING BROADCAST
          </span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-black text-white font-heading">
          Landslide Advisories & Emergency Alerts
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 mt-1">
          Immediate alerts issued when rainfall thresholds, slope inclinometers, or saturation levels exceed critical safety margins.
        </p>
      </div>

      {/* Recommended General Guidelines */}
      <div className="p-4 rounded-3xl glass-card border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs text-slate-300">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-orange-500/10 border border-orange-500/20 flex items-center justify-center text-orange-400 shrink-0">
            <Volume2 className="w-4 h-4" />
          </div>
          <div>
            <span className="font-bold text-white block">Community Emergency Protocol</span>
            <span className="text-slate-400 text-[11px]">
              Nilgiris District Emergency Operations Control: Dial 1077 (Toll Free) or Police 100
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-xl border border-emerald-500/20">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>Siren Broadcast Stations Synced</span>
        </div>
      </div>

      {/* Filter Chips Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-2xl glass-card border-slate-800">
        <div className="flex items-center gap-1.5 text-xs text-slate-400 font-semibold">
          <Filter className="w-3.5 h-3.5 text-slate-500" />
          <span>Filter by Severity:</span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {['ALL', 'CRITICAL', 'HIGH', 'MODERATE', 'LOW'].map((sev) => (
            <button
              key={sev}
              onClick={() => setSelectedSeverity(sev)}
              className={`text-xs px-3 py-1 rounded-xl font-semibold border transition ${
                selectedSeverity === sev
                  ? 'bg-orange-500/20 text-orange-300 border-orange-500/40'
                  : 'bg-slate-900/60 text-slate-400 border-slate-800 hover:text-slate-200'
              }`}
            >
              {sev}
            </button>
          ))}
        </div>
      </div>

      {/* Bulletins Grid */}
      {loading ? (
        <LoadingState message="Broadcasting active alert bulletins..." className="min-h-[40vh]" />
      ) : error ? (
        <ErrorState message={error} onRetry={loadAlerts} />
      ) : alerts.length === 0 ? (
        <EmptyState
          title="No Active Bulletins"
          description="There are currently no active warning alerts for this severity tier."
          actionLabel="Clear Filters"
          onAction={() => setSelectedSeverity('ALL')}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {alerts.map((alert) => (
            <AlertCard key={alert.id || alert.alert_id} alert={alert} />
          ))}
        </div>
      )}
    </div>
  );
};
