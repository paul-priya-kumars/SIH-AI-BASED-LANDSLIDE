import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { RiskZone } from '../types';
import { useGeolocation } from '../hooks/useGeolocation';
import { MapView } from '../components/map/MapView';
import { ZoneDetailModal } from '../components/map/ZoneDetailModal';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import { Layers, MapPin, Filter, Database, ShieldAlert, Sparkles } from 'lucide-react';

export const RiskMapPage: React.FC = () => {
  const { location, detectLocation } = useGeolocation();
  const [zones, setZones] = useState<RiskZone[]>([]);
  const [selectedZone, setSelectedZone] = useState<RiskZone | null>(null);
  const [selectedFilter, setSelectedFilter] = useState<string>('ALL');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadZones = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getRiskZones();
      setZones(data);
    } catch (err) {
      setError('Unable to load GIS hazard zones.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadZones();
  }, []);

  const filteredZones = zones.filter((zone) => {
    if (selectedFilter === 'ALL') return true;
    return zone.risk_level === selectedFilter;
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs uppercase tracking-widest font-bold text-orange-400">
              Interactive GIS Spatial Layer
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-blue-400 border border-slate-700">
              M2 CONTRACT INTERFACE
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-white font-heading">
            Landslide Susceptibility & Hazard Map
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Visualizing regional slope saturation, high-risk gorges, and active hazard buffer perimeters.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={detectLocation}
            className="inline-flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition"
          >
            <MapPin className="w-3.5 h-3.5 text-orange-400" />
            Center My Location
          </button>
        </div>
      </div>

      {/* Filter Chips Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-2xl glass-card border-slate-800">
        <div className="flex items-center gap-1.5 text-xs text-slate-400 font-semibold">
          <Filter className="w-3.5 h-3.5 text-slate-500" />
          <span>Filter Threat Levels:</span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {['ALL', 'VERY_HIGH', 'HIGH', 'MODERATE', 'LOW'].map((lvl) => (
            <button
              key={lvl}
              onClick={() => setSelectedFilter(lvl)}
              className={`text-xs px-3 py-1 rounded-xl font-semibold border transition ${
                selectedFilter === lvl
                  ? 'bg-orange-500/20 text-orange-300 border-orange-500/40'
                  : 'bg-slate-900/60 text-slate-400 border-slate-800 hover:text-slate-200'
              }`}
            >
              {lvl.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Main Leaflet Map View */}
      {loading ? (
        <LoadingState message="Rendering OpenStreetMap layers & GIS hazard polygons..." className="min-h-[500px]" />
      ) : error ? (
        <ErrorState message={error} onRetry={loadZones} />
      ) : (
        <div className="space-y-4">
          <MapView
            center={[location.latitude, location.longitude]}
            zoom={12}
            zones={filteredZones}
            userLocation={location}
            onSelectZone={(zone) => setSelectedZone(zone)}
            className="h-[550px] w-full"
          />

          {/* Quick Zone Catalog Bar */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-orange-400" />
              Identified Landslide Hazard Sectors ({filteredZones.length})
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {filteredZones.map((z) => (
                <div
                  key={z.zone_id}
                  onClick={() => setSelectedZone(z)}
                  className="p-3.5 rounded-2xl glass-card glass-card-hover border-slate-800 cursor-pointer flex items-center justify-between"
                >
                  <div>
                    <span className="text-xs font-bold text-slate-200 block truncate">
                      {z.name}
                    </span>
                    <span className="text-[11px] text-slate-400 font-mono">
                      Rain: {z.rainfall_mm}mm • Slope: {z.slope_deg}°
                    </span>
                  </div>
                  <span
                    className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full border ${
                      z.risk_level === 'VERY_HIGH'
                        ? 'bg-red-500/20 text-red-400 border-red-500/30'
                        : z.risk_level === 'HIGH'
                        ? 'bg-orange-500/20 text-orange-400 border-orange-500/30'
                        : z.risk_level === 'MODERATE'
                        ? 'bg-amber-500/20 text-amber-400 border-amber-500/30'
                        : 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                    }`}
                  >
                    {Math.round(z.risk_probability * 100)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Zone Detail Modal */}
      <ZoneDetailModal
        zone={selectedZone}
        onClose={() => setSelectedZone(null)}
      />
    </div>
  );
};
