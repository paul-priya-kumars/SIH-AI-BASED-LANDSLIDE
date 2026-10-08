import React from 'react';
import { X, CloudRain, Mountain, Compass, Layers, ShieldAlert, AlertTriangle } from 'lucide-react';
import { RiskZone } from '../../types';
import { RiskBadge } from '../dashboard/RiskBadge';

interface ZoneDetailModalProps {
  zone: RiskZone | null;
  onClose: () => void;
}

export const ZoneDetailModal: React.FC<ZoneDetailModalProps> = ({ zone, onClose }) => {
  if (!zone) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="relative w-full max-w-lg p-6 rounded-3xl glass-card border-slate-700 shadow-2xl bg-slate-900/95">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-1.5 rounded-full bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700 transition"
          aria-label="Close modal"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Title */}
        <div className="mb-4 pr-8">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
              Zone Identifier: {zone.zone_id}
            </span>
          </div>
          <h3 className="text-xl font-bold text-white leading-tight">
            {zone.name}
          </h3>
        </div>

        {/* Risk Level & Probability */}
        <div className="flex items-center justify-between p-4 rounded-2xl bg-slate-800/60 border border-slate-700/60 mb-5">
          <div>
            <span className="text-xs text-slate-400 block mb-1">Assessed Threat Level</span>
            <RiskBadge level={zone.risk_level} size="lg" />
          </div>
          <div className="text-right">
            <span className="text-xs text-slate-400 block mb-0.5">Failure Probability</span>
            <span className="text-2xl font-black text-white font-mono">
              {Math.round(zone.risk_probability * 100)}%
            </span>
          </div>
        </div>

        {/* Environmental Parameters */}
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5 text-orange-400" />
          M2 Environmental & Terrain Indicators
        </h4>

        <div className="grid grid-cols-2 gap-3 mb-5">
          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
            <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-1">
              <CloudRain className="w-3.5 h-3.5 text-blue-400" />
              <span>Rainfall Accumulation</span>
            </div>
            <div className="text-base font-bold text-white font-mono">{zone.rainfall_mm} mm</div>
          </div>

          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
            <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-1">
              <Mountain className="w-3.5 h-3.5 text-amber-400" />
              <span>Slope Gradient</span>
            </div>
            <div className="text-base font-bold text-white font-mono">{zone.slope_deg}°</div>
          </div>

          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
            <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-1">
              <Compass className="w-3.5 h-3.5 text-indigo-400" />
              <span>Altitude</span>
            </div>
            <div className="text-base font-bold text-white font-mono">{zone.elevation_m} m</div>
          </div>

          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
            <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-1">
              <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
              <span>Buffer Radius</span>
            </div>
            <div className="text-base font-bold text-white font-mono">{zone.radius_meters} m</div>
          </div>
        </div>

        {zone.soil_type && (
          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 mb-6">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1">
              Geological Regolith & Soil Composition
            </span>
            <span className="text-xs text-slate-200 font-medium">{zone.soil_type}</span>
          </div>
        )}

        {/* Action button */}
        <button
          onClick={onClose}
          className="w-full py-2.5 px-4 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs rounded-xl transition"
        >
          Close Sector Details
        </button>
      </div>
    </div>
  );
};
