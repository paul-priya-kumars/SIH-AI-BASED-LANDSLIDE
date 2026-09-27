import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { RouteRisk } from '../types';
import { MapView } from '../components/map/MapView';
import { RiskBadge } from '../components/dashboard/RiskBadge';
import { LoadingState } from '../components/common/LoadingState';
import {
  Route as RouteIcon,
  Navigation,
  Clock,
  Gauge,
  AlertTriangle,
  ShieldCheck,
  ArrowRight,
  Info,
  CheckCircle,
} from 'lucide-react';

export const RouteSafetyPage: React.FC = () => {
  const [startLocation, setStartLocation] = useState<string>('Coonoor Foothills');
  const [destination, setDestination] = useState<string>('Ooty Town Center');
  const [routeRisk, setRouteRisk] = useState<RouteRisk | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const predefinedCorridors = [
    { start: 'Coonoor Foothills', end: 'Ooty Town Center' },
    { start: 'Mettupalayam Gate', end: 'Kotagiri Ridge' },
    { start: 'Gudalur Valley', end: 'Naduvattam Pass' },
  ];

  const handleEvaluateRoute = async (start = startLocation, dest = destination) => {
    setLoading(true);
    try {
      const data = await api.getRouteRisk(start, dest);
      setRouteRisk(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleEvaluateRoute();
  }, []);

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div>
        <span className="text-xs uppercase tracking-widest font-bold text-orange-400 block mb-1">
          Transit Hazard Safety Analyzer
        </span>
        <h1 className="text-2xl sm:text-3xl font-black text-white font-heading">
          Mountain Transit Route Safety
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 mt-1">
          Evaluate alternative mountain passes to avoid active rockfall sectors and saturated slope cuts.
        </p>
      </div>

      {/* Safety Notice Banner */}
      <div className="p-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 flex items-start gap-2.5">
        <Info className="w-4 h-4 shrink-0 text-amber-400 mt-0.5" />
        <div>
          <span className="font-bold">Phase 1 Demonstration Simulation:</span> Transit evaluations use synthetic GIS corridor overlays and heuristic safety models. Always follow on-ground police and disaster authority roadblock advisories.
        </div>
      </div>

      {/* Route Inputs Form */}
      <div className="p-6 rounded-3xl glass-card border-slate-800 shadow-xl">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
          <div className="md:col-span-5">
            <label className="text-xs font-semibold text-slate-300 block mb-1.5">
              Start Origin Location:
            </label>
            <div className="relative">
              <input
                type="text"
                value={startLocation}
                onChange={(e) => setStartLocation(e.target.value)}
                placeholder="e.g. Coonoor Ghat"
                className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-sm text-white focus:outline-hidden focus:border-orange-500"
              />
              <Navigation className="w-4 h-4 text-slate-500 absolute right-3 top-3" />
            </div>
          </div>

          <div className="md:col-span-5">
            <label className="text-xs font-semibold text-slate-300 block mb-1.5">
              Destination Pass / Town:
            </label>
            <div className="relative">
              <input
                type="text"
                value={destination}
                onChange={(e) => setDestination(e.target.value)}
                placeholder="e.g. Ooty Town Center"
                className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-sm text-white focus:outline-hidden focus:border-orange-500"
              />
              <RouteIcon className="w-4 h-4 text-slate-500 absolute right-3 top-3" />
            </div>
          </div>

          <div className="md:col-span-2">
            <button
              onClick={() => handleEvaluateRoute()}
              disabled={loading}
              className="w-full py-2.5 px-4 bg-orange-600 hover:bg-orange-500 disabled:opacity-50 text-white font-bold text-xs rounded-xl shadow-md transition"
            >
              {loading ? 'Evaluating...' : 'Analyze Routes'}
            </button>
          </div>
        </div>

        {/* Quick Corridor Buttons */}
        <div className="mt-4 pt-4 border-t border-slate-800/80 flex flex-wrap items-center gap-2 text-xs">
          <span className="text-slate-500 text-[11px] font-medium">Quick Corridors:</span>
          {predefinedCorridors.map((c, i) => (
            <button
              key={i}
              onClick={() => {
                setStartLocation(c.start);
                setDestination(c.end);
                handleEvaluateRoute(c.start, c.end);
              }}
              className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700 transition text-[11px]"
            >
              {c.start} → {c.end}
            </button>
          ))}
        </div>
      </div>

      {loading && !routeRisk ? (
        <LoadingState message="Calculating corridor slope exposures..." />
      ) : routeRisk ? (
        <div className="space-y-6">
          {/* Comparison Cards: Route A vs Route B */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Route A - Recommended */}
            <div
              className={`p-6 rounded-3xl border ${
                routeRisk.recommended_route.is_recommended
                  ? 'border-emerald-500/40 bg-emerald-950/10 shadow-lg shadow-emerald-950/20'
                  : 'glass-card border-slate-800'
              } flex flex-col justify-between`}
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-3">
                  <span className="inline-flex items-center gap-1 text-[11px] font-extrabold uppercase px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    Recommended Route
                  </span>
                  <RiskBadge level={routeRisk.recommended_route.risk_level} size="sm" />
                </div>

                <h3 className="text-xl font-bold text-white mb-2">
                  {routeRisk.recommended_route.name}
                </h3>

                <div className="grid grid-cols-2 gap-3 mb-4 text-xs font-mono">
                  <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                    <span className="text-slate-500 block text-[10px] uppercase font-sans">Distance</span>
                    <span className="text-base font-bold text-white">{routeRisk.recommended_route.distance_km} km</span>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                    <span className="text-slate-500 block text-[10px] uppercase font-sans">Est. Duration</span>
                    <span className="text-base font-bold text-white">{routeRisk.recommended_route.travel_time_mins} mins</span>
                  </div>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed mb-4">
                  {routeRisk.recommended_route.summary_advisory}
                </p>
              </div>

              <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 text-xs">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1">
                  Active Hazard Zones Intersected:
                </span>
                <span className="text-emerald-400 font-medium">
                  {routeRisk.recommended_route.hazard_zones_crossed.join(', ')}
                </span>
              </div>
            </div>

            {/* Route B - Alternative / High Risk */}
            <div
              className={`p-6 rounded-3xl border ${
                routeRisk.alternative_route.risk_level === 'HIGH' || routeRisk.alternative_route.risk_level === 'VERY_HIGH'
                  ? 'border-red-500/40 bg-red-950/10 shadow-lg shadow-red-950/20'
                  : 'glass-card border-slate-800'
              } flex flex-col justify-between`}
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-3">
                  <span className="inline-flex items-center gap-1 text-[11px] font-extrabold uppercase px-2.5 py-0.5 rounded-full bg-red-500/20 text-red-400 border border-red-500/30">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    Alternative Cut Route
                  </span>
                  <RiskBadge level={routeRisk.alternative_route.risk_level} size="sm" />
                </div>

                <h3 className="text-xl font-bold text-white mb-2">
                  {routeRisk.alternative_route.name}
                </h3>

                <div className="grid grid-cols-2 gap-3 mb-4 text-xs font-mono">
                  <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                    <span className="text-slate-500 block text-[10px] uppercase font-sans">Distance</span>
                    <span className="text-base font-bold text-white">{routeRisk.alternative_route.distance_km} km</span>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                    <span className="text-slate-500 block text-[10px] uppercase font-sans">Est. Duration</span>
                    <span className="text-base font-bold text-white">{routeRisk.alternative_route.travel_time_mins} mins</span>
                  </div>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed mb-4">
                  {routeRisk.alternative_route.summary_advisory}
                </p>
              </div>

              <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 text-xs">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1">
                  Active Hazard Zones Intersected:
                </span>
                <span className="text-red-400 font-medium">
                  {routeRisk.alternative_route.hazard_zones_crossed.join(', ')}
                </span>
              </div>
            </div>
          </div>

          {/* Map Preview of Routes */}
          <div className="p-6 rounded-3xl glass-card border-slate-800 shadow-xl">
            <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
              <RouteIcon className="w-4 h-4 text-orange-400" />
              <span>Corridor Trajectory Comparison</span>
              <span className="text-xs font-normal text-slate-400">
                (Green: Recommended Route A • Dashed Red: Hazardous Route B)
              </span>
            </h3>
            <MapView
              center={[11.3850, 76.7450]}
              zoom={11}
              routeWaypoints={routeRisk.recommended_route.waypoints}
              alternativeWaypoints={routeRisk.alternative_route.waypoints}
              className="h-[400px] w-full"
            />
          </div>
        </div>
      ) : null}
    </div>
  );
};
