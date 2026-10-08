import React from 'react';
import { MapPin, Navigation, AlertCircle, RefreshCw } from 'lucide-react';
import { UserLocation } from '../../types';
import { PRESET_LOCATIONS } from '../../data/mockData';

interface LocationCardProps {
  location: UserLocation;
  loading: boolean;
  error: string | null;
  permissionDenied: boolean;
  onDetectGPS: () => void;
  onSelectLocation: (loc: UserLocation) => void;
  isStale?: boolean;
  lastUpdated?: number | null;
}

export const LocationCard: React.FC<LocationCardProps> = ({
  location,
  loading,
  error,
  onDetectGPS,
  onSelectLocation,
  isStale = false,
  lastUpdated,
}) => {
  return (
    <div className={`p-5 rounded-3xl glass-card border-slate-800 shadow-xl ${isStale ? 'animate-pulse' : ''}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-orange-500/10 border border-orange-500/20 flex items-center justify-center text-orange-400">
            <MapPin className="w-4 h-4" />
          </div>
          <div>
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block">
              Geographic Focal Point
            </span>
            <h3 className="text-base font-bold text-white flex items-center gap-1.5">
              <span>{location.name || 'Monitoring Station'}</span>
              {location.accuracy && (
                <span className="text-[10px] font-normal text-emerald-400 font-mono">
                  (GPS ±{Math.round(location.accuracy)}m)
                </span>
              )}
            </h3>
          </div>
        </div>

        <button
          onClick={onDetectGPS}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-orange-500 hover:bg-orange-600 disabled:opacity-50 text-white text-xs font-semibold rounded-xl shadow-sm transition"
          title="Detect Current GPS Location"
        >
          <Navigation className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>{loading ? 'Locating...' : 'Detect My GPS'}</span>
        </button>
      </div>

      {/* Lat/Long display */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800 font-mono text-xs">
          <span className="text-slate-500 block text-[10px] uppercase font-sans">Latitude</span>
          <span className="text-slate-200 font-bold">{location.latitude.toFixed(4)}° N</span>
        </div>
        <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800 font-mono text-xs">
          <span className="text-slate-500 block text-[10px] uppercase font-sans">Longitude</span>
          <span className="text-slate-200 font-bold">{location.longitude.toFixed(4)}° E</span>
        </div>
      </div>

      {/* Permission alert / notice if applicable */}
      {error && (
        <div className="mb-4 p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-start gap-2 text-xs text-amber-300">
          <AlertCircle className="w-4 h-4 shrink-0 text-amber-400 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Preset Location Switcher */}
      <div>
        <label className="text-[11px] font-semibold text-slate-400 block mb-2">
          Switch Monitoring Region:
        </label>
        <div className="flex flex-wrap gap-1.5">
          {PRESET_LOCATIONS.map((preset) => {
            const isActive =
              Math.abs(preset.latitude - location.latitude) < 0.005 &&
              Math.abs(preset.longitude - location.longitude) < 0.005;
            const displayName = (preset.name || 'Station').split(' ')[0];
            return (
              <button
                key={preset.name}
                onClick={() => onSelectLocation(preset)}
                className={`text-xs px-2.5 py-1 rounded-lg border transition ${
                  isActive
                    ? 'bg-orange-500/20 text-orange-300 border-orange-500/40 font-semibold'
                    : 'bg-slate-900/50 text-slate-400 border-slate-800 hover:text-slate-200 hover:border-slate-700'
                }`}
              >
                {displayName}
              </button>
            );
          })}
        </div>
      </div>

      {/* Timestamp */}
      <div className="mt-4 pt-3 border-t border-slate-800/20 flex justify-between text-xs">
        <span>
          <MapPin className="w-3 h-3 mr-1" />
          Location updated: {lastUpdated ? new Date(lastUpdated).toLocaleTimeString() : 'Live'}
        </span>
        <span>
          {lastUpdated && !isStale && (
            <span className="ml-2 text-xs font-semibold text-green-400">
              <RefreshCw className="w-3 h-3" /> Fresh
            </span>
          )}
          {lastUpdated && isStale && (
            <span className="ml-2 text-xs font-semibold text-orange-400">
              <RefreshCw className="w-3 h-3" /> Stale
            </span>
          )}
        </span>
      </div>
    </div>
  );
};