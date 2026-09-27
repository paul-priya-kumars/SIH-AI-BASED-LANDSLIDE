import React from 'react';
import { CloudRain, Mountain, Compass, Trees, Droplets, Thermometer, Database, RefreshCw, Clock } from 'lucide-react';
import { EnvironmentData } from '../../types';

interface EnvironmentalCardProps {
  environment: EnvironmentData;
  isStale?: boolean;
  lastUpdated?: number | null;
}

export const EnvironmentalCard: React.FC<EnvironmentalCardProps> = ({ environment, isStale = false, lastUpdated }) => {
  const metrics = [
    {
      label: 'Cumulative Rainfall (24h)',
      value: `${environment.rainfall} mm`,
      indicator: environment.rainfall > 120 ? 'Critical Downpour' : environment.rainfall > 70 ? 'Heavy' : 'Normal',
      indicatorColor: environment.rainfall > 120 ? 'text-red-400 bg-red-500/10' : environment.rainfall > 70 ? 'text-amber-400 bg-amber-500/10' : 'text-emerald-400 bg-emerald-500/10',
      icon: CloudRain,
      accent: 'text-blue-400',
    },
    {
      label: 'Terrain Slope Angle',
      value: `${environment.slope}°`,
      indicator: environment.slope > 35 ? 'Unstable Incline' : environment.slope > 25 ? 'Moderate Slope' : 'Gentle',
      indicatorColor: environment.slope > 35 ? 'text-red-400 bg-red-500/10' : environment.slope > 25 ? 'text-amber-400 bg-amber-500/10' : 'text-emerald-400 bg-emerald-500/10',
      icon: Mountain,
      accent: 'text-amber-400',
    },
    {
      label: 'Elevation',
      value: `${environment.elevation} m`,
      indicator: 'Highland Ridge',
      indicatorColor: 'text-indigo-400 bg-indigo-500/10',
      icon: Compass,
      accent: 'text-indigo-400',
    },
    {
      label: 'Vegetation Index (NDVI)',
      value: environment.ndvi.toFixed(2),
      indicator: environment.ndvi < 0.4 ? 'Sparse / Disturbed' : 'Dense Forest Canopy',
      indicatorColor: environment.ndvi < 0.4 ? 'text-orange-400 bg-orange-500/10' : 'text-emerald-400 bg-emerald-500/10',
      icon: Trees,
      accent: 'text-emerald-400',
    },
    {
      label: 'Soil Water Saturation',
      value: `${environment.soil_saturation_pct ?? 82}%`,
      indicator: (environment.soil_saturation_pct ?? 82) > 80 ? 'Liquefaction Risk' : 'Normal Moisture',
      indicatorColor: (environment.soil_saturation_pct ?? 82) > 80 ? 'text-red-400 bg-red-500/10' : 'text-emerald-400 bg-emerald-500/10',
      icon: Droplets,
      accent: 'text-cyan-400',
    },
    {
      label: 'Ambient Temperature',
      value: `${environment.temperature}°C`,
      indicator: `${environment.humidity}% Humidity`,
      indicatorColor: 'text-slate-300 bg-slate-800',
      icon: Thermometer,
      accent: 'text-rose-400',
    },
  ];

  return (
    <div className={`p-6 rounded-3xl glass-card border-slate-800 shadow-xl ${isStale ? 'animate-pulse' : ''}`}>
      <div className="flex items-center justify-between mb-5">
        <div>
          <span className="text-xs uppercase tracking-widest font-semibold text-slate-400 block mb-0.5">
            Hydrometeorological & Topographic Sensors
          </span>
          <h3 className="text-lg font-bold text-white">Environmental Indicators</h3>
        </div>
        {environment.is_mock && (
          <span className="inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded-md bg-slate-800 text-slate-400 border border-slate-700">
            <Database className="w-2.5 h-2.5 text-blue-400" />
            M2 GIS MOCK
          </span>
        )}
        {isStale && (
          <span className="text-xs text-orange-400 bg-orange-500/20 px-2 py-0.5 rounded">
            <RefreshCw className="w-3 h-3" /> Stale Data
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3.5">
        {metrics.map((item, i) => {
          const IconComponent = item.icon;
          return (
            <div
              key={i}
              className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 transition group"
            >
              <div className="flex items-center justify-between mb-2">
                <IconComponent className={`w-5 h-5 ${item.accent} transition-transform group-hover:scale-110`} />
                <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${item.indicatorColor}`}>
                  {item.indicator}
                </span>
              </div>
              <div className="text-xl sm:text-2xl font-black text-white font-mono tracking-tight mb-1">
                {item.value}
              </div>
              <div className="text-xs text-slate-400 leading-tight">
                {item.label}
              </div>
            </div>
          );
        })}
      </div>

      {/* Timestamp */}
      <div className="mt-4 pt-3 border-t border-slate-800/20 text-xs flex justify-between text-slate-500">
        <span>
          <Clock className="w-3 h-3 mr-1" />
          Last updated: {lastUpdated ? new Date(lastUpdated).toLocaleTimeString() : 'Live'}
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